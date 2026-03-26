# SNSメトリクス取得ツール

## セットアップ

```bash
cd sns_metrics
```

## 使い方

### 1. YouTube（API経由・正確）

**事前準備**: Google Cloud ConsoleでAPIキーを取得する
1. https://console.cloud.google.com/ にアクセスする
2. プロジェクトを作成する（名前は何でもOK）
3. 「APIとサービス」→「ライブラリ」→ `YouTube Data API v3` を有効にする
4. 「認証情報」→「認証情報を作成」→「APIキー」を選択する
5. `fetch_youtube.py` の `API_KEY` に貼り付ける

```bash
uv run fetch_youtube.py
```

### 2. TikTok / Instagram / Facebook / X（スクレイピング）

Chromeがインストールされていれば追加設定不要。

```bash
uv run fetch_sns.py
```

ブラウザが自動で開き、各プラットフォームにアクセスしてメトリクスを取得する。
ログイン画面が出た場合はスキップするか、手動でログインする。

## 出力

`results/` フォルダにJSONファイルが保存される:
- `youtube.json` — YouTube統計
- `sns_metrics.json` — TikTok/Instagram/Facebook/X統計
