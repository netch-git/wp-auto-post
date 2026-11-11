/**
 * ====================================================================
 * gBizINFO API v2 大規模オープンデータ自動取得エンジン (TriggerApp Daisy-Chain)
 * ====================================================================
 * 
 * 【解決する課題】
 * 1. 6分実行制限 (Exceeded maximum execution time) の完全突破
 * 2. appendRow の乱用による I/O ボトルネック解消 (setValues 一括書き込み)
 * 3. ネットワーク瞬断・エラー時の自動リトライと中断位置からの確実な再開
 * 4. 全件処理完了時の自己トリガー自動破棄 (ゴミトリガー放置防止)
 */

const GBIZ_CONFIG = {
  API_BASE_URL: 'https://api.info.gbiz.go.jp/hojin/v2/hojin',
  TOKEN_PROPERTY_KEY: 'GBIZ_API_TOKEN', // PropertiesService または直接記入
  DEFAULT_TOKEN: 'RuAOt26DNiaFTxPlJiZ78Kvxz0Zn6y4B', // ユーザーのAPIトークン
  TARGET_SHEET_NAME: 'gBizINFO_法人台帳',
  SAFE_TIME_LIMIT_MS: 4.5 * 60 * 1000, // 4分30秒で安全に次回トリガーへバトンタッチ
  PAGE_LIMIT: 100, // 1リクエストの取得件数
  MAX_PAGE_PER_CONDITION: 10 // gBizINFO v2 API 仕様上の最大ページ数
};

/**
 * 手動実行用エントリポイント（ここからスタート）
 */
function startGbizSync() {
  const props = PropertiesService.getScriptProperties();
  
  // 初期設定：取得対象の都道府県コード（例: 34 = 広島県, 13 = 東京都）
  props.setProperties({
    'GBIZ_CURRENT_PREFECTURE': '34', // 都道府県コード (2桁)
    'GBIZ_CURRENT_PAGE': '1',
    'GBIZ_PROCESSED_TOTAL': '0',
    'GBIZ_STATUS': 'RUNNING'
  });

  // シート初期化
  initTargetSheet();

  // 既存の同名トリガーを掃除
  cleanupGbizTriggers();

  // 初回実行
  runGbizSyncBatch();
}

/**
 * 再帰的デイジーチェーン実行本体
 */
function runGbizSyncBatch() {
  const startTime = Date.now();
  const props = PropertiesService.getScriptProperties();
  
  const token = props.getProperty(GBIZ_CONFIG.TOKEN_PROPERTY_KEY) || GBIZ_CONFIG.DEFAULT_TOKEN;
  let prefCode = props.getProperty('GBIZ_CURRENT_PREFECTURE') || '34';
  let currentPage = parseInt(props.getProperty('GBIZ_CURRENT_PAGE') || '1', 10);
  let processedTotal = parseInt(props.getProperty('GBIZ_PROCESSED_TOTAL') || '0', 10);

  const sheet = initTargetSheet();
  const collectedRows = [];

  console.log(`[gBizINFO] バッチ開始: 都道府県=${prefCode}, ページ=${currentPage}, 累積件数=${processedTotal}`);

  while (true) {
    // 1. 実行時間チェック（4分30秒を超えたら次回へ引き継ぎ）
    const elapsed = Date.now() - startTime;
    if (elapsed > GBIZ_CONFIG.SAFE_TIME_LIMIT_MS) {
      console.warn(`[gBizINFO] 制限時間接近 (${Math.round(elapsed / 1000)}秒経過)。中断して次回トリガーを予約します。`);
      break;
    }

    // 2. APIフェッチ
    const url = `${GBIZ_CONFIG.API_BASE_URL}?prefecture=${prefCode}&page=${currentPage}&limit=${GBIZ_CONFIG.PAGE_LIMIT}`;
    const options = {
      method: 'get',
      headers: {
        'Accept': 'application/json',
        'X-hojinInfo-api-token': token
      },
      muteHttpExceptions: true
    };

    let response;
    try {
      response = UrlFetchApp.fetch(url, options);
    } catch (e) {
      console.error(`[gBizINFO] Fetch例外: ${e.message}。10秒待機後リトライします。`);
      Utilities.sleep(10000);
      continue;
    }

    const statusCode = response.getResponseCode();
    if (statusCode === 429) {
      console.warn(`[gBizINFO] レート制限 (429) 検知。20秒待機します。`);
      Utilities.sleep(20000);
      continue;
    }

    if (statusCode !== 200) {
      console.error(`[gBizINFO] APIエラー HTTP ${statusCode}: ${response.getContentText()}`);
      break;
    }

    const json = JSON.parse(response.getContentText());
    const hojinList = json['hojin-infos'] || [];

    if (hojinList.length === 0) {
      console.log(`[gBizINFO] 該当条件でのデータ終了（0件返却）。`);
      // 全件終了フラグ
      props.setProperty('GBIZ_STATUS', 'COMPLETED');
      break;
    }

    // 3. データ整形（インメモリ配列に格納）
    for (const h of hojinList) {
      collectedRows.push([
        h.corporate_number || '',
        h.name || '',
        h.name_en || '',
        h.postal_code || '',
        h.location || '',
        h.status || '',
        h.number_of_activity || '0',
        h.update_date || '',
        new Date() // 取得タイムスタンプ
      ]);
    }

    processedTotal += hojinList.length;
    currentPage++;

    // gBizINFO v2 API の最大ページ制限 (page=10) を超えた場合のハンドリング
    if (currentPage > GBIZ_CONFIG.MAX_PAGE_PER_CONDITION) {
      console.log(`[gBizINFO] 都道府県 ${prefCode} の最大ページ (10) に到達しました。`);
      props.setProperty('GBIZ_STATUS', 'COMPLETED');
      break;
    }

    // API負荷軽減のための微小ウェイト (300ms)
    Utilities.sleep(300);
  }

  // 4. スプレッドシートへ一括バルク書き込み（appendRowを使わずsetValuesで爆速書き込み）
  if (collectedRows.length > 0) {
    const lastRow = sheet.getLastRow();
    sheet.getRange(lastRow + 1, 1, collectedRows.length, collectedRows[0].length)
         .setValues(collectedRows);
    console.log(`[gBizINFO] スプレッドシートへ ${collectedRows.length} 件を一括書き込み完了。`);
  }

  // 5. 次回状態の保存
  props.setProperties({
    'GBIZ_CURRENT_PAGE': currentPage.toString(),
    'GBIZ_PROCESSED_TOTAL': processedTotal.toString()
  });

  // 6. デイジーチェーントリガーの判定
  const status = props.getProperty('GBIZ_STATUS');
  if (status === 'COMPLETED') {
    console.log(`🎉 [gBizINFO] すべてのデータ取得が正常完了しました！ 合計: ${processedTotal} 件`);
    cleanupGbizTriggers();
    props.deleteProperty('GBIZ_STATUS');
  } else {
    // まだ続きがある場合：1分後の再帰トリガーを登録して終了
    scheduleNextTrigger();
  }
}

/**
 * 1分後の次回トリガーを自動生成
 */
function scheduleNextTrigger() {
  cleanupGbizTriggers();
  ScriptApp.newTrigger('runGbizSyncBatch')
    .timeBased()
    .after(60 * 1000) // 1分後
    .create();
  console.log('⏰ [gBizINFO] 次回バッチの自動トリガー（1分後）を正常に予約しました。');
}

/**
 * 既存トリガーのクリーンアップ（20個上限防止）
 */
function cleanupGbizTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  for (const t of triggers) {
    if (t.getHandlerFunction() === 'runGbizSyncBatch') {
      ScriptApp.deleteTrigger(t);
    }
  }
}

/**
 * 台帳シートの作成とヘッダー初期化
 */
function initTargetSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(GBIZ_CONFIG.TARGET_SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(GBIZ_CONFIG.TARGET_SHEET_NAME);
    const headers = [
      '法人番号', '法人名', '英語名', '郵便番号', '本社所在地', 
      'ステータス', '行政活動情報件数', '更新日', 'データ取得日時'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold').setBackground('#e8f0fe');
    sheet.setFrozenRows(1);
  }
  return sheet;
}
