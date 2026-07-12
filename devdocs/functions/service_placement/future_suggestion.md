# Service Placementの将来候補

以下はproduction inventory schema `1.0`の成立に不要であり、今回の実装範囲には
含めない。必要性と利用側の契約が具体化した時点で、schema versionを更新して追加する。

## Actual-backed Virtual Machine対応

- nodeutils reportをNautobot `VirtualMachine`へ安全に対応付けるingest契約を追加する。
- DeviceとVMで異なるactual field、interface、IP、識別子の取得方法を定義する。
- production composerでVMをサポートし、現在の`unsupported_actual_type` skipを廃止する。

## declared Linux/macOS対応

- nodeutilsを実行できないLinux/macOSをdeclared stateとして許可する条件を定義する。
- declared値を`linux`/`macos` selectorへ入れることによるactualとの意味の違いを明示する。
- 必要な接続・鮮度・drift評価契約を追加する。schema `1.0`ではdeclared platformを
  HAOSだけに限定する。

## ホスト別SSH user

- 全ホスト共通の`ansible_user: "{{ default_user }}"`で対応できなくなった場合、
  `DesiredNodeOperationalConfig`へtypedなホスト別userを追加する。
- user名の検証、秘密情報との分離、bootstrap inventoryとの整合を定義する。

## Actual-state allowlistの拡張

- `os_name`、`os_version`、`architecture`、収集時刻などは、具体的なplaybook consumerが
  追加された場合に限りhost variableとして公開する。
- CPU、memory、GPU、package、Docker、interface一覧、observed service payloadを
  production inventoryへ一括展開しない。必要な値ごとにsource path、型、鮮度、テストを
  定義する。

## Platform・接続方式・電源制御の追加

- Linux、macOS、HAOS以外のplatformを追加する場合は、正規化値、selector、必要actual、
  対応playbookをまとめて契約化する。
- Tailscale以外のVPNや踏み台接続、ホスト別SSH optionが必要になった場合は、文字列の
  任意注入ではなくtyped operational fieldとして追加する。
- 新しいpower control方式は対応platform、必須actual、実行playbookを明示し、
  platformとの組み合わせ検証を拡張する。

## Deployment profile schemaの拡張

- schema `1.0`で監査済みのscalar、list、限定的なcollection以外が必要になった場合、
  nested objectのproperties、追加キー禁止、制約値などを明示できるschemaへ拡張する。
- 拡張時も新schemaへ一括移行し、旧profile schemaのreaderやversion negotiationは
  残さない。
