# Step 4 Implementation Report

## Summary

Step 4 の pure range classification helper を実装した。

実装対象:

- `nintent/nautobot_intent_catalog/evaluations.py`
- `nintent/nautobot_intent_catalog/tests/test_evaluations.py`

今回の変更は Nautobot/Django ORM に依存しない。`DesiredIPRange` 風の
任意オブジェクトと endpoint IP 文字列を受け取り、Python 標準の
`ipaddress` で正規化、包含判定、不正 range 検出、重複検出を行う。

## Added Helpers

`evaluations.py` に以下を追加した。

- `normalize_endpoint_ip_string(value)`
  - endpoint IP を host address 文字列へ正規化する。
  - CIDR suffix 付きの値は host 部分へ正規化する。
  - 不正値は空文字を返す。

- `normalize_desired_range_addresses(ip_range)`
  - `start_address` / `end_address` を host address に正規化する。
  - `missing_start_address`
  - `missing_end_address`
  - `invalid_start_address`
  - `invalid_end_address`
  - `address_family_mismatch`
  - `range_start_after_end`
  を deterministic な error code として返す。

- `desired_ip_range_facts(ip_range)`
  - plan.md の推奨 facts に沿って、range facts を serializable dict にする。
  - 不正 range の場合は `valid: false` と `errors` を付与する。

- `matching_desired_ip_ranges(endpoint_ip, range_candidates)`
  - endpoint IP を含む valid range facts を deterministic order で返す。

- `invalid_desired_ip_ranges(range_candidates)`
  - invalid range facts を deterministic order で返す。

- `overlapping_desired_ip_ranges(range_candidates)`
  - valid range 同士の重複を検出し、重複区間を facts として返す。

- `classify_endpoint_ip_ranges(endpoint_ip, range_candidates)`
  - endpoint IP の正規化結果
  - matching ranges
  - invalid ranges
  - all overlapping ranges
  - overlapping matching ranges
  をまとめて返す。

内部実装として `NormalizedIPRange` dataclass と `_strict_host_address()` を追加した。
既存の `_host_address()` は互換的で lenient な挙動を保つため変更していない。

## Tests

`test_evaluations.py` に `IPRangeClassificationTests` を追加した。

カバーした内容:

- endpoint IP と range start/end の host address 正規化
- IPv4 range containment
- matching ranges の deterministic sort
- invalid endpoint IP が例外を出さないこと
- invalid range definitions の deterministic error reporting
- overlapping matching ranges の検出

実行結果:

```bash
cd nintent && python3 -m unittest nautobot_intent_catalog.tests.test_evaluations
```

結果:

```text
Ran 26 tests in 0.001s
OK
```

README_DEV のローカルテスト方針に沿って全体も確認した。

```bash
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
```

結果:

```text
Ran 76 tests in 0.006s
OK
```

## README_DEV Consistency

README_DEV の注意点と矛盾しない。

- Nautobot/Django なしで動く pure helper と unit tests にしている。
- `IPAddress.objects.order_by("address")` のような ORM access は追加していない。
- `IPAddress.address` のような display property 前提を range helper に広げていない。
- 既存の Nautobot actual object conversion boundary は維持している。
- 旧 plugin 名、旧 setting key、旧 import path、旧 URL alias は追加していない。

## Notes For Step 5

Step 5 では `evaluate_endpoint_intent()` に `range_candidates` を渡し、
`classify_endpoint_ip_ranges()` の結果を `observed_facts` と gap 判定に接続できる。

接続時の注意:

- `ip_policy` を `_expected_endpoint_facts()` に追加する。
- invalid endpoint IP は評価を crash させず、range/policy gap に変換する。
- `dhcp_reservation_ready` は `ip_policy=dhcp_reserved` かつ range/policy の blocking gap がない場合だけ true にする。
- `DesiredIPRange` queryset を使う場合も ORM で IP address 文字列を数値比較しない。DB から取得後、今回の pure helper に渡して判定する。
