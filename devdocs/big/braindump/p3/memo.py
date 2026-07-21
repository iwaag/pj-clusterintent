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

対応状況（完了）
----------------
根本原因（接続先アイデンティティのみに基づく SSH known_hosts と、
DesiredNode の恒久的な身元との不整合）は
``devdocs/small/fix_sshkey/plan.md`` の一連の変更で解消済み。
``nctl-node-<DesiredNode UUID>`` を唯一の ``HostKeyAlias`` とし、
bootstrap/production 両インベントリが同一のエイリアス・
``ansible_ssh_common_args`` を持つようになったため、``ansible_host`` が
``agdnsmasq.local`` から ``192.168.0.2`` に変わっても再 enroll 不要かつ
同じ鍵で認証される。実装詳細・各ステップの報告は
``devdocs/small/fix_sshkey/report_step1.md`` 〜 ``report_step6.md``、
実機での再現検証（``agdnsmasq`` に対する enroll・bootstrap/production
両経路での接続・reconcile 実行）は
``devdocs/small/fix_sshkey/report_verification.md`` を参照。

禁止事項（引き続き有効）
------------------------
* ``StrictHostKeyChecking=no``、グローバルな ``accept-new``、host key 検証の
  無効化を恒久対策にしない。
* 広範囲な known_hosts 削除や、照合なしの鍵置換をしない。
（上記は修正後も設計原則として維持されており、コード・テストのいずれにも
現れない。）

補足
----
agpc observation 時の become password 引継ぎは別件であり、nctl commit
3f65248 により修正済み。この SSH host key の申し送りは、その修正の再発ではない。
"""
