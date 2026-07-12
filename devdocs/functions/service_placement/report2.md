# Service Placement 実装レポート: Step 2

## 実施範囲

`plan.md`の「2. Add placement and node operational models in nintent」を実装した。
サービス配置とnode実行ポリシーをtyped modelとして追加し、Nautobot CRUD、strict
YAML loader/importer、参照解決、所有権分離、テスト、概念・運用文書を更新した。

旧placement名、旧YAML root、Ansible group alias、互換reader、converter、fallback、
dual-writeは追加していない。新しい配置モデルにはAnsible group fieldを持たせず、
`deployment_profile`だけを保存する。

## Migration

以下の順序付きmigrationを追加した。

- `0003_desired_node_actual_types.py`
  - 既にmodelに存在していたがmigration化されていなかった
    `DesiredNode.accepted_actual_types`を追加した。
  - `DesiredNode.node_type`を現行4種類
    `device|virtual_machine|container|service_host`へ一致させた。
- `0004_service_placement_operational_config.py`
  - `DesiredServicePlacement`と`DesiredNodeOperationalConfig`を追加した。
  - placement instance一意性、profile/schemaの非空、placement configのPostgreSQL
    JSON object型、actual-state policyとOS fieldの排他・必須条件をDB constraintにした。

既存migrationを書き換えず、追加migrationだけで現在のmodel stateへ到達する。

## DesiredServicePlacement

以下を実装した。

- `DesiredService`、`DesiredNode`、任意の`DesiredEndpoint`への明示的FK
- `(desired_service, instance_name)`一意制約
- `active|disabled`のdesired state
- instance role、deployment profile、config schema version、JSON config
- `manual|yaml|policy|generated`のassignment sourceとoperator reason
- configがdictであること、profile/schema非空、endpoint/node一致のmodel validation
- service、node、endpoint削除時に暗黙にplacementを失わない`PROTECT`方針

## DesiredNodeOperationalConfig

以下を実装した。

- `DesiredNode`とのone-to-one関係
- `required|declared` actual-state policy
- required時の`expected_host_os=linux|macos`
- declared時の`declared_host_os=haos`
- `local|tailscale` connection pathとnode-scoped endpoint選択
- Ansible port、`none|wol|macos_sleep` power control、明示的laptop分類
- expected/declared OS排他、endpoint/node一致、connection endpoint要件、
  platform/power組合せ、port範囲のmodel validation

Tailscale endpointは有効なIPを必須とした。declared local endpointはIP、DNS、mDNS
のいずれかを必須とした。Linuxは`none|wol`、macOSは`none|macos_sleep`、HAOSは
`none`だけを許可する。

## Nautobot UI

両modelについて以下を追加した。

- `NautobotModelForm`
- filter set
- list table
- list/detail/add/edit/delete viewとURL
- detail template
- Intent Catalog navigation item
- DesiredService detail上のplacement一覧
- DesiredNode detail上のoperational configとplacement一覧
- Source YAML diagnostic view上の新section表示

Nautobot 3.1系のchangelog action問題を避けるため、table actionは既存方針と同じ
`edit|delete`に限定した。

## Strict YAML loader/importer

新しいtop-level sectionを追加した。

- `desired_service_placements`
- `desired_node_operational_configs`

参照契約は以下に固定した。

- nodeはglobally uniqueな`DesiredNode.slug`だけで解決する。
- serviceはIntentSource slug、catalog namespace、catalog metadata name、service type
  の4項目をすべて指定する。
- endpointは選択済みnode内の`name + endpoint_type`で解決する。
- missingまたは複数matchはエラーとし、最初のrowを選択しない。

新sectionはunknown field、不完全な参照、非slug identity、list/scalar config、JSON
非互換値、文字列boolean、policy不整合、重複identityを拒否する。旧shapeへのrename、
coercion、alias、fallbackは実装していない。

Import Job全体を`transaction.atomic()`で囲み、途中の参照・validation失敗時に部分保存
しないよう変更した。全create/updateで`full_clean()`を実行し、同一identityかつ同一値
の場合はwriteしないidempotent upsertとした。既存DesiredEndpointもnode名ではなくslug
だけで解決するbreaking contractへ変更した。

## DesiredService所有権

Git解析は引き続きqualified service identityに対して`update_or_create()`を行い、置換する
のは解析所有fieldと`DesiredDependency`だけである。placement default/identityは独立した
importer関数へ分離し、service analysis defaultにはplacement fieldを含めていない。
したがってrepository再解析は同じDesiredService rowを更新し、関連placementを削除・上書き
しない。

## Documentation

- `CONCEPT.md`
  - placementとnode operational policyの責務、所有権、validationを追加した。
  - service placementを`expected_spec`へ格納する旧説明を削除した。
- `README.md`
  - 現行YAML shape、qualified reference、atomic import、strict rejectionを記録した。
  - node名参照と旧shape変換の説明を削除した。

## テストと検証

- nintent unit tests: `136 tests`, 全成功
- Python `compileall`: 成功
- `git diff --check`: 成功
- Django 4.2.30によるmodel/migration module import: 成功
- Django migration stateと現在のmodel stateのautodetector比較: 差分なし
- template存在テスト: 新detail templateを含め成功
- strict loader test:
  - qualified service/node-scoped endpoint正常系
  - unknown placement field拒否
  - unqualified service拒否
  - HAOS policy、boolean、connection、power不整合拒否
- importer helper test:
  - unchanged時のidempotency
  - create/update前のvalidation
  - endpoint queryのnode scope
  - service queryの4項目qualified identity

ローカル仮想環境には検証用としてDjango 4.2.30を追加したが、`pyproject.toml`、
`uv.lock`、package dependencyには追加していない。

## 実環境で必要な確認

このworkspaceにはNautobot/PostgreSQL runtimeがないため、以下は実環境で実施する。

```bash
nautobot-server makemigrations nautobot_intent_catalog --check --dry-run
nautobot-server migrate nautobot_intent_catalog
```

その後、Nautobot web/workerを再起動し、両modelのCRUD、filter、navigation、Job discovery、
PostgreSQL `jsonb_typeof(config) = 'object'` constraint、同一YAMLの2回importが2回目に
unchangedとなることを確認する。

## Exit criterion

source上では、operatorがplacementとoperational settingsをUIまたはenvironment YAMLから
作成でき、HAOS declared stateを表現でき、service再解析が独立所有placementを保持する
実装になった。実Nautobot/PostgreSQLでのmigration/UI smoke testだけをdeployment時確認事項
として残す。

Step 2では後方互換実装を追加していない。既存`expected_spec.ansible_groups`の撤去、
`preferred_services`撤去、production seedのplacement化はplanのStep 3以降の対象であり、
今回の新model/loader/importerはそれらを読まない。
