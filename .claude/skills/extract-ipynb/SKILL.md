---
name: extract-ipynb
description: ipynb のコードセルだけを .py ファイルに抽出する。ノートブックから Python コードを取り出したい・スクリプト化したいときに使う。
---

# ipynb からの Python コード抽出

## 手順

1. 専用スクリプト `scripts/extract_ipynb_code.py` を使う（標準ライブラリのみ、依存なし）:

   ```bash
   # 出力先を省略すると /tmp/<ノートブック名>.py に書き出す
   python3 scripts/extract_ipynb_code.py <notebook.ipynb> [output.py]
   ```

   例（document/tmp に抽出する場合）:

   ```bash
   mkdir -p document/tmp
   python3 scripts/extract_ipynb_code.py document/day2-tutorial.ipynb document/tmp/day2-tutorial.py
   ```

   出力先ディレクトリは自動作成されないので、必要なら先に `mkdir -p` する。

2. 抽出後、正しい Python になっているか検証する:

   ```bash
   python3 -m py_compile <output.py>
   ```

## スクリプトの仕様

- `cell_type == "code"` のセルのみ抽出（Markdown セルは除外、空セルもスキップ）
- 各セルの先頭に `# %% [cell N]` の区切りコメントを付ける（元のセル番号が追える。VS Code はこれをセル区切りとして認識する）
- Jupyter マジック（`%...`）とシェル行（`!...`）はコメントアウトして残す — そのままでは Python として不正なため

## 注意

- リポジトリのノートブックは `document/` 配下にある
- `document/tmp/` は git 未追跡。コミットに含めたくなければ `.gitignore` に追加する
