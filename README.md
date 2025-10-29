非エンジニア向け 手順書（3支局のエクセルZIPを自動取得→Notion更新→差分レポート）

対象
- 四国厚生局（愛媛）
- 近畿厚生局（兵庫）
- 九州厚生局（福岡）

ゴール
1) NotionのDBを月次で自動アップサート
2) 先月との差分があれば、変化の分析と営業提案までを含むレポートを自動作成

前提
- GitHubアカウントあり
- Googleアカウントあり（共有ドライブを使う）
- Notionを使用（フリープランで可）

ステップ0 準備
1. GitHubで新しいリポジトリを作成（PublicでもPrivateでも可）
2. このフォルダの内容をそのままアップロードする（後述のZIPを解凍して丸ごと入れる）
3. GitHubのSettings → Secrets and variables → Actions → New repository secret で以下を登録
   - NOTION_TOKEN：Notionのインテグレーショントークン
   - NOTION_DB_ID：作成したNotionデータベースのID
   - GDRIVE_SERVICE_ACCOUNT：サービスアカウントのJSON文字列（後述）
4. Google Cloudでサービスアカウントを作成し、キーファイル（JSON）をダウンロード
   - Google Cloud Console → IAMと管理 → サービス アカウント → 作成
   - 役割はドライブの読み書きができるもの
   - ダウンロードしたJSONの中身をそのままコピーし、GitHubのGDRIVE_SERVICE_ACCOUNTに貼り付け
5. Google Driveに共有ドライブを作成し、上記サービスアカウントをメンバー追加（コンテンツ管理）
6. Notionでデータベースを新規作成し、プロパティを用意（最低限）
   - 施設名（Title）
   - 施設キー（Text）
   - 都道府県（Text または Select）
   - 住所（Text）
   - 電話（Text）
   - 届出項目（Multi-select）
   - 算定開始年月（Date または Text）
   - 拠点（Select：神戸、松山、北九州）
   - 状態（Select：新規、拡張、継続、失効）
   - 優先度スコア（Number）
   - 最終更新日（Date）
   - ソースURL（URL）
   - 原本ハッシュ（Text）
   - 変更点サマリ（Rich text）
   データベースのURL末尾のIDをNOTION_DB_IDに設定
7. Notionの設定→連携からインテグレーションを作成し、データベースに連携を招待

ステップ1 設定ファイルの編集
- src/config.yaml を開き、共有ドライブ名などを自分の環境に合わせて修正

ステップ2 GitHub Actionsの有効化
- .github/workflows/monthly.yml は毎月第2週の平日10:30（JST）に実行
- リポジトリにpushすると有効化

ステップ3 初回テスト実行
- GitHubのActionsタブで手動実行
- Google Driveのsnapshots、raw、xlsx、reports に成果物が出る
- Notion DBにレコードが作成・更新される

ステップ4 運用
- 毎月自動で実行
