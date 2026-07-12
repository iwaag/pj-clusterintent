# Service Placement 実装レポート: Step 1

## 実施範囲

`plan.md`の「1. Freeze and test the new contracts」を実装した。Nautobot/Django
実行環境を必要としない純粋Pythonの契約層と、Ansible側のcanonical JSON検証を
作成した。旧schema readerや互換処理は追加していない。

## 監査結果

現行のproduction inventory、旧example inventory、全playbookのhost selector、
profile対象roleのdefaults/tasks/templatesを監査した。分類結果は
`ansible_agdev/docs/production_inventory_contract.md`に固定した。

- observed selector: `linux`, `macos`
- declared selector: `haos`
- desired operational policy: `power_managed`
- service placement: `dnsmasq_server`, `prometheus_server`,
  `grafana_server`, `nomad_server`, `nomad_client`, `haos_server`,
  `prometheus_node_exporter_targets`
- bootstrap/production execution index: `ssh_hosts`
- obsolete: `gpu_hosts`, example-onlyの`nautobot_server`

`has_gpu`には現行consumerがないためproduction schemaから除外した。
`package_manager`は引き続き禁止し、Ansible factとrole内部ロジックを使用する。

## 確定した契約

- production inventory schema versionは`1.0`。
- deployment profile config schema versionは`1`のみを許可する。
- actual freshnessは生成時刻から72時間以内。ちょうど72時間はfreshとする。
- observed OS mappingは`Linux -> linux`、`Darwin -> macos`のみ。
- declared platformは`haos`のみ。
- power policyはLinux=`none|wol`、macOS=`none|macos_sleep`、HAOS=`none`。
- DesiredService参照はIntentSource slugを含む4項目の一意tuple。
- DesiredEndpoint参照は選択済みNode内の`name + endpoint_type`。
- local接続は`local_ip`, `local_dns_hostname`, `mdns_hostname`,
  `inventory_hostname`の順。Tailscaleは選択EndpointのIPを必須としfallbackしない。
- `ansible_user`は全host共通の`{{ default_user }}`としてgroup varsから供給する。
- canonical JSONはsort済み、空白なし、UTF-8、BOM/末尾改行なし、NaN禁止。
- production YAML metadata、companion reportのtop-level schema、global errorと
  host-skip reason codeを固定した。

## 追加・変更した成果物

### ansible_agdev

- `vars/deployment_profiles.yml`
  - 7 profileを追加。
  - roleで実在する変数名だけをallowlist化。
  - secret、package/version、生成済みDNS record、任意objectは公開しない。
- `docs/production_inventory_contract.md`
  - group、host variable、role/profile、参照、接続、freshness、platform、
    YAML/JSON schema、failure taxonomyの監査結果を記録。
- `vars/fixtures/canonical_json_contract.yml`
- `playbooks/verify_deployment_profiles_contract.yml`
  - AnsibleとPythonのcanonical JSON byte列およびSHA-256一致を検証。
- `inventories/generated/group_vars/all/main.yml`
- `inventories/production/group_vars/all/main.yml`
  - 共通`ansible_user: "{{ default_user }}"`を追加。
- `README_DEV.md`
  - 契約変更時の検証方法を追加。

### nintent

- `nautobot_intent_catalog/production_inventory_contract.py`
  - Django/Nautobot非依存のstrict validatorを追加。
  - canonical JSON/digest、profile shape、placement config type、qualified
    reference、endpoint ownership、platform/power、freshness、connection、
    host variable conflict、production YAML/report schemaを検証する。
- `nautobot_intent_catalog/tests/fixtures/production_inventory_contract_cases.yml`
  - Linux、macOS、HAOS、actual欠落・期限切れ、Endpoint mismatch、unknown
    profile、型不正、曖昧参照、OS drift、不正power、変数競合を追加。
- `nautobot_intent_catalog/tests/test_production_inventory_contract.py`
  - 上記fixtureおよびclosed schemaを実行可能な契約テストにした。
- `README_DEV.md`
  - contract moduleとfixtureの位置付けを追加。

## 検証結果

- nintent unit tests: `126 tests`, 全成功。
- Python compileall: 成功。
- production deployment profiles: 7件、strict validation成功。
- 現在のprofile canonical digest:
  `d3c8ce79a70668062ef71d9f78c5886f6ba088ad731f66cb1f466100bf16d638`
- Ansible canonical JSON fixture: byte列とSHA-256の双方が一致。
- Ansible playbook syntax check: 成功。
- 現行production inventory: 9 hostを正常にparse。
- 9 hostすべてで共通`ansible_user`契約を確認。
- `git diff --check`: nintent、ansible_agdevとも成功。

Vault実体がない環境のため、検証時だけ一時的なテスト用password fileを使用した。
secretや生成artifactはリポジトリへ保存していない。

## Exit criterion

生成予定の全groupとhost variableについて、documented sourceを定義した。
actualからのheuristic inferenceは契約層で許可していない。Step 1のexit criterionは達成。

## 次の実装

Step 2で`DesiredServicePlacement`と`DesiredNodeOperationalConfig`のmodel、migration、
CRUD、loader/importerを実装する。Nautobot実行環境がないため、model-free unit test、
static validation、migration source reviewを中心に進め、実環境で必要な確認事項を別途
記録する。
