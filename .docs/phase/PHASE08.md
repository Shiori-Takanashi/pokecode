# PHASE 08: スクレイピング機能の統合と翻訳サービスの拡張

## 目的

国別フレンドコード取得機能を完成させ、翻訳サービスの拡張、URL構築、キャッシュ管理機能を実装する。

## 変更内容

### 1. 設定管理のクラス化（config.py）

**目的**: 設定取得を統一されたインターフェースで提供

**変更内容**:
- 関数からクラスベースの `ConfigGetter` に変更
- `get_url()` → `get_domain()` に変更し、環境変数をより明確に
- `get_output_file(name: str)` に変更し、柔軟なファイル名指定を可能に
- 未使用の `PYPROJECT` インポートを削除

**メリット**:
- 設定取得のインターフェースを統一
- 環境変数が設定されていない場合のエラーハンドリング改善
- コードの可読性向上

### 2. キャッシュ削除機能の追加（cache.py）

**新規メソッド**:
```python
def delete(self) -> None:
    """キャッシュを削除する"""
    self.cache = {}
    self.cache_file.unlink(missing_ok=True)
```

**用途**: テストやデバッグ時にキャッシュをクリアする機能を提供

### 3. URL構築機能の追加（url_builder.py）

**新規ファイル**: `src/pokecode/url_builder.py`

**目的**: 国コードからURLを動的に構築

**実装**:
```python
def build_url_with_code(*, domain: str = "None", code: str = "None") -> str:
    """国コード（ISO Alpha-3）からURLを構築する"""
    if code == "None" or len(code) != 3:
        raise ValueError("codeが不正です。")

    if domain == "None":
        cg = ConfigGetter()
        url = cg.get_domain()
        url_with_code = f"{url}/?country={code}"
    else:
        url_with_code = f"{domain}/?country={code}"

    return url_with_code
```

**特徴**:
- 国コードのバリデーション（3文字チェック）
- 設定からドメインを自動取得
- ログ出力による追跡可能性

### 4. スクレイピング機能の拡張（scraping.py）

**追加された機能**:
```python
def scrape_friend_code_from_trainer(trainer: Tag) -> str:
    """トレーナー情報からフレンドコードを抽出"""
    button = trainer.select_one("div.card > div.card-body > button")
    if button is None:
        raise ValueError("buttonが発見できません。")
    friend_code = button["data-friend-code"]
    if isinstance(friend_code, str):
        return str(friend_code)
    else:
        return ""
```

**削除された機能**:
- `scrape_from_tagname()`: 未使用のため削除
- `scrape_tag_of_html()` → `scrape_html()` に名前変更

**クリーンアップ**:
- 未使用の型エイリアス `TargetElement` を削除
- コードの可読性向上

### 5. 翻訳サービスの改善（translation.py）

**追加機能**:
```python
def translate_countries_batch(
    self,
    *,
    countries: list[dict[str, str]],
    ignore_cache: bool = False,  # 新規
    batch_size: int = 10,
) -> list[dict[str, str]]:
```

**改善点**:
1. `ignore_cache` パラメータの追加
   - キャッシュを無視して再翻訳する機能
   - デバッグやテストに有用

2. プロンプトの改善
   - 「直訳ではなく、日本語の正式名称で翻訳」を明示
   - 具体例を追加（サモア → サモア独立国）
   - 出力形式を明確化

### 6. メイン処理の拡張（main.py）

**新機能**:
1. 翻訳サービスの統合
   - 国名の日本語翻訳処理を追加
   - バッチ処理により効率的に翻訳

2. URL構築とフレンドコード取得
   - 国コードからURLを生成
   - 各国のフレンドコード一覧を取得
   - JSON形式で保存

3. 出力ファイルの改善
   - `counties.json`: 国情報の保存
   - `countries_translated.json`: 翻訳結果の保存
   - `url_with_code.json`: 生成されたURL一覧
   - `friend_codes_of_{code}.json`: 国別フレンドコード

**処理フロー**:
```
1. HTML取得 → 2. 国リスト抽出 → 3. 翻訳 → 4. URL生成 → 5. フレンドコード取得
```

### 7. 型定義のクリーンアップ

**request_html.py**:
- 未使用の型エイリアス `HtmlResult` を削除
- 直接 `str` を返り値として使用

**scraping.py**:
- 未使用の型エイリアス `TargetElement` を削除
- 型ヒントをよりシンプルに

### 8. ファイル削除

**削除**: `src/pokecode/request_json.py`

**理由**:
- 現在の実装ではJSON APIを使用していない
- HTMLスクレイピングに集中
- 必要になった際に再実装可能

## 影響範囲

| ファイル | 変更タイプ | 説明 |
|---------|----------|------|
| `config.py` | 🔄 リファクタリング | クラスベースに変更 |
| `cache.py` | ➕ 機能追加 | `delete()` メソッド追加 |
| `url_builder.py` | ✨ 新規作成 | URL構築機能 |
| `scraping.py` | ➕ 機能追加 | フレンドコード抽出機能 |
| `translation.py` | 🔄 改善 | プロンプト改善、キャッシュ制御 |
| `main.py` | ➕ 機能追加 | 翻訳・フレンドコード取得統合 |
| `request_html.py` | 🧹 クリーンアップ | 型エイリアス削除 |
| `request_json.py` | ❌ 削除 | 未使用機能の削除 |

## 実装上の注意点

### 1. エラーハンドリング

すべての新機能で適切なエラーハンドリングを実装：
- バリデーションエラー（国コード長など）
- パース失敗時の詳細なログ出力
- リトライやフォールバック機能

### 2. ログ出力

各処理段階でログを記録：
- デバッグレベルでの詳細情報
- インフォレベルでの進捗状況
- エラーレベルでの問題報告

### 3. テスト容易性

- 各関数は独立してテスト可能
- キャッシュのクリア機能により、テストの独立性を確保
- モック可能な設計

## 次のステップ (PHASE09)

1. **テスト実装**
   - URL構築のユニットテスト
   - スクレイピング機能のテスト
   - 翻訳サービスのモックテスト

2. **パフォーマンス改善**
   - 並列リクエスト処理
   - キャッシュ戦略の最適化
   - バッチサイズの調整

3. **エラーハンドリング強化**
   - リトライロジックの追加
   - タイムアウト処理の改善
   - より詳細なエラーメッセージ

4. **ドキュメント整備**
   - API仕様書の作成
   - 使用例の追加
   - トラブルシューティングガイド

## 完了日

2026-02-07
