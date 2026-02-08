# 国名日本語翻訳機能の設計書

## 概要
OpenAI APIを使用して、英語の国名を日本語に翻訳する機能を実装する。

## 目的
- `result01.json`の`.country_name`フィールドを日本語翻訳するための基盤を構築
- 効率的でバッチ処理可能な翻訳機能の提供
- 翻訳結果のキャッシング機構

## 設計

### モジュール構成

#### 1. `pokecode/translation.py` (メインモジュール)

**関数定義：**

##### `translate_country_name(country_name: str) -> str`
- 単一の国名を日本語に翻訳
- キャッシュから取得可能な場合はAPIを呼び出さない
- **入力例**: "Afghanistan" → **出力例**: "アフガニスタン"

##### `translate_countries_batch(countries: list[dict[str, str]]) -> list[dict[str, str]]`
- 複数の国リストを一括翻訳
- `.country_name`フィールドを対象に翻訳し、新しい`country_name_ja`フィールドを追加
- バッチ処理でOpenAI APIの呼び出し回数を最小化
- **入力例**:
  ```python
  [
    {"iso_alpha3": "AFG", "country_name": "Afghanistan"},
    {"iso_alpha3": "ALB", "country_name": "Albania"}
  ]
  ```
- **出力例**:
  ```python
  [
    {"iso_alpha3": "AFG", "country_name": "Afghanistan", "country_name_ja": "アフガニスタン"},
    {"iso_alpha3": "ALB", "country_name": "Albania", "country_name_ja": "アルバニア"}
  ]
  ```

#### 2. `pokecode/cache.py` (キャッシング機構)

**クラス定義：**

##### `TranslationCache`
- 翻訳結果をJSONファイル（`.cache/translations.json`）に永続化
- `get(key: str) -> str | None`: キャッシュから取得
- `set(key: str, value: str) -> None`: キャッシュに保存
- `load()`: ファイルからロード
- `save()`: ファイルに保存

**キャッシュファイル形式：**
```json
{
  "Afghanistan": "アフガニスタン",
  "Albania": "アルバニア",
  ...
}
```

### OpenAI API呼び出し仕様

**モデル**: `gpt-3.5-turbo` または `gpt-4`

**プロンプト設計：**
```
You are a professional translator specializing in geography and place names.
Translate the following English country names to Japanese.
Return ONLY the Japanese translation, nothing else.

[国名のリスト（改行区切り）]
```

**バッチサイズ**: 1リクエストで最大10国名（API制限を考慮）

### エラーハンドリング

- OpenAI APIの接続エラー → 例外を発生させ、ログに記録
- API認証失敗 → 設定エラーメッセージ
- キャッシュ操作エラー → ロギング、継続
- タイムアウト → リトライ機構（最大3回）

### 環境変数

**必須：**
- `OPENAI_API_KEY`: OpenAI APIキー

**オプション：**
- `OPENAI_MODEL`: 使用モデル（デフォルト: `gpt-3.5-turbo`）
- `OPENAI_REQUEST_TIMEOUT`: タイムアウト秒数（デフォルト: 30）

### 統合ポイント

#### `main.py`での使用例
```python
from pokecode.translation import translate_countries_batch

# 既存のコード...
countires_without_extra_chars = [...]

# 日本語翻訳を追加
countries_with_ja = translate_countries_batch(countires_without_extra_chars)

# JSON保存
save_json(countries_with_ja, output_file)
```

### 実装スケジュール

1. **Phase 1**: `cache.py` - キャッシング機構の実装
2. **Phase 2**: `translation.py` - OpenAI API統合と翻訳関数の実装
3. **Phase 3**: `main.py` への統合
4. **Phase 4**: テストとドキュメント整備

### 考慮事項

- **コスト最適化**: キャッシュにより、同じ国名の再翻訳を避ける
- **スケーラビリティ**: バッチ処理により複数国の効率的な翻訳が可能
- **信頼性**: 既知の国名の翻訳結果を事前定義したデフォルト辞書で補助
- **ロギング**: 翻訳プロセスの可視化
