---
name: creating-plan
description: 実装前のPlan作成と反復レビューを行うオーケストレーションフローを実行する。ユーザーが実装を依頼した場合や、複雑なタスクに取り組む前に使用する。
allowed-tools: Read, Grep, Glob, Write, Agent, AskUserQuestion, Bash(~/.claude/scripts/project-id.sh)
---

## 前提

- plan-creator agent: Plan作成
- plan-reviewer agent: レビュー（観点はプロンプトで指定）
- PROJECT_ID: `~/.claude/scripts/project-id.sh` を実行して取得する（例: `/Users/foo/bar` → `-Users-foo-bar`）。取得できない場合は `default` を使用
- Plan出力先: `~/.claude/context/<PROJECT_ID>/plans/<plan-name>/`

## 進行チェックリスト

以下をコピーして進行状況を追跡する:

```
Plan作成進捗:
- [ ] Step 1: plan-creator 起動
- [ ] Step 2: 不確実リストの確認
- [ ] Step 2.5: 不確実リストの深掘り調査（該当時のみ）
- [ ] Step 3: 規模判定によるフロー分岐
- [ ] Step 4: 洗い出し - reviewer並列起動（ラウンド 1/{max}）
- [ ] Step 5: 精査 - トリアージ（必要に応じて調査）
- [ ] Step 6: 収束判定
- [ ] Step 7: Plan修正 → Step 4に戻る（必要な場合のみ）
- [ ] Step 8: ユーザーに提示
```

## フロー

### Step 1: plan-creator 起動

plan-creator agent を起動し、以下を渡す:
- ユーザーのタスク内容（$ARGUMENTS またはこれまでの会話から）
- Plan名（タスク内容から適切な kebab-case 名を決定）

フロー開始時に `~/.claude/scripts/project-id.sh` を実行して PROJECT_ID を取得する。
plan-creator には Plan出力先の完全なパス `~/.claude/context/<PROJECT_ID>/plans/<plan-name>/` を渡す。
plan-creator は plan.md、規模判定、不確実リスト、前提条件を返す。

### Step 2: 不確実リストの確認

**不確実リストが「なし」?** → Step 3 へ進む
**不確実リストがある?** → Step 2.5 へ進む

### Step 2.5: 不確実リストの深掘り調査

不確実リストの各項目について、Explore エージェント等を使って追加調査を行う。
調査しても解消できなかった項目のみユーザーに提示し確認を求める。

調査結果により Plan の修正が必要な場合のみ、調査結果（解消できた項目 + ユーザーの回答）をまとめて plan-creator を再起動し、Plan を更新させる。修正不要ならそのまま Step 3 へ進む。

### Step 3: 規模に応じたフロー分岐

**small?** → Step 4 へ進む（最大2ラウンド）
**medium?** → Step 4 へ進む（最大5ラウンド。オプション観点から最低1つを選んで追加起動すること）
**large?** → Step 4 へ進む（最大10ラウンド。オプション観点から最低2つを選んで追加起動すること。影響範囲が大きいため、多角的にレビューして見落としを減らす）

### Step 4: 洗い出し - reviewer並列起動

`reviews/round-{N}/` ディレクトリを作成する。

plan-reviewer agentを並列起動する。各reviewerにStep 1で取得したPlan出力先ディレクトリ、ユーザーの元の要求、現在のラウンド番号を渡す。
reviewerはseverity判定なしで気になった点をすべて列挙する。出力先: `reviews/round-{N}/`

**コア観点（必ず起動）**:
- **戦略reviewer**: アプローチの妥当性 + スコープの妥当性
- **実装reviewer**: 既存コードとの整合性 + 実装順序と依存関係

**オプション観点（Planの内容に応じて追加起動）**:
- リスク（選んだアプローチが本番環境で失敗するシナリオ）
- 破壊的変更・後方互換性
- パフォーマンス影響
- セキュリティ
- その他、Plan の内容から必要と判断した観点

オプション観点がある場合は、該当観点ごとに reviewer を追加起動する。
ユーザーが追加の観点を指示した場合も、該当観点で reviewer を起動する。

### Step 5: 精査 - トリアージ（必要に応じて調査）

reviewer が書き出した `reviews/round-{N}/` 配下の全指摘を読み、各指摘にステータスを付与する:
※ 判断に情報が足りない指摘がある場合は、Explore等を並列起動して調査した上で判定する

- **adopted**: 採用
- **rejected**: 棄却（理由を記録）
- **deferred**: ユーザーに判断を仰ぐ
- **partial**: 部分的に採用

**deferredがある?** → ユーザーに提示し判断を求める。回答に基づきdeferredをadoptedまたはrejectedに更新してからStep 6へ進む

#### トリアージ結果の記録

`reviews/round-{N}/triage.md` にトリアージ結果を記録する。

### Step 6: 収束判定

**最大ラウンド数に達した?** → Step 8 へ（未解決の指摘をユーザーに報告）
**adopted / partial がゼロ?**（指摘なし or すべて rejected） → Step 8 へ
**adopted / partial がある?**（severity 問わず） → Step 7 へ

### Step 7: Plan修正 → Step 4に戻る

plan-creatorを再起動し、Plan出力先ディレクトリ、ユーザーの元の要求、adopted/partialの指摘内容を渡す。
修正完了後、Step 4に戻って再度洗い出しから行う。（再レビュー時もreviewerは全体を一から見直すため、前ラウンドのreviews/round-{N-1}/配下のファイルはreviewerに渡さない）。

再レビュー時のレビュー範囲は前ラウンドのトリアージ結果で判定する:
- adopted/partialにcriticalまたはmajorが1つ以上含まれる場合: Step 3の規模に応じてオプション観点も選定し直して再起動
- adopted/partialがすべてminorの場合: コア観点のみで再起動

**Planを修正したら、必ずStep 4に戻って再度洗い出しを行うこと。修正後にレビューを経ずにStep 8へ進んではならない。**

### Step 8: ユーザーに提示

最終的な plan.md の内容とファイルパスをユーザーに提示する。レビューで論点があった場合はその対応サマリーも添える。
ユーザーの承認を得てからフローを終了する。

## 注意事項

- 各ラウンドの冒頭で「現在 N/{最大ラウンド数} ラウンド目」と明記すること
