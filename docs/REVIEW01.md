# REVIEW01: pokecode ロギング設計レビュー（CLI 側）

## 対象コード

- src/pokecode/logconfig.py
- src/pokecode/main.py
- src/pokecode/loading.py
- src/pokecode/request.py

## 全体方針（要約）

- **アプリケーション単位で 1 回だけロギングを初期化する**
- **情報は logger.info を中心に、必要最低限のイベントだけを記録する**
- **ハンドラーの重複追加を避け、同じメッセージが多重ログされないようにする**
- **モジュール側は「どこに出すか」ではなく「何を記録するか」だけを意識する**

---

## logconfig.setup_logging の設計

```python
# src/pokecode/logconfig.py

import logging
import sys
from logging import Logger, StreamHandler


def setup_logging(logger: Logger, *, level: str = "INFO") -> None:
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(resolved_level)

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    target_stream = sys.stderr
    stream_handler = None

    for h in logger.handlers:
        if isinstance(h, StreamHandler) and getattr(h, "stream", None) is target_stream:
            stream_handler = h
            break

    if stream_handler is None:
        stream_handler = StreamHandler(target_stream)
        logger.addHandler(stream_handler)

    stream_handler.setFormatter(formatter)

    logger.propagate = False
```

### 役割

- 呼び出し元から渡された `logger`（例: `logging.getLogger("pokecode")`）に対して、以下を行う:
  - ログレベルの設定
  - `sys.stderr` 向け `StreamHandler` を **1 個だけ** 確保
  - 共通フォーマッタの設定
  - `logger.propagate = False` により、root ロガーへの伝播を防止

### 重複ログを避けるポイント

- `for h in logger.handlers:` で既存の `StreamHandler` を探索し、
  - すでに `sys.stderr` 向けの `StreamHandler` があれば **再利用**
  - なければ新規作成して追加
- これにより、同じロガーに対して `setup_logging()` を複数回呼んでも、
  - **ハンドラーが際限なく増えていくことはない**
  - 同一メッセージが複数回出力されることを防げる

---

## main.py での初期化戦略

```python
# src/pokecode/main.py

import logging

from pokecode.request import requests_json
from pokecode.logconfig import setup_logging
from pokecode.loading import load_config
from pokecode.config import PYPROJECT


def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger, level="INFO")

    logger.info("Application Start.")

    data = load_config(PYPROJECT)
    url = data["tool"]["pokecode"]["local"]

    msg = requests_json(url)
    logger.info("Response payload: %s", msg)

    logger.info("Application End.")
```

### 方針

- アプリケーションのエントリポイントである `main()` の冒頭で、
  - `logging.getLogger("pokecode")` を取得
  - `setup_logging(logger, level="INFO")` を **1 回だけ** 呼ぶ
- 以降のコードは、
  - 「アプリ開始」「設定ロード」「HTTP リクエスト」「アプリ終了」といった
    ライフサイクルイベントを `logger.info` で記録

### ログメッセージの重複について

- `main()` 自身はシンプルに 3 箇所だけ info ログを出している:
  - `Application Start.`
  - `Response payload: ...`
  - `Application End.`
- これとは別に、`loading` / `request` モジュールがそれぞれ自分の責務に応じたログを出す。
- 「アプリ全体の大きな節目」と「各機能の詳細ログ」をレイヤー分けしており、
  - 同じ内容を 2 回以上言わない（重複メッセージを避ける）
  - しかし、流れは上から下まで追える、というバランスになっている。

---

## loading.load_config の設計

```python
# src/pokecode/loading.py

import logging
import tomllib
from pathlib import Path

from pokecode.config import PYPROJECT

logger = logging.getLogger(__name__)


def load_config(pyproject_path: Path = PYPROJECT) -> dict:
    logger.info("Loading config: %s", pyproject_path)

    if not pyproject_path.exists():
        logger.error("Config file not found: %s", pyproject_path)
        raise FileNotFoundError("'pyproject.toml'が発見不可。")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    logger.info("Config loaded successfully")
    return data
```

### ポイント

- `logger = logging.getLogger(__name__)` により、ロガー名は `"pokecode.loading"` になる。
  - 親ロガーは `"pokecode"` であり、`main.py` で設定したハンドラー構成を再利用できる。
- ログメッセージは **関心ごとに限定**:
  - 設定ファイルをどのパスから読み込むか
  - 見つからなかった場合のエラー
  - 正常に読み込めたことの確認
- 成功ケースでのログは 2 行だけであり、冗長になりすぎない。

### 重複回避の観点

- `main()` では単に `load_config()` を呼び出すだけで、細かいログはここに集中させる。
- `main` 側で「設定読み込み開始」「設定読み込み完了」などを **二重に出さない** ことで、
  - 読み手にとって「どこで何が起きたか」が明瞭
  - かつ、同じ情報を読むコストが増えない。

---

## request.requests_json の設計

```python
# src/pokecode/request.py

import logging
import requests
from requests import Response

logger = logging.getLogger(__name__)


def requests_json(url: str) -> dict | list:
    logger.info("Request start: %s", url)

    res: Response = requests.get(url)
    res.raise_for_status()

    try:
        data = res.json()
    except ValueError as e:
        ct = res.headers.get("Content-Type")
        logger.error("JSON parse failed. content-type=%s", ct)
        raise RuntimeError(f"JSON parse failed. content-type={ct}") from e

    logger.info("Request success: type=%s", type(data).__name__)

    if isinstance(data, dict):
        logger.info("json is dict.")
        return data
    if isinstance(data, list):
        logger.info("json is list.")
        return data

    raise RuntimeError("JSON is invalid.")
```

### ポイント

- ここでも `logger = logging.getLogger(__name__)` を採用し、ロガー名は `"pokecode.request"`。
  - 親ロガー `"pokecode"` が stderr ハンドラーを持っているので、
    追加のハンドラーは不要。
- ログのタイミング:
  - リクエスト開始（URL）
  - ステータスコードの検証後、JSON 変換成功時の型
  - JSON が dict / list どちらかのブランチ
  - JSON パース失敗時のエラー（content-type を含めて記録）

### 重複を避けながら情報量を確保

- `main()` 側ではレスポンスのペイロード全体を 1 回だけ info で記録し、
  - `requests_json()` 側では「リクエストのライフサイクルと型情報」に集中。
- 「どの URL に投げたか」「どんな JSON が返ってきたか」「パースに失敗したか」といった観点が、
  - それぞれ 1 回ずつ、役割分担された形で記録されている。

---

## ロギング階層と伝播の整理

### ロガー階層

- `main.py` : `logging.getLogger("pokecode")`
- `loading.py` : `logging.getLogger("pokecode.loading")`
- `request.py` : `logging.getLogger("pokecode.request")`

Python ロギングでは、ドット区切りのロガー名により以下のような階層になる:

- 親ロガー: `"pokecode"`
- 子ロガー: `"pokecode.loading"`, `"pokecode.request"`

### 伝播の動作

- 子ロガーは、ハンドラーを持たない場合、親ロガーへメッセージを伝播する。
- 今回の設計では:
  - 親ロガー `"pokecode"` にだけ `StreamHandler(sys.stderr)` を付与
  - 各モジュールロガーはハンドラーを持たず、親に任せる

結果として:

- ハンドラーは 1 本（stderr 向け）だけ
- どのモジュールから出たログも、同じフォーマット・同じ出力先に集約
- handler の重複追加が抑制され、同じメッセージが多重に出力されるリスクが低い

---

## この設計のトレードオフ

### 良い点

- アプリ単位で 1 箇所（main）だけがロギング構成を知っていればよい
- 各モジュールは「自分の責務に関する情報だけ」を logger.info で出せばよい
- ハンドラーの重複やグローバルフラグ管理のような複雑さがない
- ログレベル変更は `setup_logging(logger, level=...)` の引数で一元的に制御可能

### 注意点 / 今後の拡張余地

- もし将来、ファイル出力や JSON ログなど出力先を増やしたい場合は、
  - `setup_logging()` 内でハンドラーを追加し、
  - それでも「同じロガーに同種ハンドラーを複数ぶら下げない」ポリシーを徹底する必要がある。
- サーバ側（server/app.py）とはロガー構成をどう共有するか、
  - 「CLI 用ロガー」と「サーバ用ロガー」を分けるのか
  - あるいは共通の親ロガーにぶら下げるのか
  - といった設計を別途レビューする余地がある。

---

## まとめ

- `setup_logging()` は「どのロガーに、どんなハンドラーを 1 回だけ付けるか」を責務とする。
- `main()` はアプリケーション全体のライフサイクルイベントのみを info で記録する。
- `loading` / `request` などのモジュールは、自分のドメインに関する詳細ログのみを info で記録する。
- ロガー階層と伝播を活用することで、
  - ハンドラー構成はシンプルに 1 箇所へ集約
  - 情報は過不足なく、かつ重複を避けた形でログに残す。

この REVIEW01 は、現時点の CLI 側ロギング設計のスナップショットであり、
将来的にファイル出力や構造化ログを導入する際の基準点として参照できるようにすることを目的とする。
