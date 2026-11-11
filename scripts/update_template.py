with open('scripts/template.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace filterRecords in script
old_filter = '''    function filterRecords() {
      const q = filterInput.value.trim().toLowerCase();
      const t = typeFilter.value;

      filteredData = ALL_CORPS.filter(r => {
        const matchText = !q || r.n.includes(q) || r.m.toLowerCase().includes(q) || r.c.toLowerCase().includes(q) || r.l.toLowerCase().includes(q) || r.b.toLowerCase().includes(q);
        const matchType = !t || r.t === t;
        return matchText && matchType;
      });

      currentPage = 1;
      renderTable();
    }'''

new_filter = '''    function escapeHtml(str) {
      return str.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[m]);
    }

    function filterRecords() {
      const rawQuery = filterInput.value.trim().normalize('NFKC').toLowerCase();
      const t = typeFilter.value;
      const tokens = rawQuery.split(/[\\s\\u3000]+/).filter(tok => tok.length > 0);

      filteredData = ALL_CORPS.filter(r => {
        if (t && r.t !== t) return false;
        if (tokens.length === 0) return true;
        const searchable = `${r.n} ${r.m} ${r.t} ${r.c} ${r.l} ${r.b}`.normalize('NFKC').toLowerCase();
        return tokens.every(tok => searchable.includes(tok));
      });

      currentPage = 1;
      renderTable();
    }'''

assert old_filter in content, 'old_filter not found'
content = content.replace(old_filter, new_filter)

# Replace table render empty state
old_empty = 'pageInfo.innerText = total > 0 ? `表示中: ${startIdx + 1} - ${endIdx} 件 / 該当 ${total.toLocaleString()} 件` : \'該当する法人が見つかりませんでした\';'
new_empty = '''pageInfo.innerText = total > 0 ? `表示中: ${startIdx + 1} - ${endIdx} 件 / 該当 ${total.toLocaleString()} 件` : '該当する法人が見つかりませんでした';
      if (total === 0) {
        const q = filterInput.value.trim();
        tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-slate-500"><div class="max-w-md mx-auto space-y-3"><div class="text-sm font-bold text-slate-800">「${escapeHtml(q)}」は実測台帳（${ALL_CORPS.length.toLocaleString()}社）に見つかりませんでした</div><p class="text-xs text-slate-500 leading-relaxed">本白書はgBizINFO API v2から計量分析用に抽出した県内主要法人${ALL_CORPS.length.toLocaleString()}社を収録しています。<br>国税庁登録の県内全8万社は経済産業省公式ポータルで直接検索できます。</p><a href="https://info.gbiz.go.jp/hojin/search?keyword=${encodeURIComponent(q)}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-700 text-white rounded text-xs font-medium hover:bg-blue-800 transition shadow-sm"><span>↗</span> gBizINFO公式ポータルで「${escapeHtml(q)}」を直接検索する</a></div></td></tr>`;
        renderPagination(1);
        return;
      }'''

assert old_empty in content, 'old_empty not found'
content = content.replace(old_empty, new_empty)

content = content.replace('placeholder="会社名・自治体名・住所・特許・補助金で検索..."', 'placeholder="社名・自治体・住所・特許（例：マツダ、中国電力、エディオン、福山、特許）..."')

with open('scripts/template.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Successfully updated scripts/template.html')
