# Step 5 Implementation Report

## Summary

Step 5 の endpoint evaluation 拡張を実装した。

実装対象:

- `nintent/nautobot_intent_catalog/evaluations.py`
- `nintent/nautobot_intent_catalog/jobs.py`
- `nintent/nautobot_intent_catalog/tests/test_evaluations.py`

Step 4 で追加した pure range classification helper を
`evaluate_endpoint_intent()` に接続し、endpoint の `ip_policy` と
matching `DesiredIPRange.range_policy` の整合性を評価できるようにした。

## Evaluation Changes

`evaluate_endpoint_intent()` に `range_candidates` 引数を追加した。

- `range_candidates=None`
  - 従来互換のため range-aware 判定を無効にする。
- `range_candidates` に iterable を渡した場合
  - endpoint IP を desired range に分類する。
  - `observed_facts.ip_policy_range_classification` に分類結果を保存する。
  - `observed_facts.matching_ip_policy_ranges` に matching range facts を保存する。
  - range/policy mismatch を gap に変換する。

`_expected_endpoint_facts()` に `ip_policy` を追加した。

追加・接続した gap code:

- `missing_ip_policy_range`
- `ambiguous_ip_policy_range`
- `ip_policy_range_mismatch`
- `invalid_ip_policy_range`
- `static_endpoint_in_dhcp_pool`
- `dhcp_reserved_endpoint_in_dynamic_pool`

`dhcp_reservation_ready` の条件を更新した。

- `ip_policy=dhcp_reserved` が必須。
- endpoint IP が必要。
- MAC candidate が一意であることが必要。
- interface gap、range gap、policy gap、conflict がある場合は false。
- `static` と `external` は MAC candidate があっても DHCP-ready にならない。

`_wants_dhcp_material()` も `ip_policy=dhcp_reserved` の endpoint だけが
DHCP MAC evaluation を要求するように変更した。

## Job Changes

`EvaluateEndpointIntent` Job で `DesiredIPRange` を読み込むようにした。

- `deprecated` / `retired` range は除外する。
- `planned` / `approved` / `active` range は候補として渡す。
- `DesiredIPRange` の IP 文字列を ORM で数値比較しない。
- DB から取得した range rows を pure helper に渡して判定する。
- Job summary に `range_candidates` 件数を含める。

`IPAddress` candidate の取得は引き続き `order_by("host", "mask_length")` のまま。
README_DEV の Nautobot 3.1.x compatibility note と整合している。

## Tests

`test_evaluations.py` の endpoint fixture に明示的な
`ip_policy="dhcp_reserved"` を追加した。

追加テスト:

- `dhcp_reserved` endpoint が `dhcp_reservable_pool` 内なら DHCP-ready になる。
- `dhcp_reserved` endpoint が `dhcp_dynamic_pool` 内なら partial gap になり、DHCP-ready にならない。
- `static` endpoint は MAC candidate があっても DHCP-ready にならない。
- matching range がない場合に `missing_ip_policy_range` を出す。
- overlapping/multiple matching range で `ambiguous_ip_policy_range` を出す。
- invalid range row があっても crash せず `invalid_ip_policy_range` を出す。

実行結果:

```bash
cd nintent && python3 -m unittest nautobot_intent_catalog.tests.test_evaluations
```

結果:

```text
Ran 31 tests in 0.002s
OK
```

README_DEV のローカルテスト方針に沿って全体も確認した。

```bash
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
```

結果:

```text
Ran 81 tests in 0.007s
OK
```

## README_DEV Consistency

README_DEV の注意点と矛盾しない。

- 旧 plugin 名、旧 setting key、旧 import path、旧 URL alias は追加していない。
- Nautobot `IPAddress.address` を ORM field として扱う変更はしていない。
- `IPAddress.objects.order_by("host", "mask_length")` は維持している。
- range 判定は Nautobot model 依存ではなく pure helper に閉じている。
- ローカル検証は Nautobot/Django なしで動く unit tests を使用した。

## Notes For Step 6

Step 6 の dnsmasq export では、今回の evaluation result を使って
`dhcp_reservations` を抑制できる。

期待する接続:

- `ExportDnsmasqRecords` は引き続き side-effect free にする。
- `DesiredEndpoint.ip_policy=dhcp_reserved` だけを `dhcp-host=` の候補にする。
- endpoint evaluation の `dhcp_reservation_ready=false` を尊重する。
- `DesiredIPRange.range_policy=dhcp_dynamic_pool` と `generate_dnsmasq=true` から
  `dhcp-range=` を生成する。
- JSON payload は `dns_records`、`dhcp_reservations`、`dhcp_ranges` を分ける。
