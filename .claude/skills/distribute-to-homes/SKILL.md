---
name: distribute-to-homes
description: 既にログイン済みの TLJH 参加者のホームに、指定したファイルまたはディレクトリを配る。「全員のホームに教材を置く」「参加者全員に配布」「day1 を全ホームに配る」「tester にだけ配る」ときに使う。編集済みファイルは壊さない（同名はスキップ）。
---

# 教材を既存ホームに配る

既にログイン済みの参加者のホームに、ファイル or ディレクトリを配布する。
`/etc/skel`（新規ログイン者向け）は触らず、既に存在するホームだけに配る。

## いつ使うか

- 既にログインして作業を始めた参加者全員に教材を届けたい
- `day1/` のように**ディレクトリごと**配りたい
- 対象を絞りたい（例: tester だけ）

（まだログインしていない参加者へは skel 経由。`place-in-skel` スキルを使う）

## 手順

`infra-setup/11_distribute_to_homes.sh` を実行する:

```
bash infra-setup/11_distribute_to_homes.sh <ローカルのパス> [ユーザーglob]
```

- 全ホームに配る: `bash infra-setup/11_distribute_to_homes.sh document/day1`
- tester だけに配る: `bash infra-setup/11_distribute_to_homes.sh document/day1 'jupyter-tester-*'`
- 参加者だけ（tester 除外）に配りたい等、glob で絞れる
- 配布元は**このローカルマシンの git ファイル**

## 注意

- **同名が既にある人はスキップ**する（編集内容を壊さない・冪等）。
  更新版を配りたいときは別名にする（例: day1-v2/）
- ログイン済みホームのみが対象。未ログインの人へは `place-in-skel` を使う
- 配る前にローカルが最新か確認（`git pull` で main を最新化してから）
- 全員 + 新規ログイン者の両方に配りたいなら、`place-in-skel`（skel）と
  このスキル（既存ホーム）を両方実行する
