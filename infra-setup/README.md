# infra-setup — イベント用インフラ構築スクリプト

FXトレーディング演習の実行環境（app/DB VM + TLJH VM の2台構成）を構築・運用するスクリプト集。
1ファイル = 1タスク。共通設定は `config.sh` にまとまっており、各スクリプトが source する。

```
参加者のブラウザ ×50   ──▶   TLJH VM (fx-tljh)      ──▶   app/DB VM (fx-trade-api-ssd)
                       HTTP   e2-highmem-8          内部NW   FastAPI + Postgres (docker compose)
                              Jupyter環境 ×50人分   0.1〜0.5ms
```

## 実行順序

| # | ファイル | やること | いつ実行するか |
|---|---|---|---|
| - | `config.sh` | 共通設定（プロジェクト/ゾーン/VM名/サイズ） | 実行しない（source される） |
| 1 | `01_appdb_resize_disk.sh` | app/DB VM のディスクを 10GB→50GB に拡張 | イベント前に1回 |
| 2 | `02_appdb_change_db_password.sh <新パスワード>` | Postgres パスワードを初期値から変更 | イベント前に1回 |
| 3 | `03_tljh_create_vm.sh` | TLJH VM を作成（静的IP・ファイアウォール込み） | イベント前に1回 |
| 4 | `04_tljh_provision.sh` | TLJH の自動プロビジョニング | 直接実行しない（VM 起動時に自動実行) |
| 5 | `08_create_users.sh users/testers.txt` | ID リストのユーザーを Hub に事前登録（何度実行しても安全） | テスター/参加者 ID 確定時 |
| 6 | `07_distribute_notebook.sh <file>` | ノートブックを /etc/skel + 全ホームに配布 | 初回配布時と、Day 2 の教材配布時 |
| 7 | `05_verify.sh` | 疎通・レイテンシの検証 | 上記完了後、およびイベント当日朝 |
| 8 | `06_truncate_balances.sh` | balances テーブルの掃除 | Day 1 と Day 2 の間 |

**運営の時系列手順（ユーザー登録→配布→当日対応→片付け）は `運営手順.md` を参照。**

## リハーサル → 本番の流れ

1. `07_distribute_notebook.sh document/tutorial.ipynb`（Day 1）と `document/colab_template.ipynb`（Day 2）で教材配布 → 運営がリハーサル用ID
   （例: `rehearsal-*`）でログインしてリハーサル実施
2. リハーサルユーザーの掃除（任意）: VM 上で `sudo userdel -r jupyter-rehearsal-<id>` + TLJH 管理画面から削除
3. ノートブックを更新したら再度 `07_distribute_notebook.sh`（/etc/skel も更新されるため、
   その後に初回ログインする本番ユーザーには自動で最新版が入る。
   本番は参加者に事前配布したIDで初回ログインしてもらう）
4. Day 2 教材（`colab_template.ipynb`）は Day 1 と同時に配布済み。差し替えが必要なら別ファイル名で 07 を実行（既存ホームにもそのまま入る）

注意: 07 は既存ホームの同名ファイルを**絶対に上書きしない**（上書きオプションは事故防止のため無い）。
内容を更新して配り直すときは別のファイル名にする（例: `tutorial-v2.ipynb`）。

ID リストは `users/` 配下（`testers.txt` = tester-1〜8、2026-08-29 作成）。08 で登録した ID は Admin パネルに
表示されるが、**Linux ユーザーとホームディレクトリは本人の初回ログイン時に作られる**（パスワードもその時に確定）。

ログインできるのは **08 で登録済みの ID だけ**（TLJH は `FirstUseAuthenticator.create_users=False` が既定。
未登録 ID は "Invalid username or password" で弾かれる）。パスワードは初回ログイン時に本人が決める（**7 文字以上**）。

## 前提

- gcloud CLI 認証済み、プロジェクト `fx-itnern` を使用（`kinetic-dream-319407` は使用禁止）
- app/DB VM（`fx-trade-api-ssd`）は構築済みで、`/home/ky2001/fxtrade-api` の docker compose で稼働中
- アプリ側の対応（uvicorn `--workers 8`、DBプール設定）はコード側で別途行う

## 04_tljh_provision.sh が設定するもの

- TLJH 本体 + 管理者ユーザー（初回ログイン時のパスワードがそのまま登録される方式）
- ユーザー毎リソース上限: メモリ 1GB / CPU 1コア（cgroup 強制）、ディスク 2GB（usrquota + cron）
- 全ユーザーへの環境変数 `FX_API_BASE_URL`（app VM の内部IP）
- 参加者用パッケージ: requests / numpy / pandas / matplotlib / tqdm

## 背景資料

- 構成の意図と懸念の整理: `../document/TLJH説明.md`
- 03 / 04 のステップごとの解説（usrquota・cgroup・startup-script などの用語含む）: `03_04_解説.md`
