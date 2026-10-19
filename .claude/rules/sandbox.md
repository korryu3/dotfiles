---
description: sandbox内でコマンドが落ちるときの既知の原因
---

# sandboxの環境の罠

- `excludedCommands`（`git *`・`uv *`・`yarn *`・`docker *`）は単体の形のコマンドにしか効かない。パイプ・`&&`・リダイレクト・`git -C`などを付けるとsandbox内で動き、`.git`への書き込みが拒否されて`Operation not permitted`で落ちる。単体で打ち、出力はツール側のオプションで絞る。別ディレクトリで打つときは`cd`を単独の呼び出しで先に打つ
- Node製のCLIの通信が`fetch failed`になったら`NODE_USE_ENV_PROXY=1`を付ける（Nodeの組み込みfetchは既定でsandboxのプロキシを読まない）。起動時に`SecItemCopyMatching failed`で落ちたら`NODE_USE_SYSTEM_CA=0`を付ける
- pythonのimport時に`ssl.py`の`load_verify_locations`で`PermissionError`が出たら（pytestの収集エラーなど）、`SSL_CERT_FILE=/private/etc/ssl/cert.pem REQUESTS_CA_BUNDLE=/private/etc/ssl/cert.pem`を付ける（certifiの証明書がsandboxの読み取り許可に無い）
- sandbox内の計測はターミナルより2倍以上遅い。絶対値ではなく比率で読み、ターミナルと比べるときは同じworktree・同じvenv・同時実行なしで条件をそろえる。新しいvenvの初回はさらに遅いので比較に使わない
