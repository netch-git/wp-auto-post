import json
import base64
from pathlib import Path

reports_dir = Path('/home/antigravity/netch-git/wp-auto-post/reports/daily')
brain_dir = Path('/home/antigravity/.gemini/jetski/brain/v1/default/jetski_remote_agents_3p/dc026dd2-9b4e-4139-9ba8-efe4b4c29953')

articles = {}
for dt in ['2026-11-11', '2026-11-10']:
    articles[dt] = {}
    for p, name, img_name in [
        ('part_a', 'Part A: デジタルスキル・マネタイズ', f'{dt}#本日のデジタル資産・スキルのマネタイズ.png'),
        ('part_b', 'Part B: 海外の高度GAS事例', f'{dt}#本日の高度GAS.png'),
        ('part_c', 'Part C: 生成AI・Antigravity動向', f'{dt}#本日の生成AIニュース.png')
    ]:
        md_file = reports_dir / f'{dt}-{p}.md'
        img_file = reports_dir / img_name
        content = md_file.read_text(encoding='utf-8') if md_file.exists() else ''
        
        img_data_url = ''
        if img_file.exists():
            b64 = base64.b64encode(img_file.read_bytes()).decode('utf-8')
            img_data_url = f'data:image/png;base64,{b64}'

        articles[dt][p] = {
            'title': name,
            'filename': md_file.name,
            'content': content,
            'image_name': img_name,
            'image_url': img_data_url,
            'char_count': len(content)
        }

html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>note 投稿・ワンクリックコピーツール</title>
  <style>
    :root {
      --primary: #10b981;
      --primary-hover: #059669;
      --bg: #0f172a;
      --surface: #1e293b;
      --surface-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --code-bg: #090d16;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Hiragino Sans', 'Noto Sans JP', sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 24px;
    }
    .container { max-width: 1100px; margin: 0 auto; }
    header { margin-bottom: 24px; }
    h1 { font-size: 1.6rem; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px; }
    .subtitle { color: var(--text-muted); font-size: 0.9rem; margin-top: 4px; }

    .nav-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
      background: var(--surface);
      padding: 12px 16px;
      border-radius: 12px;
      border: 1px solid var(--surface-border);
    }
    .pill-group { display: flex; gap: 8px; }
    .pill-btn {
      background: #334155;
      color: var(--text);
      border: none;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    .pill-btn:hover { background: #475569; }
    .pill-btn.active {
      background: #0284c7;
      color: #fff;
      font-weight: 600;
    }
    .pill-btn.part-btn.active {
      background: var(--primary);
    }

    .action-panel {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
      align-items: center;
      background: linear-gradient(135deg, #1e293b, #0f172a);
      border: 1px solid #38bdf8;
      padding: 16px 20px;
      border-radius: 12px;
      margin-bottom: 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .action-info h2 { font-size: 1.15rem; color: #fff; }
    .meta-tags { display: flex; gap: 10px; margin-top: 6px; font-size: 0.85rem; color: var(--text-muted); }
    .meta-tag { background: #334155; padding: 2px 8px; border-radius: 4px; color: #cbd5e1; }

    .btn-copy {
      background: var(--primary);
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 10px;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .btn-copy:hover {
      background: var(--primary-hover);
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(16, 185, 129, 0.5);
    }
    .btn-copy:active { transform: translateY(0); }

    .main-grid {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 24px;
    }
    @media (max-width: 860px) {
      .main-grid { grid-template-columns: 1fr; }
    }

    .sidebar-card {
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .eyecatch-box {
      width: 100%;
      aspect-ratio: 1;
      border-radius: 8px;
      overflow: hidden;
      background: #000;
      border: 1px solid var(--surface-border);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .eyecatch-box img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .btn-download {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      background: #3b82f6;
      color: white;
      text-decoration: none;
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      transition: background 0.2s;
      text-align: center;
    }
    .btn-download:hover { background: #2563eb; }

    .tip-box {
      background: rgba(56, 189, 248, 0.08);
      border-left: 4px solid #38bdf8;
      padding: 12px;
      border-radius: 4px;
      font-size: 0.85rem;
      color: #cbd5e1;
    }
    .tip-box strong { color: #38bdf8; }

    .editor-card {
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .editor-header {
      background: #172033;
      padding: 10px 16px;
      border-bottom: 1px solid var(--surface-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    textarea.markdown-area {
      width: 100%;
      height: 600px;
      background: var(--code-bg);
      color: #e2e8f0;
      font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
      font-size: 0.92rem;
      line-height: 1.6;
      border: none;
      padding: 16px;
      resize: vertical;
      outline: none;
      white-space: pre-wrap;
    }

    .toast {
      position: fixed;
      bottom: 30px;
      right: 30px;
      background: #10b981;
      color: white;
      padding: 14px 24px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 0.95rem;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      gap: 10px;
      transform: translateY(100px);
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 9999;
    }
    .toast.show {
      transform: translateY(0);
      opacity: 1;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>📑 note投稿用 完全コピーツール</h1>
      <p class="subtitle">画面右側のプレビュー機能でのコードブロック欠損を防止し、純粋なMarkdownテキストを1クリックで完全コピーします。</p>
    </header>

    <div class="nav-bar">
      <div class="pill-group" id="date-group">
        <button class="pill-btn active" onclick="selectDate('2026-11-11')">📅 本日 (2026-11-11)</button>
        <button class="pill-btn" onclick="selectDate('2026-11-10')">📅 昨日 (2026-11-10)</button>
      </div>

      <div class="pill-group" id="part-group">
        <button class="pill-btn part-btn active" onclick="selectPart('part_a')">Part A (マネタイズ)</button>
        <button class="pill-btn part-btn" onclick="selectPart('part_b')">Part B (高度GAS)</button>
        <button class="pill-btn part-btn" onclick="selectPart('part_c')">Part C (生成AI)</button>
      </div>
    </div>

    <div class="action-panel">
      <div class="action-info">
        <h2 id="article-title">記事タイトル</h2>
        <div class="meta-tags">
          <span class="meta-tag" id="meta-filename">filename.md</span>
          <span class="meta-tag" id="meta-chars">0 文字</span>
          <span class="meta-tag" style="background:#065f46; color:#a7f3d0;">✓ コードブロック・数式 100%保持</span>
        </div>
      </div>
      <div>
        <button class="btn-copy" onclick="copyCurrentContent()">
          <span>📋 本文を完全コピー</span>
        </button>
      </div>
    </div>

    <div class="main-grid">
      <div class="sidebar-card">
        <div>
          <h3 style="font-size:0.95rem; margin-bottom:10px; color:#93c5fd;">🖼️ アイキャッチ画像</h3>
          <div class="eyecatch-box">
            <img id="eyecatch-img" src="" alt="Eyecatch">
          </div>
        </div>
        <a id="btn-download-img" class="btn-download" href="#" download="eyecatch.png">
          💾 画像をダウンロード (高解像度 PNG)
        </a>

        <div class="tip-box">
          <strong>💡 note 貼り付けのヒント</strong><br>
          1. 「本文を完全コピー」ボタンを押します。<br>
          2. note の記事作成画面を開き、そのまま <code>Ctrl + V</code>（Macは <code>Cmd + V</code>）で貼り付けます。<br>
          3. コードブロックや段落が欠落することなく、完全に反映されます。
        </div>
      </div>

      <div class="editor-card">
        <div class="editor-header">
          <span>📝 Raw Markdown（直接選択・全コピーも可能）</span>
          <button style="background:none; border:none; color:#38bdf8; cursor:pointer; font-size:0.85rem;" onclick="selectAllText()">すべて選択</button>
        </div>
        <textarea id="content-area" class="markdown-area" readonly></textarea>
      </div>
    </div>
  </div>

  <div id="toast" class="toast">
    <span>✅ クリップボードに完全コピーしました！そのまま note に貼り付けられます。</span>
  </div>

  <script>
    const DATA = """ + json.dumps(articles, ensure_ascii=False) + """;

    let currentDate = '2026-11-11';
    let currentPart = 'part_a';

    function selectDate(date) {
      currentDate = date;
      document.querySelectorAll('#date-group .pill-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(date));
      });
      render();
    }

    function selectPart(part) {
      currentPart = part;
      const partNames = { 'part_a': 'Part A', 'part_b': 'Part B', 'part_c': 'Part C' };
      document.querySelectorAll('#part-group .pill-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(partNames[part]));
      });
      render();
    }

    function render() {
      const art = DATA[currentDate] && DATA[currentDate][currentPart];
      if (!art) return;

      document.getElementById('article-title').textContent = `${currentDate} : ${art.title}`;
      document.getElementById('meta-filename').textContent = art.filename;
      document.getElementById('meta-chars').textContent = `${art.char_count.toLocaleString()} 文字`;
      
      const area = document.getElementById('content-area');
      area.value = art.content;

      const img = document.getElementById('eyecatch-img');
      const dlBtn = document.getElementById('btn-download-img');
      if (art.image_url) {
        img.src = art.image_url;
        dlBtn.href = art.image_url;
        dlBtn.download = art.image_name;
        dlBtn.style.display = 'inline-flex';
      } else {
        img.src = '';
        dlBtn.style.display = 'none';
      }
    }

    function copyCurrentContent() {
      const art = DATA[currentDate] && DATA[currentDate][currentPart];
      if (!art) return;

      navigator.clipboard.writeText(art.content).then(() => {
        showToast();
      }).catch(err => {
        const area = document.getElementById('content-area');
        area.select();
        document.execCommand('copy');
        showToast();
      });
    }

    function selectAllText() {
      const area = document.getElementById('content-area');
      area.focus();
      area.select();
    }

    function showToast() {
      const toast = document.getElementById('toast');
      toast.classList.add('show');
      setTimeout(() => {
        toast.classList.remove('show');
      }, 2500);
    }

    // Initial render
    render();
  </script>
</body>
</html>
"""

target_file = brain_dir / 'note_copy_assistant.html'
target_file.write_text(html_content, encoding='utf-8')
print('Successfully wrote HTML:', target_file, 'Size:', target_file.stat().st_size)
