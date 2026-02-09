# Mypy型スタブのインストール

## 問題

Mypyで以下のような警告が出る場合：

```
Library stubs not installed for "requests"
Hint: "python3 -m pip install types-requests"
```

## 原因

`requests` ライブラリには元々型ヒント（type hints）が含まれていません。Mypyが型チェックを行うには、別途**型スタブ（type stubs）**ファイルが必要です。

### 型スタブとは

- 外部ライブラリの型情報を提供する `.pyi` ファイル
- 元のライブラリコードを変更せずに型情報を追加できる
- Mypyがコードの型安全性を検証するために必要

## 解決方法

### 特定のライブラリの型スタブをインストール

```bash
python3 -m pip install types-requests
```

### すべての不足している型スタブを自動インストール

```bash
mypy --install-types
```

このコマンドは、プロジェクト内で使用されているすべてのライブラリの型スタブを自動的に検出してインストールします。

## 型スタブをインストールする利点

1. **型チェックの精度向上**
   - `Response` オブジェクトのメソッド（`.raise_for_status()`, `.text`, `.headers` など）の戻り値の型が正確に推論される
   - 型エラーを事前に検出できる

2. **IDEサポートの向上**
   - コード補完がより正確になる
   - 関数のシグネチャが表示される
   - リファクタリングが安全になる

3. **実行時エラーの防止**
   - 型の不一致を事前に検出
   - バグの早期発見につながる

## よく使われる型スタブパッケージ

- `types-requests` - requests ライブラリ用
- `types-beautifulsoup4` - BeautifulSoup4 用
- `types-PyYAML` - PyYAML 用
- `types-setuptools` - setuptools 用

## 参考リンク

- [Mypy公式ドキュメント - Missing imports](https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports)
- [typeshed リポジトリ](https://github.com/python/typeshed) - Python標準ライブラリとサードパーティライブラリの型スタブコレクション
