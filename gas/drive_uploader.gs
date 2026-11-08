/**
 * Google Drive Uploader for GitHub Actions / Headless Pipelines
 * 
 * 【概要】
 * GitHub Actions などの外部CI/CD環境から Google ドライブへ画像を直接アップロードする Web App です。
 * サービスアカウントの「個人アカウントにおけるストレージ容量0MB制限（storageQuotaExceeded）」を回避し、
 * オーナー（個人Googleアカウント）の容量枠を用いてファイル（アイキャッチ画像・レポート）を確実に保存します。
 * 
 * 【デプロイ手順（初回のみ・3分）】
 * 1. Google Drive または https://script.google.com/ で「新しいプロジェクト」を作成。
 * 2. 本コード（drive_uploader.gs）を貼り付けて保存。
 * 3. 画面右上の「デプロイ」>「新しいデプロイ」をクリック。
 * 4. 種類の選択: 「ウェブアプリ」
 *    - 次のユーザーとして実行: 自分（your_account@gmail.com）
 *    - アクセスできるユーザー: 全員（Anyone）
 * 5. 「デプロイ」を押し、表示された「ウェブアプリのURL」をコピー。
 * 6. GitHub リポジトリ（wp-auto-post）の Secrets に以下を登録：
 *    - GAS_UPLOAD_URL: コピーしたウェブアプリURL
 *    （必要に応じて GAS_UPLOAD_TOKEN を設定し、本スクリプトの AUTH_TOKEN と一致させてください）
 */

const DEFAULT_TARGET_FOLDER_ID = '17qo8NbDC_D6Xdbz1b6oo6OxXIIBFaezK'; // note-images folder
const AUTH_TOKEN = PropertiesService.getScriptProperties().getProperty('AUTH_TOKEN') || '';

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return responseJson({ status: 'error', message: 'Empty post data' }, 400);
    }

    const payload = JSON.parse(e.postData.contents);

    // 簡易トークン認証（AUTH_TOKENが設定されている場合のみ検査）
    if (AUTH_TOKEN && payload.token !== AUTH_TOKEN) {
      return responseJson({ status: 'error', message: 'Unauthorized' }, 401);
    }

    const folderId = payload.folderId || DEFAULT_TARGET_FOLDER_ID;
    const fileName = payload.fileName || `upload_${Date.now()}`;
    const mimeType = payload.mimeType || 'application/octet-stream';
    const base64Content = payload.base64Content;

    if (!base64Content) {
      return responseJson({ status: 'error', message: 'base64Content is required' }, 400);
    }

    const folder = DriveApp.getFolderById(folderId);
    const decodedBytes = Utilities.base64Decode(base64Content);
    const blob = Utilities.newBlob(decodedBytes, mimeType, fileName);
    
    // 既存の同名ファイルがあるかチェック（上書きまたは新規作成）
    const existingFiles = folder.getFilesByName(fileName);
    let targetFile;
    if (existingFiles.hasNext()) {
      const oldFile = existingFiles.next();
      // 同名ファイルが存在する場合はゴミ箱へ移動して新規作成
      oldFile.setTrashed(true);
    }
    targetFile = folder.createFile(blob);

    return responseJson({
      status: 'success',
      fileId: targetFile.getId(),
      fileName: targetFile.getName(),
      fileUrl: targetFile.getUrl(),
      size: targetFile.getSize()
    });

  } catch (err) {
    return responseJson({
      status: 'error',
      message: err.toString(),
      stack: err.stack
    }, 500);
  }
}

function doGet(e) {
  return responseJson({
    status: 'ok',
    message: 'Google Drive Uploader WebApp is running healthy.'
  });
}

function responseJson(data, statusCode) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
