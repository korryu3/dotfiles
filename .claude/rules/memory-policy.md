---
description: メモリに変化するものを書かない（不変層原則）
---

# メモリ運用ポリシー

- メモリに書いてよいのは3種だけ。働き方のfeedback（Whyを添える）、コードや公式ドキュメントから読めない環境の罠、不変のポインタ（`type: reference`）
- タスクの状態・設計判断・実装の固有名詞・CLAUDE.mdやrulesに既にある内容は書かない。タスク文脈は`~/.claude/context/<PROJECT_ID>/notes/`へ
- 判断が覆ったら同じターンでメモリを直す。安定した知見は`メモリ → CLAUDE.md / rules → linter / hook`の順に昇格させ、昇格したらメモリから消す
- `notes/active-tasks.md`は現在の状態だけを書き換えて保つ。押し出された記述は`active-tasks-history.md`へ逐語で移す
- SessionStart hookがメモリの違反を警告したら、勝手に棚卸しを始めず、AskUserQuestionで直すかどうかを確認する
