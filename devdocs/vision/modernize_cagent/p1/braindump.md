cagentをpj-agdevのautolabエージェントやagforgeの新しい設計に追従させる。
ロールとしてのwindowはfrontに改名、routeとしてのwindowは当面残す。

# やりたいこと

## 前準備

### サブエージェント定義

frontとoperator

nctlを触るのはoperator

### cagent --help
nctlのread系操作だけまとめたcliを作る
cagent --helpで操作説明
後で操作系まとめたcagent-adminも作ろうと思ってるが今回はスコープ外

## cagent-トピックの設計

チャンネルは問わない。
autolabやagforge同様。
.local下のワークスペースにchatlog.mdを配置。

プロンプト合成に使うガイドはpj-clusterintent/cagent/agent/guides/front/guide.md

frontエージェントの返答時に"required_info.md"があった場合、
- それをoperatorフォルダにコピー
- "pj-clusterintent/cagent/agent/tools/toolset_nctl.md"をoperatorフォルダ直下の"tools/"フォルダにコピー
- プロンプトはpj-clusterintent/cagent/agent/guides/operator_read/guide.mdでoperator起動
- operatorの返事をそのままかえして終了

frontエージェントの返答時に"requested_change.md"があった場合、

- PlaneのClusterAdminプロジェクトのワークに追加。

# あとまわし
- 「ollamaがあったらそのエンドポイントを教えて、なければどっかに作って。」みたいな変更と情報取得両方問われた場合の対応