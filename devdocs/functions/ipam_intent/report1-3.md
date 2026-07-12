# nintent IPAM Intent Step 1-3 Report

## Scope

`plan.md` の Step 1 だけでは data model、UI、YAML import の境界が
中途半端になるため、Step 1-3 相当をまとめて実装した。

今回の主目的は、`generate_dnsmasq` に混ざっていた DNS export と DHCP
reservation export の意味を分離し、IP range intent を nintent 側の desired
state として持てるようにすること。

## Implemented

### Data model

- `DesiredEndpoint.ip_policy` を追加した。
  - `static`
  - `dhcp_reserved`
  - `external`
- `DesiredIPRange` を追加した。
  - `name`
  - `slug`
  - `start_address`
  - `end_address`
  - `range_policy`
  - `lifecycle`
  - `generate_dnsmasq`
  - `dnsmasq_options`
  - `description`
- migration `0002_ipam_intent_contract.py` を追加した。

`DesiredIPRange` は Nautobot IPAM の actual model ではなく、
`nautobot_intent_catalog` の desired state として実装している。
Nautobot に存在しない `IPRange` モデルを前提にしていない。

### UI surfaces

`DesiredIPRange` を既存 app model と同じ CRUD パターンへ接続した。

- form
- table
- filter
- list/detail/create/edit/delete views
- URL routes
- navigation item
- detail template `desirediprange.html`

`DesiredEndpoint` については、form、table、filter、detail template、
node detail 内の endpoint table、quick-add form に `ip_policy` を追加した。

README_DEV の注意に合わせて、`ObjectView` 用の detail template を追加し、
`tests/test_templates.py` も更新した。`ButtonsColumn` は既存と同じ
`buttons=("edit", "delete")` の明示指定を維持している。

### YAML loader and importer

YAML loader に `desired_ip_ranges` top-level section を追加した。

Example:

```yaml
desired_ip_ranges:
  - name: home-dynamic-dhcp
    slug: home-dynamic-dhcp
    start_address: 192.168.0.200
    end_address: 192.168.0.250
    range_policy: dhcp_dynamic_pool
    lifecycle: active
    generate_dnsmasq: true
    dnsmasq_options:
      lease_time: 12h
```

`DesiredEndpointEntry` に `ip_policy` を追加した。
`ip_address` を持つ endpoint は `ip_policy` 必須にしている。
IP intent がない endpoint は importer 側で `external` として扱う。

Importer には次を追加した。

- `desired_ip_range_identity()`
- `desired_ip_range_defaults()`
- endpoint defaults への `ip_policy` 反映
- IP intent があるのに `ip_policy` がない場合の拒否

`ImportIntentSources` Job は `desired_ip_ranges` を import し、
import summary に range count と created/updated/unchanged count を含める。

### dnsmasq export behavior

DHCP reservation export の条件に `ip_policy=dhcp_reserved` を追加した。

- `static`: DNS record は export 可能、DHCP reservation は export しない
- `dhcp_reserved`: MAC と node facts が deterministic な場合に DHCP reservation 対象
- `external`: nintent/IPAM DHCP 管理外として reservation 対象外

これにより、`generate_dnsmasq=true` だけで DHCP reservation が出る暗黙挙動を
外した。DNS record export は引き続き `generate_dnsmasq` と
`dnsmasq_record_type` で制御する。

## Documentation updates

`README.md` と `CONCEPT.md` の YAML 例に `ip_policy` を追加した。
新しい loader 契約では、IP address 付き endpoint が `ip_policy` なしだと
invalid になるため、ドキュメント例もそのまま import できる形に更新している。

## Verification

README_DEV に記載されているローカルテストを実行した。

```text
python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 71 tests in 0.006s
OK
```

追加で構文チェックと whitespace チェックも実行した。

```text
python3 -m compileall nautobot_intent_catalog
git diff --check
```

どちらも問題なし。

## README_DEV consistency

- 旧 plugin 名、旧 setting key、旧 import path、旧 URL alias の fallback は追加していない。
- Nautobot `IPRange` の存在を仮定していない。
- `ObjectView` 追加に合わせて detail template を追加した。
- `tests/test_templates.py` を更新した。
- `ButtonsColumn` の changelog action 問題を避ける既存方針を維持した。
- Job import は Nautobot がある環境では壊れた import が loud failure になる既存構造を維持した。

## Remaining work

この workspace には Nautobot/Django がないため、次は実 Nautobot 環境で
README_DEV 記載の確認が必要。

```bash
nautobot-server makemigrations nautobot_intent_catalog --check --dry-run
nautobot-server migrate nautobot_intent_catalog
```

Step 4 以降では、range containment、overlap detection、endpoint policy と
range policy の整合性評価を追加する。

Step 5 以降では、`DesiredIPRange.range_policy=dhcp_dynamic_pool` から
`dhcp-range=` artifact を生成する処理を追加する。
