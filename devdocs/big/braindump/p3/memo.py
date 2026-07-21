"""Phase 3 申し送り: agdnsmasq の SSH 接続先と host key の整合性。

状況
----
2026-07-21 の reconcile operation 01KY2NZR048X0GKWYBN4DVENW5 では、
agdnsmasq の observation と IPAM reconcile は成功した。一方、dnsmasq の
設定タスクは production inventory 経由で SSH 接続した際、"Host key
verification failed" となり未実行で終わった。

確認済みの事実
--------------
* bootstrap observation inventory では ``agdnsmasq.local`` を使い、接続できる。
* production inventory では同じノードの ``ansible_host`` が ``192.168.0.2`` に
  解決される。
* production inventory を使う ``ansible -m ping`` は host key verification
  failure で到達不能になる。
* これは desired state / actual-state ingest / dnsmasq service target の問題では
  なく、接続アイデンティティ（名前と IP）に対する SSH known_hosts の不整合である。

次回の安全な進め方
------------------
1. 信頼できる既知のフィンガープリントと照合して、``agdnsmasq.local`` と
   ``192.168.0.2`` が同一ホストの正しい host key を提示することを確認する。
   未検証の ``ssh-keyscan`` 出力をそのまま信頼しない。
2. 接続先を一意に決める。確認済みの IP 用 known_hosts エントリを追加するか、
   production inventory 側も検証済みのホスト名を使うようにする。
3. 明示的な承認を得てから plan-only reconcile を再実行し、結果を確認した上で
   apply する。

禁止事項
--------
* ``StrictHostKeyChecking=no``、グローバルな ``accept-new``、host key 検証の
  無効化を恒久対策にしない。
* 広範囲な known_hosts 削除や、照合なしの鍵置換をしない。

補足
----
agpc observation 時の become password 引継ぎは別件であり、nctl commit
3f65248 により修正済み。この SSH host key の申し送りは、その修正の再発ではない。
"""
