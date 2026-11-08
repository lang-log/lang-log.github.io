// Interface text in languages other than English, used by lang.js. The pages are written
// in English; each entry maps the English text of one text node (spaces collapsed) to its
// translation.
// - exact: whole strings.
// - patterns: [regular expression, replacement] for text with numbers or names in it. The
//   replacement may be a function (match, tr) where tr translates a part.
// - Text that is neither is split into sentences, and translated when every sentence is.
// Record names, source titles, citations, codes and licence names stay as they are.
// Add a string here when you add interface text to a page or a script.
window.LANGLOG_I18N = {
  ja: {
    join: '',
    exact: {
      // Stats, Sources and Updates pages and the guide row of the top page (tools/build_home.py)
      'Spoken languages by macroarea': '大地域ごとの音声言語',
      'All figures': 'すべての数',
      'Africa': 'アフリカ',
      'Papunesia': 'パプネシア',
      'Eurasia': 'ユーラシア',
      'North America': '北アメリカ',
      'South America': '南アメリカ',
      'Australia': 'オーストラリア',
      'Oceania': 'オセアニア',
      'No location in the data': 'データに位置がないもの',
      'Stats': '統計',
      'Updates': '更新情報',
      'About Lang Log': 'Lang Log について',
      'All records': 'すべての記録',
      'By modality': 'モダリティ別',
      'Other kinds of languages': 'そのほかの言語',
      'Families': '語族',
      'Languoids': 'Languoids',
      'Records from study trees only': '研究の系統樹だけにある記録',
      'Spoken languages': '音声言語',
      'Spoken dialects': '音声言語の方言',
      'Sign-language dialects': '手話の方言',
      'Manual alphabets': '指文字',
      'Constructed languages': '人工言語',
      'Pidgins': 'ピジン',
      'Mixed languages': '混合言語',
      'Top-level families': 'トップレベルの語族',
      'Families and subgroups': '語族と下位グループ',
      'Study trees': '研究の系統樹',
      'Source-tagged placements': '出典つきの位置づけ',
      'Conflicting clade pairs between studies': '研究どうしで食い違う分岐の組',
      'New pages: Stats, Sources and Updates, linked from the top page.':
        '新しいページ: 統計、出典、更新情報。トップページからたどれます。',
      'Lang Log is now available in 21 languages.':
        'Lang Log を 21 の言語で使えるようになりました。',
      'Maps can fill the whole window in a map view, and tapping a point shows its records with links to their pages.':
        '地図を画面いっぱいのマップビューで見られるようになり、点をタップするとその記録が出て、各ページへのリンクからたどれます。',
      'Maps on record pages can be zoomed and panned, with country borders.':
        '記録のページの地図を拡大・移動できるようになり、国境も表示します。',
      'Every family, language and dialect has its own page, at an address that follows its classification.':
        'すべての語族、言語、方言に、分類に沿ったアドレスの専用ページができました。',
      'Stats · Lang Log by yoshi': '統計 · Lang Log by yoshi',
      'Updates · Lang Log by yoshi': '更新情報 · Lang Log by yoshi',
      // Releases page (tools/build_releases.py) and its link in the guide row
      'Releases': 'リリース',
      'Releases · Lang Log by yoshi': 'リリース · Lang Log by yoshi',
      'Latest': '最新',
      'Pre-release': 'プレリリース',
      'No releases yet.': 'リリースはまだありません。',
      'No release notes.': 'リリースノートはありません。',
      'Downloads': 'ダウンロード',
      'View on GitHub': 'GitHub で見る',
      'All releases on GitHub': 'GitHub ですべてのリリースを見る',
      'Date unknown': '日付不明',
      'Sources & scope · Lang Log by yoshi': '出典と範囲 · Lang Log by yoshi',
      // Record pages and top page after the atlas merge (tools/build_paths.py, tools/build_home.py, dist/tree.js)
      'Top': 'トップ',
      'Classification by source': '出典ごとの分類',
      'Placement:': '位置づけ:',
      'Other direct members:': 'ほかの直接の下位:',
      'Search results': '検索結果',
      'No matching records.': '一致する記録はありません。',
      'Loading records…': '記録を読み込んでいます…',
      '1 matching record': '1 件が一致',
      'Clear search': '検索をやめる',
      'Cross-family / outgroup source trees': '語族をまたぐ / 外群の系統樹',
      'Study trees and WALS families that span more than one Glottolog family. They are listed here for navigation only.':
        'Glottolog の複数の語族にまたがる研究の系統樹と WALS の語族です。案内のためだけに載せています。',
      'Whole tree': '全体の樹形図',
      'Show the tree of this branch': 'この枝の樹形図を表示',
      'Where Lang Log attaches this tree': 'Lang Log でこの系統樹をつないでいる場所',
      "Other sources' trees below this record": 'この記録の下にあるほかの出典の系統樹',
      'Drag to pan · Scroll / pinch to zoom · Click a node to open its page':
        'ドラッグで移動 · スクロールかピンチで拡大縮小 · 点をクリックでそのページへ',
      "Open a row to see its members. Each name opens its own page, with every source's placement and paper links.":
        '行を開くと下位の記録が見えます。名前を押すと、その記録のページ(出典ごとの位置づけと論文へのリンク付き)が開きます。',
      'Independent families and isolates are parallel roots. Dashed: navigation attachment, not ancestry. Distances are not time.':
        '独立した語族と孤立言語は、並んだ根として表示します。破線は案内のためのつなぎで、祖先関係ではありません。距離は時間を表しません。',
      '→ sampled study tree': '→ 標本をとった研究の系統樹',
      '→ catalog grouping': '→ カタログのグループ',
      'sampled study tree': '標本をとった研究の系統樹',
      'catalog grouping': 'カタログのグループ',
      'catalog': 'カタログ',
      'study tree': '研究の系統樹',
      'This record is not in the tree data.': 'この記録は樹形図のデータにありません。',
      'WALS families in Lang Log': 'Lang Log の WALS の語族',
      'No members recorded here.': 'ここに記録された下位はありません。',
      'Sign Language': '手話',
      'Unclassifiable': '分類できない言語',
      'Pidgin': 'ピジン',
      'Mixed Language': '混合言語',
      'Unattested': '記録が確かめられない言語',
      'Artificial Language': '人工言語',
      'Speech Register': '特別な話し方(位相)',
      'Bookkeeping': '整理用の記録',
      // Header, navigation, page titles
      'by': 'by',
      'Sources & scope': '出典と範囲',
      'Sources & scope ↗': '出典と範囲 ↗',
      'All families': 'すべての語族',
      'Atlas domains': '地図の分野',
      'Language families': '語族',
      'Sign languages': '手話',
      'Writing systems': '文字体系',
      'Dark theme': 'ダークテーマ',

      // Language feature map (dist/feature-map.html, dist/feature-map.js)
      'Language feature map': '言語の特性地図',
      'Language feature map · Lang Log by yoshi': '言語の特性地図 · Lang Log by yoshi',
      'About': '説明',
      'About this map': 'この地図について',
      'Colour by': '色分けする特性',
      'None (one colour)': 'なし(1色)',
      'Conditions': '条件',
      '+ Add condition': '+ 条件を追加',
      'Choose a feature': '特性を選ぶ',
      'Remove this condition': 'この条件を削除',
      'Select all': 'すべて選択',
      'No data': 'データなし',
      'Close': '閉じる',
      'WALS page': 'WALS のページ',
      'Lang Log record': 'Lang Log の記録',
      'World map of the languages that match the conditions': '条件に合う言語の世界地図',
      'The map data could not be loaded.': '地図のデータを読み込めませんでした。',
      'This map needs JavaScript. The feature data is in':
        'この地図には JavaScript が必要です。特性のデータは次にあります:',
      'Land and borders: Natural Earth (public domain)':
        '陸地と国境: Natural Earth(パブリックドメイン)',
      'Language feature map: every language on a world map, narrowed by conditions on WALS features and coloured by one of them.':
        '言語の特性地図: すべての言語を世界地図に出し、WALS の特性の条件で絞り込み、1つの特性で色分けします。',

      // Not-found page (dist/404.html)
      'Page not found': 'ページが見つかりません',
      'There is no page at this address. It may have moved, or the link may be mistyped.':
        'このアドレスにはページがありません。移動したか、リンクが間違っている可能性があります。',
      'Top page': 'トップページ',

      // Top page (build_home.py)
      'Search': '検索',
      'An atlas of language families, sign languages and writing systems. Every placement says which source it follows, competing classifications are shown together, and the data can be downloaded.':
        '語族、手話、文字体系の地図です。どの位置づけにも、どの出典に従ったかを示し、食い違う分類は並べて見せます。データはダウンロードできます。',
      'Also': 'ほかに',
      'All families and isolates': 'すべての語族と孤立言語',
      ': one plain page per Glottolog record, with its classification and a map.':
        ': Glottolog の記録ごとに 1 ページずつ、分類と地図を載せたシンプルなページです。',
      'Corpora and data for low-resource languages: planned.':
        '資源の少ない言語のコーパスとデータ: 準備中です。',
      'Sources: Glottolog, WALS, published study trees and script catalogs, each under its own license':
        '出典: Glottolog、WALS、公開された研究の系統樹、文字のカタログ(それぞれのライセンスに従います)',
      '© 2026 MATSUURA Yoshihiro. All rights reserved.':
        '© 2026 松浦 義広。無断での転載・利用を禁じます。',

      // Atlas: search and filters
      'FIND A BRANCH': '系統を探す',
      'Find a branch': '系統を探す',
      'Open': '開く',
      'Name, ISO code, Glottocode…': '名前、ISO コード、Glottocode…',
      'Name, alias or code…': '名前、別名、コード…',
      'Search languages and families': '言語と語族を検索',
      'Search records and aliases': '記録と別名を検索',
      'Try Japanese · 日本語 · Basque · Austronesian':
        '例: Japanese · 日本語 · Basque · Austronesian',
      'Evidence filter': '根拠で絞り込む',
      'All evidence': 'すべての根拠',
      'With research trees': '研究の系統樹があるもの',
      'With conflicting study clades': '研究どうしで分岐が食い違うもの',
      'Record category': '記録の種類',
      'All categories': 'すべての種類',
      'Spoken genealogy': '音声言語の系統',
      'Isolates': '孤立言語',

      // Atlas: toolbar
      'View': '表示',
      'List': '一覧',
      'Tree': '樹形図',
      'All roots': 'すべての根',
      'Selected branch': '選んだ系統',
      'Collapse all': 'すべて閉じる',
      'Random': 'ランダム',
      'Sign language': '手話',
      'Writing system': '文字体系',
      'Choose a random language, sign language or writing system':
        '言語・手話・文字体系からランダムに選ぶ',
      'Choose a random language or dialect': '言語か方言をランダムに選ぶ',
      'Choose a random sign language or dialect': '手話か方言をランダムに選ぶ',
      'Choose a random writing system': '文字体系をランダムに選ぶ',
      'Download': 'ダウンロード',
      'Copy link': 'リンクをコピー',
      'Zoom in': '拡大',
      'Zoom out': '縮小',
      'Fit': '全体',
      'Drag to pan · Scroll / pinch to zoom · Click a node to inspect':
        'ドラッグで移動 · スクロールかピンチで拡大縮小 · 点をクリックで詳細',
      'Dashed: navigation attachment, not ancestry. Distances are not time.':
        '破線: 案内のためのつなぎで、祖先関係ではありません。距離は時間を表しません。',
      'INTEGRATED · SOURCE-CONDITIONED': '統合 · 出典ごとの位置づけ',
      'Independent roots & alternatives': '独立した根と別の説',
      'Interactive language classification tree. Search or use the list to select a node.':
        '操作できる言語分類の樹形図です。検索か一覧で項目を選んでください。',
      'Expandable classification outline': '開閉できる分類の一覧',
      'Source-conditioned classification forest': '出典ごとの分類の森',
      'Language': '言語',
      'Dialect': '方言',
      'Expand this grouping': 'このグループを開く',
      'Expand A': 'A を開く',
      'Expand B': 'B を開く',
      'Show in tree': '樹形図で見る',
      'Catalog classification': 'カタログの分類',
      'Lexical-feature hypotheses': '語彙特徴による仮説',
      'Manual-alphabet evidence': '指文字の根拠',

      // Atlas: header numbers
      'Glottolog records': 'Glottolog の記録',
      'Manual-alphabet samples': '指文字の標本',

      // Record details
      'Record details': '記録の詳細',
      'Record information': '記録の情報',
      'Record page': '記録のページ',
      'Select a row to see its placements, names and sources.':
        '行を選ぶと、位置づけ、名前、出典が表示されます。',
      'ONE RECORD · SOURCE-CONDITIONED PLACEMENTS': '1 件の記録 · 出典ごとの位置づけ',
      'Open detail page ↗': '詳細ページを開く ↗',
      'Details ↗': '詳細 ↗',
      'Classification alternatives & evidence': '別の分類と根拠',
      'Classification alternatives & evidence ⚑': '別の分類と根拠 ⚑',
      'Classification and placements': '分類と位置づけ',
      'Conditional placements': '出典ごとの位置づけ',
      'Classification according to Glottolog 5.3': 'Glottolog 5.3 による分類',
      'Classification according to Glottolog': 'Glottolog による分類',
      'Classification according to Lang Log': 'Lang Log による分類',
      'Lang Log’s own': 'Lang Log 独自',
      'According to': '出典:',
      'According to Glottolog 5.3': 'Glottolog 5.3 による',
      'Name in this language': 'この言語での名前',
      'Names': '名前',
      'No alternate names recorded.': '別名は記録されていません。',
      'No child records imported.': '下位の記録は取り込まれていません。',
      'Isolate: no higher family': '孤立言語: 上位の語族なし',
      'Top-level: no higher family': '最上位: 上位の語族なし',
      'Independent top-level entry; no higher family asserted here.':
        '独立した最上位の項目です。ここでは上位の語族を主張していません。',
      'Independent top-level isolate; no higher family asserted here.':
        '独立した最上位の孤立言語です。ここでは上位の語族を主張していません。',
      'Alternative accounts and research notes': '別の説と研究メモ',
      'Incompatible study branches': '両立しない研究の分岐',
      'Glottolog record & bibliography ↗': 'Glottolog の記録と文献 ↗',
      'Glottolog record & references ↗': 'Glottolog の記録と参考文献 ↗',
      'Glottolog record ↗': 'Glottolog の記録 ↗',
      'Paper ↗': '論文 ↗',
      'Research data ↗': '研究データ ↗',
      'Source tree & data ↗': '元の系統樹とデータ ↗',
      'Catalog ↗': 'カタログ ↗',
      '← Variant list': '← 一覧に戻る',
      'If following': '次に従う場合:',
      'group before': 'が先にまとまる:',
      'Open in the atlas': '地図で開く',
      'Full source detail': '出典の詳細',
      'Other classifications': 'ほかの分類',
      'This record as JSON': 'この記録の JSON',

      // Hugging Face
      'Hugging Face models': 'Hugging Face のモデル',
      '🤗 Hugging Face models': '🤗 Hugging Face のモデル',
      '🤗 Models on Hugging Face ↗': '🤗 Hugging Face のモデル ↗',
      'Hugging Face model task': 'Hugging Face のモデルのタスク',
      'Model task': 'モデルのタスク',
      'All tasks': 'すべてのタスク',
      'Translation': '翻訳',
      'Text generation / LLM': 'テキスト生成 / LLM',
      'Speech recognition': '音声認識',
      'Text to speech': '音声合成',
      'Masked language modeling': 'マスク言語モデル',
      'Sentence similarity': '文の類似度',
      'Feature extraction': '特徴抽出',
      'Text classification': 'テキスト分類',
      'Token classification': 'トークン分類',
      'Question answering': '質問応答',
      'Summarization': '要約',
      'Loading public model metadata from Hugging Face…':
        'Hugging Face から公開モデルの情報を読み込んでいます…',
      'Could not reach Hugging Face. Use the links above or retry; this does not mean no models exist.':
        'Hugging Face に接続できませんでした。上のリンクを使うか、もう一度試してください。モデルがないという意味ではありません。',
      'Retry loading models': 'モデルを読み込み直す',
      'Search the name on Hugging Face ↗': 'Hugging Face で名前を検索 ↗',
      'No models found with this exact language tag.':
        'この言語タグがぴったり付いたモデルは見つかりませんでした。',

      // Downloads
      'Integrated XML ↓': '統合 XML ↓',
      'Assertions JSON ↓': '主張の JSON ↓',
      'Names / base JSON ↓': '名前 / 基本 JSON ↓',
      'OPML ↓': 'OPML ↓',
      'Provenance ↓': '来歴 ↓',
      'SVG (current view)': 'SVG(今の表示)',
      'Complete Glottolog and WALS trees, all imported names and source tags':
        'Glottolog と WALS の全系統樹、取り込んだ全名前と出典タグ',
      'Complete outline for compatible outliner tools': 'アウトライナー用の完全な一覧',
      'Attribution and license notices ↗': '帰属とライセンスの表示 ↗',

      // Sources & scope dialog
      'Close ×': '閉じる ×',
      'Scope': '範囲',
      'Sources': '出典',
      'Source register': '出典の一覧',
      'Classification and names from': '分類と名前の出典:',
      ', used under': '。ライセンス:',
      'Branches are conditional on their source. Different placements appear together; no source switch is needed.':
        '分岐は出典ごとのものです。違う位置づけが並んで表示されるので、出典を切り替える必要はありません。',
      'Independent families and isolates are parallel roots. Expand each branch to follow its recorded classification.':
        '独立した語族と孤立言語は、並んだ根として表示されます。各系統を開くと、記録された分類をたどれます。',
      'Click a row to expand and inspect. Select a language to compare its source-conditioned placements and paper-linked alternatives. Expand a study branch within the same outline.':
        '行をクリックすると開いて詳しく見られます。言語を選ぶと、出典ごとの位置づけと、論文に基づく別の説を比べられます。研究の分岐も同じ一覧の中で開けます。',
      'Top-level entries of Glottolog 5.3. Each record has its own page at a URL that follows its classification.':
        'Glottolog 5.3 の最上位の項目です。どの記録にも、分類に沿った URL の専用ページがあります。',

      ': individual source citations and licenses below. Imported summary trees are attributed to their authors and curators. Code equivalences:':
        ': 個々の出典の引用とライセンスは下にあります。取り込んだ要約系統樹は、その著者と管理者に帰属します。コードの対応:',
      'Classification ·': '分類 ·',

      // Record pages: map
      'Points: Glottolog 5.3 (CC BY 4.0).': '点: Glottolog 5.3(CC BY 4.0)。',
      'Land and borders:': '陸地と国境:',
      'Reset': '戻す',
      'Reset view': '元の表示に戻す',
      'Map view': 'マップビュー',
      'Close map view': 'マップビューを閉じる',
      'Records at this point': 'この地点の記録',
      '(public domain).': '(パブリックドメイン)。',
      'Projection: Web Mercator.': '図法: Web メルカトル図法。',

      // Levels and record kinds
      'family': '語族',
      'language': '言語',
      'dialect': '方言',
      'isolate': '孤立言語',
      'study clade': '研究の分岐',
      'navigation category': '案内用の分類',
      'research': '研究',
      'review': '総説',
      'tag unspecified': 'タグなし',
    },
    patterns: [
      [
        /^First ([\d,]+) matches\. Refine your search\.$/,
        '最初の $1 件です。検索語を絞ってください。',
      ],
      [/^Show ([\d,]+) more$/, 'さらに $1 件表示'],
      [/^(\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4})$/, '$1'],
      [/^Showing ([\d,]+) of ([\d,]+) languages$/, '$2 言語のうち $1 言語を表示'],
      [/^and ([\d,]+) more$/, 'ほか $1 件'],
      [/^([\d,]+) matching records$/, '$1 件が一致'],
      [/^Families · ([\d,]+)$/, '語族 · $1'],
      [/^If following (.+)$/, '$1 に従う場合'],
      [/^Clade in (.+)$/, '$1 での分岐'],
      [/^Source label · (.+)$/, '元の表記 · $1'],
      [/^(.+) · Language families · Lang Log by yoshi$/, '$1 · 語族 · Lang Log by yoshi'],
      [/^Language families · Lang Log by yoshi$/, '語族 · Lang Log by yoshi'],
      [/^Signs & Scripts · Lang Log by yoshi$/, '手話と文字 · Lang Log by yoshi'],
      [/^Page not found · Lang Log by yoshi$/, 'ページが見つかりません · Lang Log by yoshi'],
      [/^(.+) · Search results · Lang Log by yoshi$/, '$1 · 検索結果 · Lang Log by yoshi'],
      [/^Search results · Lang Log by yoshi$/, '検索結果 · Lang Log by yoshi'],
      [/^All families · Lang Log by yoshi$/, 'すべての語族 · Lang Log by yoshi'],
      [/^All families and isolates · ([\d,]+)$/, 'すべての語族と孤立言語 · $1'],
      [/^Members · ([\d,]+)$/, '下位の記録 · $1'],
      [/^Members according to Lang Log · ([\d,]+)$/, 'Lang Log による下位の記録 · $1'],
      [/^Recorded names (?:&|and) spellings · ([\d,]+)$/, '記録された名前とつづり · $1'],
      [/^Aliases and spellings · ([\d,]+)$/, '別名とつづり · $1'],
      [/^Related child records · ([\d,]+)$/, '関連する下位の記録 · $1'],
      [/^Catalog classification · ([\d,]+)$/, 'カタログの分類 · $1'],
      [/^Lexical-feature hypotheses · ([\d,]+)$/, '語彙特徴による仮説 · $1'],
      [/^Manual-alphabet evidence · ([\d,]+)$/, '指文字の根拠 · $1'],
      [/^Histories with reviewed relationships · ([\d,]+)$/, '関係を確認した歴史 · $1'],
      [/^Catalog entries without reviewed ancestry · ([\d,]+)$/, '祖先が未確認のカタログ項目 · $1'],
      [
        /^Incompatible study branches · ([\d,]+) source pairs?$/,
        '両立しない研究の分岐 · 出典の組 $1 つ',
      ],
      [
        /^([\d,]+) displayed occurrences · shared IDs may appear in multiple hypotheses$/,
        '表示中 $1 件 · 同じ ID が複数の仮説に出ることがあります',
      ],
      [/^([\d,]+) roots in the list$/, '一覧の根 $1 件'],
      [
        /^Same ([\d,]+) sampled IDs compared · ([\d,]+) incompatible clade pair\(s\) involving this record\.$/,
        '同じ標本 ID $1 個で比較 · この記録に関わる両立しない分岐の組 $2 つ。',
      ],
      [
        /^([\d,]+) genealogical family roots · ([\d,]+) isolates · ([\d,]+) non-genealogical categories$/,
        '系統上の語族の根 $1 · 孤立言語 $2 · 系統でない分類 $3',
      ],
      [
        /^Glottolog 5\.3 \+ WALS \+ (\d+) Phlorest summary trees · Retrieved (.+)$/,
        'Glottolog 5.3 + WALS + Phlorest の要約系統樹 $1 本 · 取得日 $2',
      ],
      [/^Source snapshots retrieved (.+)$/, '資料の取得日 $1'],
      [/^(.+) · expanded according to Glottolog 5\.3$/, '$1 · Glottolog 5.3 に沿って展開'],
      [/^According to (.+?): under (.+)$/, '$1 によると: $2 の下'],
      [/^According to (.+)$/, '$1 による'],
      [/^Placement: (.+)$/, '位置づけ: $1'],
      [/^Source sample \/ record: (.+)$/, '元の標本 / 記録: $1'],
      [/^Source sample: (.+)$/, '元の標本: $1'],
      [/^Other direct members: (.+)$/, 'ほかの直接の下位: $1'],
      [/^Macroarea: (.+)$/, '大地域: $1'],
      [/^All (\S+) models ↗$/, '$1 のモデルをすべて見る ↗'],
      [/^Map: location of (.+)$/, '地図: $1 の位置'],
      [
        /^(language|dialect|family|isolate) · ([\d,]+) sources( · ⚑)?$/,
        function (m, tr) {
          return tr(m[1]) + ' · 出典 ' + m[2] + (m[3] || '');
        },
      ],
      [
        /^(family|language|dialect|isolate|study clade|navigation category) · (.+)$/,
        function (m, tr) {
          return tr(m[1]) + ' · ' + m[2];
        },
      ],
    ],
  },
};
