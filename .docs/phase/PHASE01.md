# PHASE01：プロジェクト状況整理と要件確認

**作成日**: 2026-02-05  
**対象ブランチ**: `version02`  
**最新コミット**: `07a9383` - "requestのjsonを未理解。"

---

## 1. プロジェクト概要

### プロジェクト名
`pokecode` - ポケモン関連のコードプロジェクト

### 主な目的
外部APIまたはローカルサーバーに対して、HTML/JSONのリクエストを送信し、レスポンスを処理するシステムの構築

### 技術スタック
- **言語**: Python 3.14+
- **主要ライブラリ**:
  - `requests`: HTTPリクエスト
  - `beautifulsoup4`: HTMLパース
  - `flask`: ローカルサーバー
  - `qrcode`: QRコード生成
  - `pytest`: テスト

---

## 2. 現在の状況

### ブランチと履歴概要

```
07a9383 (HEAD -> version02)   requestのjsonを未理解。
2ac0704                       mainの例外を整理
5defe87                       main未整理
158f261 (origin/version01)    legacyを訂正
c092baf                       mypyをactionsから省略
2e5a939                       actionsを導入
ad9d627                       整理完了
215ff04                       _appを_lagecyに移動
...
```

### ブランチ構成
- **master**: v0.1.0 の安定版（215ff04)
- **version01**: v0.1 の安定版（158f261）
- **version02**: 現在の開発ブランチ（07a9383）

---

## 3. コア実装の現在状況

### 3.1 `main.py` - アプリケーション入口

**状態**: 混乱状態（コメントアウトコードが大量）

**現在の実装**:
```python
def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="INFO")
    logger.info("Application Start.")
    
    try:
        data = load_config(PYPROJECT)
        url = data["tool"]["pokecode"]["localhost_html"]
        html = request_html(url=url)
        print(html)
    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)
    finally:
        logger.info("Application End.")
```

**問題点**:
- コメント化された旧実装が存在（`request_json` を使用していた版）
- 現在は HTML リクエストのみを実装

### 3.2 `request_html.py` - HTMLリクエスト処理

**状態**: ⚠️ **未実装**（型定義のみ）

```python
def request_html(*, url: str) -> HtmlResult:
    if not (url, str):  # ← バグ：条件が不正
        raise ValueError("url is not str: %s", type(url))
    return  # ← 実装なし
```

**問題点**:
1. 関数本体が実装されていない（`return` のみ）
2. 条件判定が誤り（`(url, str)` は常に True）
3. コメント化された実装がある（参考用？）
   - `raise_for_status_with_log()` - HTTPエラーハンドリング
   - `parse_html_with_log()` - HTML解析

### 3.3 `request_json.py` - JSONリクエスト処理

**状態**: ✅ **比較的完成**（エラーハンドリング充実）

**実装済みの機能**:
- ✅ JSONリクエスト送信
- ✅ HTTPステータスチェック
- ✅ Content-Type 検証
- ✅ JSONパース処理
- ✅ 詳細なエラーメッセージ
- ✅ ResponseContext でコンテキスト情報を保持

**エラークラス**:
- `ContractViolationError`: API契約違反（基底）
- `InvalidContentTypeError`: Content-Type が JSON でない
- `InvalidJSONError`: JSON パース失敗
- `InvalidJSONTypeError`: JSON は有効だが dict/list でない

### 3.4 `logconfig.py` - ログシステム

**状態**: ✅ **実装済み**（但し既知の問題あり）

**既知の問題** (CASE01.md より):
- **StreamHandler の増殖**: pytest 実行時に StreamHandler が重複生成される
  - 1回目実行: StreamHandler × 1
  - 2回目実行: StreamHandler × 2
  - N回目実行: StreamHandler × N
- 現在、重複検出メカニズムがある（ハンドラ名で確認）

**実装内容**:
- `setup_logging()`: Logger の初期化（StreamHandler + RotatingFileHandler）
- StreamHandler の重複チェック（`_CONSOLE_NAME` で同定）

---

## 4. 未解決の課題

### 4.1 優先度: **高** 🔴

1. **`request_html.py` の実装**
   - 現在: 未実装（バグがある）
   - 要件: `request_json.py` の同等のエラーハンドリングを実装
   - 参考: コメント化されたコード内の実装パターン

2. **JSON リクエストの理解を深める**
   - コミットメッセージ: "requestのjsonを未理解。"
   - `request_json.py` は実装済みだが、何が理解できていないのか不明確
   - `main.py` で `request_json` を使用していない理由が不明

### 4.2 優先度: **中** 🟡

3. **LogHandler の増殖問題の解決**
   - 既知問題： StreamHandler が重複生成される
   - 現在の対策: handler.name による重複チェック
   - 検証: 実際に修正されているか確認が必要

4. **`main.py` の整理**
   - コメント化コードの削除
   - `request_html` と `request_json` の使い分けルール を明確化

### 4.3 優先度: **低** 🟢

5. **Flask サーバーの役割確認**
   - `server/app.py` と `server/create_qr.py` の実装が不明確
   - ローカルテスト用？本番用？

6. **READMENがない**
   - `README.md` は空のまま

---

## 5. 次のステップ（PHASE02 以降）

### **PHASE02**: `request_html.py` の実装
- [ ] `request_html()` 関数の完全実装
- [ ] `request_json.py` と同等のエラーハンドリング
- [ ] テストコード作成

### **PHASE03**: JSON リクエストの理解深掘り
- [ ] `request_json()` 使用例の確認・整理
- [ ] `main.py` で `request_json` を使用するケースの検討
- [ ] HTMLリクエストとの使い分けルール定義

### **PHASE04**: ログシステムの検証
- [ ] StreamHandler 増殖問題の本当の修正状況を確認
- [ ] テストケース追加

### **PHASE05**: 統合テストと整理
- [ ] `main.py` のコメント化コード削除
- [ ] 全体統合テスト
- [ ] ドキュメント整備

---

## 6. 設定情報（参考）

### pyproject.toml 抜粋

```toml
[tool.pokecode]
logdir = "logs"
logfile = "app.log"
debug_logdir = "debug_log"
debug_logfile = "debug.log"

localhost_html = "http://localhost:5000"
localhost_json = "http://localhost:5000/json"
```

### ディレクトリ構成

```
pokecode/
├── .docs/              # ドキュメント
│   ├── CASE01-03.md    # 既知問題の分析
│   ├── EXPLAIN01-10.md # 各トピックの説明
│   ├── PYTEST01.md     # テスト関連
│   └── phase/          # 開発フェーズドキュメント
│       └── PHASE01.md  ← このファイル
├── src/pokecode/       # メインコード
│   ├── main.py         # エントリーポイント
│   ├── config.py       # 設定読み込み
│   ├── request_html.py # ⚠️ 未実装
│   ├── request_json.py # ✅ 実装済み
│   ├── logconfig.py    # ✅ 実装済み（既知問題あり）
│   ├── loading.py
│   ├── getpath.py
│   └── .legacy/        # 古いコード
├── server/             # Flask サーバー
│   ├── app.py
│   ├── create_qr.py
│   └── static/, templates/
├── tests/              # テストコード
├── lesson/             # 学習用？
└── logs/               # 実行時ログ出力
```

---

## 7. まとめ

**現在の状態**: 開発途中で混乱状態

**最大の課題**:
1. `request_html.py` が未実装
2. JSON リクエスト機能の理解が不十分（コミットメッセージより）

**直近のアクション**:
- **PHASE02**: `request_html.py` を完成させる
- **PHASE03**: `request_json.py` の理解を深める

---
