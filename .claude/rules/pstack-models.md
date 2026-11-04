# pstackのロールごとのモデル設定。1行に1ロール。行を消すとskillの既定値に戻る。
# 値が`inherit-parent`か`auto`のロールは、親チャットのモデルで動く（Taskの`model`を省略する）。panelのリストでは、これらの値も1体として数える。
# budget: inherit-parent（セッションの/effortに従う）
feature, refactoring: inherit-parent
bug-fix: inherit-parent
perf-issue: inherit-parent
hillclimb: inherit-parent
judgment and prose: inherit-parent
hardest tasks: inherit-parent
how explorer: inherit-parent
how explainer: inherit-parent
why investigators: inherit-parent
why synthesizer: inherit-parent
reflect tooling: inherit-parent
reflect judgment, divergent, synthesizer: inherit-parent
arena runners: inherit-parent, inherit-parent
swarm workers: inherit-parent
architect runners: inherit-parent, inherit-parent
interrogate reviewers: inherit-parent, inherit-parent
