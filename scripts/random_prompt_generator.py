import random

# 30 Diverse Artistic Styles & Media (画風・画材30種ライブラリ)
STYLES_30 = [
    {
        "name_jp": "【極細ボールペン画】手帳クロスハッチング＆インク溜まり",
        "medium_en": "Intricate multi-directional ballpoint pen drawing on textured cream paper. Fine 0.38mm ballpoint pen linework, authentic microscopic ink blobs, pressure variations, dense shadow cross-hatching, zero digital airbrushing, tactile sketchbook vitality."
    },
    {
        "name_jp": "【シャーペン・メカニカルペンシル】走り書きラフスケッチ",
        "medium_en": "Expressive 0.5mm 2B mechanical pencil drawing. Fast casual drafting strokes, light graphite smudges, eraser trace marks, textured rough tooth paper, raw spontaneous creator sketchbook aesthetic, zero digital gradients."
    },
    {
        "name_jp": "【鉛筆デッサン】黒鉛光沢＆擦筆ぼかし",
        "medium_en": "Fine graphite pencil art with multi-grade 4B-2H sketching strokes. Subtle metallic sheen of graphite dust on heavy tooth drawing paper, blended stump shading against sharp pencil contours, authentic classical drawing physics."
    },
    {
        "name_jp": "【色鉛筆スケッチ】重層混色ワックス感＆紙目テクスチャ",
        "medium_en": "Detailed colored pencil illustration on textured cream Bristol board. Rich multi-layered pigment cross-hatching, luminous wax bloom sheen, visible paper grain tooth showing through strokes, soft organic color transitions."
    },
    {
        "name_jp": "【Gペン・コミック線画】鋭利な抑揚＆漆黒インク",
        "medium_en": "Dynamic Japanese manga line art drawn with sharp G-pen dip pen and deep black drafting ink. Expressive line weight modulation with sharp tapered strokes, intense black cutouts, clean paper white contrast, professional comic illustration aesthetic."
    },
    {
        "name_jp": "【サインペン・マーカー走り書き】油性マジックの潔い線＆かすれ",
        "medium_en": "Bold felt-tip marker and oil-based magic pen drawing. Confident expressive contour lines with organic ink bleed on porous newsprint paper, graphic line weight, casual quick graffiti vitality, un-rendered raw background."
    },
    {
        "name_jp": "【丸ペン極細エッチング】微細銅版画タッチ",
        "medium_en": "Microscopic copperplate etching style illustration drawn with ultra-fine maru-pen. Thousands of delicate parallel hatching lines, razor-sharp detail, vintage engraved book illustration aesthetic on aged parchment."
    },
    {
        "name_jp": "【毛筆と墨・水墨画】渇筆かすれ×破墨にじみ×和紙繊維",
        "medium_en": "Traditional Japanese sumi-e horsehair brush calligraphy art. Dynamic dry-brush friction (kappi) revealing raw fibers, rich black-to-translucent ink wash gradients, accidental expressive ink splatters on absorbent textured washi paper."
    },
    {
        "name_jp": "【フラットデザイン・ゆる絵】ミニマルベクター＆脱力系ライン",
        "medium_en": "Charming minimalist flat design illustration, playful loose vector aesthetic. Clean organic outlines with subtle hand-drawn wobble, simplified geometric shapes, gentle muted pastel color blocking, modern editorial Japanese lifestyle art."
    },
    {
        "name_jp": "【ポスターカラー・アニメ背景画】不透明水彩マット平塗り",
        "medium_en": "Opaque Japanese poster color and matte gouache painting style. Vibrant flat tonal blocking, crisp silhouette edges, velvety non-reflective finish, classic 1980s hand-painted animation background studio aesthetic."
    },
    {
        "name_jp": "【透明水彩画】ウェット・オン・ウェット滲み＆顔料粒状化",
        "medium_en": "Luminous transparent watercolor painting on rough cotton rag paper. Spontaneous wet-on-wet atmospheric bleeds, heavy mineral pigment granulation (sedimentation), delicate backrun puddle rings, glowing paper white highlights."
    },
    {
        "name_jp": "【アクリルガッシュ厚塗り】鮮やかな不透明色面＆筆跡",
        "medium_en": "Vibrant acrylic gouache illustration with visible matte brushwork. Clean planar color transitions, opaque pigment coverage, sharp silhouette shapes, contemporary editorial art aesthetic on heavyweight illustration board."
    },
    {
        "name_jp": "【パレットナイフ重厚油彩】リネン布地＆立体インパスト",
        "medium_en": "Heavy tactile oil impasto with visible palette knife ridges and thick physical paint build-up. Rough dry-brush scumbling over coarse exposed linen canvas weave, rich textural impasto relief with zero flat plastic sheen."
    },
    {
        "name_jp": "【オイルパステル・クレヨン】素朴な掠れ＆厚塗りスクラッチ",
        "medium_en": "Rich oil pastel and wax crayon artwork on rough kraft paper. Heavy buttery pigment texture, tactile crumbly strokes, scratched sgraffito highlights, expressive naive charm and warm earthy density."
    },
    {
        "name_jp": "【チョークアート・黒板画】微細チョーク粉＆指先グラデーション",
        "medium_en": "Artistic chalkboard pastel and chalk illustration on matte slate board. Soft blended chalk powder gradients, crisp chalk dust particles catching the light, authentic blackboard restaurant sign art aesthetic."
    },
    {
        "name_jp": "【木版画・リノカット】彫刻刀の刻み跡＆バレンの擦れ",
        "medium_en": "Traditional woodblock and linocut relief print. Sharp gouge chisel tool marks, organic wood grain texture bleeding through ink, slightly uneven baren rubbing impression on handmade fibrous paper."
    },
    {
        "name_jp": "【リソグラフ印刷】孔版印刷の版ズレ＆蛍光網点ドット",
        "medium_en": "Vintage 2-color Risograph screen print illustration. Distinctive mechanical color separation misregistration (registration overlap errors), soy-ink halftone dot screens, visible uncoated paper tooth, tactile indie zine print."
    },
    {
        "name_jp": "【点描画・スティップリング】ミリペン微細ドット密度",
        "medium_en": "Meticulous pen-and-ink stippling artwork. Form and volumetric shadows rendered exclusively through hundreds of thousands of tiny distinct black pigment ink dots on clean smooth Bristol board, zero solid line fills."
    },
    {
        "name_jp": "【切り絵・ペーパーコラージュ】色画用紙の立体エッジ＆影",
        "medium_en": "Cut-paper collage illustration with clean scissor-cut silhouette edges. Layered textured construction paper creating subtle real cast drop shadows between levels, modern tactile papercraft diorama aesthetic."
    },
    {
        "name_jp": "【昭和レトロ少年漫画調】網点スクリーントーン＆黄ばみ藁半紙",
        "medium_en": "Vintage Showa-era Japanese manga print aesthetic. Coarse mechanical screentone dot patterns, bold energetic ink contours, aged yellowish newsprint pulp paper texture, dynamic nostalgic comic panel atmosphere."
    },
    {
        "name_jp": "【北欧風テキスタイル・イラスト】素朴な有機的パターン＆スタンプ",
        "medium_en": "Scandinavian mid-century textile print illustration. Naive organic floral and architectural motifs, gentle block-print stamp textures, harmonious earthy Nordic color palette, clean linen fabric weave background."
    },
    {
        "name_jp": "【絵本・児童書イラスト】丸みのある温和なフォルム＆優しい筆致",
        "medium_en": "Warm and gentle picture-book illustration. Soft rounded forms, tender hand-colored crayon and watercolor textures, cozy comforting atmosphere, whimsical charming storybook art style."
    },
    {
        "name_jp": "【アイソメトリック・3Dミニチュア風】等角投影ジオラマ＆クリーン陰影",
        "medium_en": "Delightful isometric projection miniature diorama artwork. Clean 30-degree orthographic perspective, crisp architectural micro-details, soft diffused studio clay lighting, intricate tilt-shift scale feeling."
    },
    {
        "name_jp": "【ピクセルアート・ドット絵】16bit精緻ドット＆ノスタルジー",
        "medium_en": "Exquisite 16-bit pixel art illustration. Crisp pixel-perfect grid placement, carefully limited color palette with artistic manual dithering, nostalgic retro gaming aesthetic with rich environmental lighting."
    },
    {
        "name_jp": "【建築パース・コピック着彩スケッチ】ミリペン×アルコールマーカー",
        "medium_en": "Architectural concept design presentation sketch. Precision technical fineliner pen linework overlaid with rapid alcohol marker (Copic) translucent color washes, fluid design studio marker strokes, white gel-pen highlights."
    },
    {
        "name_jp": "【現代厚塗りアニメ調】面構成ブラシ＆環境光アンビエント",
        "medium_en": "Contemporary thick impasto anime illustration with rich planar facet brush transitions. Sophisticated ambient occlusion shading, crisp edge definition without line art dependency, atmospheric light bloom."
    },
    {
        "name_jp": "【90年代ヴィンテージ・セル画】トレス線＆ハンドペイントガッシュ",
        "medium_en": "Authentic 1990s retro anime cel artwork. Hand-painted acrylic vinyl gouache colors on acetate cel sheet, subtle physical xerox toner line grain, warm nostalgic animation studio production photography quality."
    },
    {
        "name_jp": "【銀残しシネマティック】ブリーチバイパス硬質フィルムトーン",
        "medium_en": "Cinematic bleach bypass film still process. Desaturated earthy chromatic base, deep silver-tinted soot shadows, high-contrast gritty textural edge sharpness, tangible atmospheric humidity, zero neon wash."
    },
    {
        "name_jp": "【サイアノタイプ・日光写真】プルシアンブルー単色＆感光滲み",
        "medium_en": "Classic cyanotype alternative photography process. Deep Prussian blue and cyan monochrome tones, soft chemical edge bleeds, tactile rag paper texture, ethereal silhouette sun-print atmosphere."
    },
    {
        "name_jp": "【チャコール・木炭デッサン】柳炭の漆黒＆練りゴムハイライト",
        "medium_en": "Dramatic willow charcoal drawing on heavy fibrous paper. Deep velvety soot-black shadows, dusty charcoal powder textures, bold kneaded-eraser subtractive highlight marks, expressive atmospheric chiaroscuro."
    }
]

# 4-Axis Matrix (人 × 時刻 × 季節 × 場所)
PEOPLE = [
    {"name": "救急病棟の女性看護師", "desc": "首元に柔らかな疲労感と静かな安堵の表情、無造作に束ねた髪と目の下の微かなクマ、澄んだ眼差し", "item": "手首のシリコンバンドスマートウォッチと透明な目薬のボトル", "gaze": "静かな虚無と安堵の視線"},
    {"name": "町工場の旋盤職人", "desc": "深く刻まれた眉間のシワ、使い込まれた保護メガネの奥に宿るミリ単位の鋭い眼光、油煙と鉄粉に燻された肌", "item": "ミツトヨ製デジタルノギスとシンワ製ステンレス直尺", "gaze": "金属の切削接点（火花が散るミクロ焦点）を捉える極度の集中視線"},
    {"name": "通学路の男子高校生", "desc": "風に乱れた前髪、冬には白い息を吐き夏には汗が光る額、若さゆえの鋭敏さとアンニュイな横顔", "item": "水滴のついた透明ビニール傘と撥水加工ナイロンリュックサック", "gaze": "遠くの光や案内板を見上げる斜め上方へのシャープな視線"},
    {"name": "温室アトリエのフローリスト", "desc": "手早く茎を揃える器用な指先、植物の葉緑素で染まった爪先、穏やかで生命力に満ちた柔らかな笑み", "item": "革巻きハンドルの剪定ばさみと麻紐のロール", "gaze": "束ねたブーケの中心軸を見つめ、花の配置と茎の長さを測る温かな視線"},
    {"name": "路地裏の中華料理人", "desc": "炎の熱気で紅潮した頬、太い腕の血管、長年の厨房立ち仕事で培われた揺るぎない体幹と精悍な口元", "item": "油が漆黒に焼き付いた鉄製北京鍋と使い込まれた木柄の中華お玉", "gaze": "強火の中で一瞬にして熱が通る具材の跳躍を見切る動体視線"},
    {"name": "尺八を奏でる老演奏家", "desc": "風にそよぐ豊かな銀髪、節くれだった指先、世俗を離れた静謐さと枯淡の美が宿る端正な骨格", "item": "竹の節と漆塗りの歌口が美しい銘木尺八と手作りの和紙楽譜", "gaze": "目を閉じる寸前の半眼で音の余韻を遠く夕空へ放つ超越的視線"},
    {"name": "移動中の女子大生", "desc": "西日や木漏れ日に透ける琥珀色の髪、耳たぶに差す血色の赤み、知性と好奇心が同居する涼やかな瞳", "item": "使い込まれた文庫本と帆布の生成りキャンバストートバッグ", "gaze": "通過する電車の窓や街路樹の葉の揺らめきを追う静かな視線"},
    {"name": "ネルドリップの喫茶店マスター", "desc": "丁寧に手入れされた髭、静止したようにブレない手元、湯気の中で香りを嗅ぎ分ける研ぎ澄まされた集中力", "item": "使い込まれた銅製細口ドリップポットと褐色のネルフィルター", "gaze": "ポットの注ぎ口から落ちる湯の雫の先端を捉え続ける静止した眼差し"},
    {"name": "深夜帰りのITエンジニア", "desc": "画面を見つめ続けた後の微かな眼精疲労、端正な顔立ち、夜の街を颯爽と歩く知的でストイックな佇まい", "item": "薄型ノートPCと大口径ノイズキャンセリングヘッドホン", "gaze": "スマートフォンの画面に反射する光を冷静に見つめながら進む視線"},
    {"name": "市場の仲卸人", "desc": "潮風と水仕事で鍛え上げられた分厚い手、声の張りを感じさせる引き結んだ唇、活気と気風の良さ", "item": "鋼の小出刃包丁と砕氷の詰まった発泡スチロール箱", "gaze": "魚の鮮度と目利きの瞬間に光る職人の鑑識眼"},
    {"name": "設計事務所の建築士", "desc": "徹夜明けの真剣な横顔、鉛筆を髪に差した無造作なスタイル、空間の美学を追い求めるクリエイターの瞳", "item": "精密なスチレンボード模型と金属定規、デザインナイフ", "gaze": "模型のミリ単位の接合部を斜め上方から厳しく見極める視線"},
    {"name": "アトリエの美大生", "desc": "絵の具が飛び散ったキャンバス地エプロン、木炭の粉で汚れた指先、モチーフを鋭く捉える芸術家の眼差し", "item": "木炭ホルダーと練り消しゴム、分厚いスケッチブック", "gaze": "キャンバスとモチーフの間を高速で往復する研ぎ澄まされた観察眼"},
    {"name": "地方路線の鉄道駅員", "desc": "折り目の正しい制服、風雪に耐えた肌、乗客の安全を見守る誠実な責任感を帯びた真っ直ぐな視線", "item": "銀色に光る鉄道懐中時計と合図灯、黒革の手帳", "gaze": "遠くのカーブから進入してくる電車のヘッドライトを待つ直進視線"}
]

TIMES = [
    {"name": "早朝（5:00-6:30）", "desc": "群青から淡い薄紅へと移ろう地平線の境界光。青白い蛍光灯の冷光と朝霧、目覚めぬ街の静寂と澄んだ空気"},
    {"name": "朝（7:30-9:00）", "desc": "建物の隙間から鋭く差し込む爽快な朝の斜光。歩道を行き交う人々の長い影、瑞々しい光の粒子"},
    {"name": "昼・正午（11:30-13:30）", "desc": "真上から容赦なく降り注ぐ力強い太陽光。コントラストの強い短い影、活気に満ちた明度と熱気"},
    {"name": "夕暮れ・黄昏（16:30-18:00）", "desc": "街全体を燃えるような赤銅色と黄金色に染め上げる西日の長い斜光。ガラス窓やレールの反射光、紫紺へと変わる夕空"},
    {"name": "夜・宵の口（19:30-21:30）", "desc": "暖かなオレンジの白熱灯と店の看板の灯り。アスファルトに反射する車のテールランプ、夕餉の香りと温かみ"},
    {"name": "深夜（23:30-2:00）", "desc": "自動販売機やコンビニから漏れる孤高の冷たいLED光。静まり返った闇に浮かぶシルエット、遠くの街灯が落とす孤独で美しい陰影"}
]

MONTHS = [
    {"m": 1, "name": "1月（睦月）", "season": "winter", "desc": "新春の身を切るような乾いた寒気、澄み渡る冬空、薄っすら積もった初雪の微細な反射光と吐く息の白さ"},
    {"m": 2, "name": "2月（如月）", "season": "winter", "desc": "冬の底にある厳しい余寒、夕暮れの冷たい残照、まだ固い梅の蕾、凍てつくアスファルトの冷気"},
    {"m": 3, "name": "3月（弥生）", "season": "spring", "desc": "早春の淡く柔らかな光、雪解けのしずく、春一番の生ぬるい風、土から芽吹き始めた草木の匂い"},
    {"m": 4, "name": "4月（卯月）", "season": "spring", "desc": "陽春のうららかな陽射し、風に舞い散る淡紅の桜吹雪、新しい生活の始まりを告げる光の粒子"},
    {"m": 5, "name": "5月（皐月）", "season": "spring", "desc": "若葉を揺らす爽快な薫風、鮮烈な初夏の日差し、木漏れ日の心地よい揺らめき、五月晴れの青空"},
    {"m": 6, "name": "6月（水無月）", "season": "rainy", "desc": "しとしとと降り続く梅雨の長雨、紫陽花を濡らす水滴、湿度を帯びたしっとりとした空気と路面の照り返し"},
    {"m": 7, "name": "7月（文月）", "season": "summer", "desc": "照りつける強烈な真夏の直射日光、青空に湧き立つ巨大な白い入道雲、アスファルトに揺らめく陽炎"},
    {"m": 8, "name": "8月（葉月）", "season": "summer", "desc": "夕暮れの激しい夕立の雨上がり、ヒグラシの声、立ち上る湿った熱気とひんやりとした夕立ち後の涼風"},
    {"m": 9, "name": "9月（長月）", "season": "autumn", "desc": "初秋の澄み渡る高い青空、風にちぎれる鰯雲、夕暮れに忍び寄る心地よい涼風と長くなり始めた影"},
    {"m": 10, "name": "10月（神無月）", "season": "autumn", "desc": "爽快な秋晴れの乾いた光、風に乗って漂う金木犀の甘い香り、黄色く色づき始めた街路樹の落ち葉"},
    {"m": 11, "name": "11月（霜月）", "season": "autumn", "desc": "晩秋の木枯らしが吹き抜ける街角、低く傾いた茜色の夕陽、朝露が凍る初霜の冷たさと枯れ葉の匂い"},
    {"m": 12, "name": "12月（師走）", "season": "winter", "desc": "凍てつく初冬の夜風、街を彩る暖かなイルミネーションの光、マフラーに顔を埋める人々の白い息"}
]

LOCATIONS = [
    {"name": "無人コインランドリー", "desc": "整然と並んだ回転乾燥機の青白いLEDと丸窓、湿った温風の匂い、リノリウム床の反射"},
    {"name": "下町の金属加工町工場", "desc": "切削油と鉄粉の匂いが染み付いた厚い木製作業台、壁に整然と掛かる工具、天井の裸電球の温かな光"},
    {"name": "雨上がりの駅前バスターミナル", "desc": "水たまりに美しく滲むバスの赤色テールランプと電光案内板、濡れたアスファルトの黒い光沢"},
    {"name": "ガラス温室の生花アトリエ", "desc": "鉄骨トラスのガラス天井から注ぐ柔らかな光、湿った土と切り花の芳香、作業台に散乱する緑の小枝"},
    {"name": "路地裏の深夜中華厨房", "desc": "火柱が豪快に上がる北京鍋、ステンレスの換気ダクトに跳ねる油の光、立ち上る白濁した湯気と熱気"},
    {"name": "高架下のコンクリート橋脚下", "desc": "巨大なコンクリート柱が落とす深い影、西日の斜光が切り裂く埃っぽい空間、遠くを通過する電車の重低音"},
    {"name": "住宅街の黄色いガードレール踏切", "desc": "夕陽を反射して黄金色に輝く鉄路、黄色と黒のストライプ遮断機、路地裏の家庭的な植木鉢"},
    {"name": "昭和レトロな純喫茶のカウンター", "desc": "琥珀色のステンドグラス照明、磨き込まれたマホガニーのカウンター木目、ネルドリップと銅製器具"},
    {"name": "海を望む濡れた急坂の住宅街", "desc": "濡れたアスファルトが夕陽を反射する急な坂道、坂の向こうに小さく見える瀬戸内の水平線と電車の架線"},
    {"name": "早朝の地方卸売市場の荷捌き場", "desc": "砕氷の白い山と水浸しのコンクリート床、立ち込める水蒸気、黄色い回転灯を回すフォークリフト"},
    {"name": "深夜の建築設計事務所", "desc": "机の上に散乱するトレーシングペーパーとスチレンボード建築模型、ディスプレイの残光"},
    {"name": "海沿いの古い防波堤と木製ベンチ", "desc": "潮風に晒されたコンクリートとテトラポッド、水面にきらめく無数の光片、遠くを往く貨物船の汽笛"}
]

ATTIRES = {
    "winter": ["ざっくり編まれたアラン模様の肉厚フィッシャーマンズウールセーターとウールマフラー", "襟元にコーデュロイ切り替えのある防寒オイルドコットンジャケットとチノパン", "本水牛トグルボタンの肉厚ウールメルトン製ダッフルコートと厚手首巻きマフラー"],
    "summer": ["洗いざらしの7.5oz極厚コットンポケットTシャツとロールアップした赤耳セルビッジデニム", "風通しの良い天然ウォッシュドリネンの半袖オープンカラーシャツとチノショーツ", "機能的なリップストップナイロン製メッシュユーティリティベストと速乾Tシャツ"],
    "spring": ["洗いざらしのオックスフォード地ボタンダウンシャツと生成りコットンのカーディガン", "薄手ウォッシュドコットンツイル製スイングトップジャケットとボーダーカットソー", "シワ感のあるフレンチリネン混紡シャツとライトウェイトニットベスト"],
    "autumn": ["オイルドコットンのフィールドジャケットと赤黒ブロックチェックのヘビーフランネルシャツ", "経年変化した14.5oz赤耳セルビッジデニムジャケットとモックネックTシャツ", "厚手コットンダック生地のチョアジャケットとヘビーウェイトスウェット"],
    "rainy": ["3レイヤー耐水圧ゴアテックスシェルジャケットと撥水リップストップナイロンパンツ", "撥水加工の厚手ウインドブレーカーと耐水ワークブーツ"]
}

FLUORESCENT_COLORS = [
    ("ピンク", "vibrant glowing neon fluorescent pink"),
    ("シルバー", "luminous shimmering fluorescent metallic silver"),
    ("ゴールド", "radiant gleaming fluorescent metallic gold"),
    ("イエロー", "vibrant blazing neon electric yellow"),
    ("グリーン", "vibrant glowing neon lime green"),
    ("ホワイト", "luminous intense fluorescent chalk white"),
    ("パープル", "vibrant glowing neon electric violet-purple")
]

from datetime import datetime, timezone, timedelta

def get_jst_today_str():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).strftime("%Y-%m-%d")

def generate_random_prompt(tag_text=None, target_date=None):
    date_str = target_date or get_jst_today_str()
    person = random.choice(PEOPLE)
    time = random.choice(TIMES)
    month = random.choice(MONTHS)
    location = random.choice(LOCATIONS)
    attire = random.choice(ATTIRES[month["season"]])
    style_obj = random.choice(STYLES_30)
    color_jp, color_en = random.choice(FLUORESCENT_COLORS)
    
    if tag_text:
        selected_tag = tag_text
    else:
        selected_tag = f"{date_str}#本日の高度GAS"
        
    layout_type = "two_line" if "デジタル資産" in selected_tag else "single_line"
    
    if layout_type == "two_line":
        # Extract title part after '#'
        title_part = selected_tag.split("#", 1)[1] if "#" in selected_tag else selected_tag
        text_layout = f"2 centered lines: top line '{date_str}#', bottom line '{title_part}'"
    else:
        text_layout = f"single prominent line '{selected_tag}'"

    # NOTE: Do NOT prepend "Aesthetic anime illustration in ..." which forces anime watercolor!
    # Let the chosen medium lead directly.
    prompt = f"""{style_obj['medium_en']}
Scene: {month['name']}（{month['season']}）の{time['name']}、{location['name']}にて。
Subject: {person['name']}。{person['desc']}。手元には{person['item']}。服装は{attire}。
Environment: {location['desc']}。{time['desc']}。{month['desc']}。Gaze: {person['gaze']}。
Texture: authentic physical medium grain and stroke resistance, zero synthetic airbrush gradients, zero smooth plastic 3D CG look.

CRITICAL COMPOSITION & TEXT RULE:
Directly across the EXACT GEOMETRIC CENTER of the image (floating prominently right in the dead middle of the canvas, strictly at vertical center Y=50% and horizontal center X=50%, NEVER placed at the bottom, top, or edges), large prominent handwritten Japanese text is scribbled in {text_layout} in {color_en} felt-tip marker pen ink.
The handwriting features masterfully fluid, calligraphic sweeping strokes, authentic ink bleeds, natural pressure variations, and a deep dark drop-shadow glow contour closely hugging the text for extreme contrast and instant mobile tap appeal. Authentic handwritten signature ink aesthetic with exquisite penmanship, impossible to miss on mobile feeds."""

    return {
        "person": person["name"],
        "time": time["name"],
        "month": month["name"],
        "location": location["name"],
        "style_jp": style_obj["name_jp"],
        "color_jp": color_jp,
        "color_en": color_en,
        "tag": selected_tag,
        "prompt": prompt
    }

if __name__ == "__main__":
    res = generate_random_prompt()
    print("=== SCENARIO METADATA ===")
    print(f"画風・画材: {res['style_jp']}")
    print(f"人物: {res['person']}")
    print(f"季節/月: {res['month']}")
    print(f"時刻: {res['time']}")
    print(f"場所: {res['location']}")
    print(f"サイン色: {res['color_jp']}")
    print(f"サイン: {res['tag']}")
    print("\n=== GENERATED PROMPT ===")
    print(res["prompt"])
