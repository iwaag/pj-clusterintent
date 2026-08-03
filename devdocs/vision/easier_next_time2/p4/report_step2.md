# Report — Step 2: survey + select

実施日: 2026-08-04
ステータス: **完了**

## GUI surveyについての制約

`http://localhost:8000/plugins/intent-catalog/workflow-episodes/2249af5f-4ff5-41aa-8e83-55b1c57dd656/`
はNautobotのセッション認証（ブラウザログイン）を要求するviewであり、
`Authorization: Token` ヘッダを付与したcurlでは302（ログイン画面へのredirect）が
返るのみで、非対話的にHTMLを取得・検証することができなかった。ユーザーには
このURLを提示し確認を依頼した。GUIが実際にレンダリングする内容（一覧のstatus
フィルタ、詳細のreport/assessment/references/resolutionセクション）は、同じ
バックエンドAPIを叩く `nctl workflow-episode show --json` の出力で構造として
確認した（下記）。ブラウザでの見た目そのものは未検証であることを明記する。

## ユーザーへの確認

AskUserQuestionで、作成したepisode
(`2249af5f-4ff5-41aa-8e83-55b1c57dd656`, candidate) のGUI URLを提示し、
selectをユーザー自身が行うかエージェントに委任するかを確認した。ユーザーは
「エージェントに委任する」を選択した。

## select操作

```
$ nctl workflow-episode select 2249af5f-4ff5-41aa-8e83-55b1c57dd656
workflow episode 2249af5f-4ff5-41aa-8e83-55b1c57dd656 ('easier_next_time2 roadmap: Phase 4 real cycle') is now selected
```

`nctl workflow-episode show --json` で status が `candidate` → `selected` に
遷移したこと、`raw_data.report` / `references` が Step 1 で書き込んだ内容の
まま保持されていることを確認した。

## コミット

コードやdocsの変更はなし（live DB writeのみ）。本report_step2.mdのみを
コミットする。
