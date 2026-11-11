/**
 * ==============================================================================
 * 🚀 高度GASオープンデータ連携＆統計モデリング スイート (v2.0)
 * 【対象】経済産業省 gBizINFO API v2 × 広島県（34）企業オープンデータ
 * 【特徴】
 *   1. デイジーチェーン自動再開トリガー（6分制限を永久突破）
 *   2. 一括二次元配列書き込み（range.setValues: I/Oフリーズ完全根絶）
 *   3. ヘッドレス スプレッドシート REST API（doGet: 0円サーバーレスAPI化）
 *   4. シート内 統計モデリング カスタム関数群（対数弾力性・ロジスティック確率・ジニ係数）
 * ==============================================================================
 */

var CONFIG = {
  API_BASE: 'https://api.info.gbiz.go.jp/hojin/v2/hojin',
  API_TOKEN: 'RuAOt26DNiaFTxPlJiZ78Kvxz0Zn6y4B', // gBizINFO公式トークン
  PREFECTURE: '34', // 広島県 JISコード
  MAX_EXECUTION_MS: 4.5 * 60 * 1000, // 4分30秒で安全退避
  CORP_TYPES: ['301', '302', '305', '401'] // 株式会社, 有限会社, 合同会社, その他法人
};

/**
 * 1. 【デイジーチェーン・クローラー】
 * 広島県内の全法人をページネーション取得し、制限時間前に安全中断＆自己トリガー生成で永続自動取得
 */
function runDaisyChainHarvest() {
  var startTime = new Date().getTime();
  var props = PropertiesService.getScriptProperties();
  var sheet = getOrCreateDataSheet();
  
  // 保存されたステートの復元
  var currentTypeIdx = parseInt(props.getProperty('CURRENT_TYPE_IDX') || '0', 10);
  var currentPage = parseInt(props.getProperty('CURRENT_PAGE') || '1', 10);
  var totalFetched = parseInt(props.getProperty('TOTAL_FETCHED') || '0', 10);
  
  Logger.log('▶ クローラー再開: 法人種別インデックス=' + currentTypeIdx + ', ページ=' + currentPage);
  
  while (currentTypeIdx < CONFIG.CORP_TYPES.length) {
    var cType = CONFIG.CORP_TYPES[currentTypeIdx];
    
    while (currentPage <= 10) {
      // 実行時間監視（4分30秒を超えたら自己トリガーを発行して脱出）
      if (new Date().getTime() - startTime > CONFIG.MAX_EXECUTION_MS) {
        props.setProperty('CURRENT_TYPE_IDX', currentTypeIdx.toString());
        props.setProperty('CURRENT_PAGE', currentPage.toString());
        props.setProperty('TOTAL_FETCHED', totalFetched.toString());
        
        spawnNextTrigger();
        Logger.log('⏱️ 実行時間上限（4分30秒）到達。次回トリガーを発行して安全中断しました。');
        return;
      }
      
      var url = CONFIG.API_BASE + '?prefecture=' + CONFIG.PREFECTURE +
                '&corporate_type=' + cType +
                '&page=' + currentPage +
                '&limit=100';
                
      var options = {
        method: 'get',
        headers: {
          'Accept': 'application/json',
          'X-hojinInfo-api-token': CONFIG.API_TOKEN
        },
        muteHttpExceptions: true
      };
      
      var response = UrlFetchApp.fetch(url, options);
      if (response.getResponseCode() === 200) {
        var data = JSON.parse(response.getContentText());
        var infos = data['hojin-infos'] || [];
        
        if (infos.length === 0) {
          break; // この種別の最終ページ
        }
        
        // 高速一括二次元配列作成
        var rows = [];
        for (var i = 0; i < infos.length; i++) {
          var item = infos[i];
          rows.push([
            item.corporate_number || '',
            item.name || '',
            cType,
            item.location || '',
            extractCityFromLocation(item.location || ''),
            item.status || '存続',
            item.update_date || '',
            new Date()
          ]);
        }
        
        // appendRow を使わず、末尾に setValues で一括書き込み（I/O高速化）
        if (rows.length > 0) {
          var lastRow = sheet.getLastRow();
          sheet.getRange(lastRow + 1, 1, rows.length, rows[0].length).setValues(rows);
          totalFetched += rows.length;
        }
        
        Logger.log('  [OK] 種別 ' + cType + ' ページ ' + currentPage + ' (' + infos.length + '件取得)');
        currentPage++;
        Utilities.sleep(400); // 礼儀正しいAPI呼び出し間隔
      } else if (response.getResponseCode() === 429) {
        Logger.log('⚠️ レート制限検知。10秒待機...');
        Utilities.sleep(10000);
      } else {
        Logger.log('⚠️ HTTPエラー: ' + response.getResponseCode());
        break;
      }
    }
    
    // 次の法人種別へ
    currentTypeIdx++;
    currentPage = 1;
  }
  
  // 全件完了時のクリーンアップ
  props.deleteProperty('CURRENT_TYPE_IDX');
  props.deleteProperty('CURRENT_PAGE');
  props.deleteProperty('TOTAL_FETCHED');
  cleanUpTriggers();
  Logger.log('🎉 広島県オープンデータ 全件巡回完了！ 合計取得件数: ' + totalFetched);
}

/**
 * 60秒後に自己を呼び出す時間主導型トリガーを発行
 */
function spawnNextTrigger() {
  cleanUpTriggers();
  ScriptApp.newTrigger('runDaisyChainHarvest')
    .timeBased()
    .after(60000)
    .create();
}

/**
 * 既存の同名トリガーをすべて削除
 */
function cleanUpTriggers() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'runDaisyChainHarvest') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
}

/**
 * データ格納用シートの取得または初期化
 */
function getOrCreateDataSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('広島県法人データ');
  if (!sheet) {
    sheet = ss.insertSheet('広島県法人データ');
    sheet.getRange(1, 1, 1, 8).setValues([[
      '法人番号', '法人名', '法人種別', '本店所在地', '市町名', 'ステータス', '更新日時', '取得タイムスタンプ'
    ]]);
    sheet.getRange('1:1').setFontWeight('bold').setBackground('#f0f4f8');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

/**
 * 住所から自治体名を正規表現でパース
 */
function extractCityFromLocation(loc) {
  var m = loc.match(/広島県(広島市[^\d]+?区|呉市|竹原市|三原市|尾道市|福山市|府中市|三次市|庄原市|大竹市|東広島市|廿日市市|安芸高田市|江田島市|安芸郡[^\d]+?町|山県郡[^\d]+?町|豊田郡[^\d]+?町|世羅郡[^\d]+?町|神石郡[^\d]+?町)/);
  return m ? m[1] : (loc.indexOf('広島市') !== -1 ? '広島市（区不明）' : '広島県内他');
}

/**
 * ==============================================================================
 * 2. 【ヘッドレス REST API (Web App)】
 * Googleスプレッドシートを外部（Webフロントエンド等）から叩けるJSON API化
 * ==============================================================================
 */
function doGet(e) {
  var sheet = getOrCreateDataSheet();
  var lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'empty', data: [] }))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  var cityFilter = (e && e.parameter && e.parameter.city) ? e.parameter.city : null;
  var limit = (e && e.parameter && e.parameter.limit) ? parseInt(e.parameter.limit, 10) : 100;
  
  var values = sheet.getRange(2, 1, Math.min(lastRow - 1, 1000), 7).getValues();
  var result = [];
  
  for (var i = 0; i < values.length; i++) {
    var row = values[i];
    var city = row[4];
    if (!cityFilter || city === cityFilter) {
      result.push({
        corporate_number: row[0],
        name: row[1],
        corporate_type: row[2],
        location: row[3],
        city: city,
        status: row[5],
        update_date: row[6]
      });
      if (result.length >= limit) break;
    }
  }
  
  return ContentService.createTextOutput(JSON.stringify({
    status: 'success',
    total_returned: result.length,
    data: result
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * ==============================================================================
 * 3. 【シート内 統計モデリング カスタム関数群】
 * スプレッドシートの数式バーから直接呼び出せる計量経済・統計関数
 * ==============================================================================
 */

/**
 * 対数弾力性（Log-Log Elasticity: 単回帰スロープ beta）を算出
 * 数式: =GBIZ_ELASTICITY(Xのセル範囲, Yのセル範囲)
 * @customfunction
 */
function GBIZ_ELASTICITY(xRange, yRange) {
  var logX = [];
  var logY = [];
  
  for (var i = 0; i < xRange.length; i++) {
    var x = parseFloat(xRange[i][0]);
    var y = parseFloat(yRange[i][0]);
    if (!isNaN(x) && !isNaN(y) && x > 0 && y > 0) {
      logX.append ? logX.push(Math.log(x)) : logX.push(Math.log(x));
      logY.push(Math.log(y));
    }
  }
  
  var n = logX.length;
  if (n < 2) return 'サンプル不足';
  
  var meanX = logX.reduce(function(a, b){ return a + b; }, 0) / n;
  var meanY = logY.reduce(function(a, b){ return a + b; }, 0) / n;
  
  var cov = 0, varX = 0;
  for (var j = 0; j < n; j++) {
    cov += (logX[j] - meanX) * (logY[j] - meanY);
    varX += Math.pow(logX[j] - meanX, 2);
  }
  
  return varX === 0 ? 0 : cov / varX;
}

/**
 * ロジスティック回帰の採択確率（シグモイド関数）を算出
 * 数式: =GBIZ_LOGISTIC_PROB(説明変数X, 切片beta0, 傾きbeta1)
 * @customfunction
 */
function GBIZ_LOGISTIC_PROB(x, beta0, beta1) {
  var z = beta0 + beta1 * x;
  return 1 / (1 + Math.exp(-z));
}

/**
 * ジニ係数（格差指数: 0〜1）を算出
 * 数式: =GBIZ_GINI(数値セル範囲)
 * @customfunction
 */
function GBIZ_GINI(range) {
  var values = [];
  for (var i = 0; i < range.length; i++) {
    for (var j = 0; j < range[i].length; j++) {
      var v = parseFloat(range[i][j]);
      if (!isNaN(v) && v >= 0) values.push(v);
    }
  }
  if (values.length < 2) return 0;
  values.sort(function(a, b) { return a - b; });
  
  var n = values.length;
  var sum = 0;
  for (var k = 0; k < n; k++) {
    sum += (2 * (k + 1) - n - 1) * values[k];
  }
  var totalSum = values.reduce(function(a, b){ return a + b; }, 0);
  return totalSum === 0 ? 0 : sum / (n * totalSum);
}
