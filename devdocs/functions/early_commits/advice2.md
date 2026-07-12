ユーザー：
nautobotのプラグイン(app)の作り方を教えてください。

AI:
Nautobotのプラグイン（Nautobot 2.0以降では公式に「App」と呼ばれます）の開発は、PythonとDjangoの知識があればスムーズに進めることができます。

Nautobot Appをゼロから開発するための基本的な手順と全体像を解説します。

1. 開発環境の準備
一番手っ取り早く確実なのは、公式が提供している開発テンプレート（Cookiecutter）を使用する方法です。

クローンと環境構築の主な流れ
Cookiecutterの実行: 公式の cookiecutter-nautobot-app を使うと、必要なディレクトリ構造や設定ファイルが自動生成されます。

Bash
pip install cookiecutter
cookiecutter https://github.com/nautobot/cookiecutter-nautobot-app
プロンプトへの入力: App名（例: nautobot-app-my-plugin）や開発者情報を入力します。

2. Nautobot App の基本構造
生成されたAppのディレクトリ構造は、通常のDjangoアプリに非常に似ています。最低限必要な構成は以下の通りです。

Plaintext
nautobot_my_plugin/
│
├── __init__.py          # Appのメタデータを定義（最重要）
├── navigation.py       # Nautobotのメニュー画面に項目を追加する設定
├── views.py            # 画面を表示するためのロジック
├── urls.py             # ルーティング（URLとViewのマッピング）
├── models.py           # 独自データをデータベースに保存する場合に定義
└── templates/          # 画面のHTMLテンプレート
__init__.py の書き方（必須設定）
Nautobotに「これはプラグインです」と認識させるために、NautobotAppConfig を継承したクラスを定義します。

Python
from nautobot.apps.config import NautobotAppConfig

class MyPluginConfig(NautobotAppConfig):
    name = "nautobot_my_plugin"          # パッケージ名
    verbose_name = "My First Plugin"      # 画面に表示される名前
    version = "0.1.0"                    # バージョン
    description = "Nautobotのカスタムプラグインです"
    base_url = "my-plugin"               # URLのプレフィックス
    required_settings = []
    default_settings = {}

config = MyPluginConfig
3. 基本的な機能の実装ステップ
独自画面を追加する基本的な流れは 「URLを決める」→「Viewを作る」→「画面（Template）を作る」 です。

Step 1: views.py でビューを作成
Nautobot 2.0以降では、便利な汎用ビュー（generic.Views）が用意されています。

Python
from nautobot.apps.views import GenericView

class MyPluginHomeView(GenericView):
    template_name = "nautobot_my_plugin/home.html"

    def get(self, request):
        return self.render_to_response({"message": "こんにちは、Nautobot App!"})
Step 2: urls.py でルーティングを設定
Python
from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.MyPluginHomeView.as_view(), name="home"),
]
Step 3: templates/nautobot_my_plugin/home.html を作成
Nautobotのベースデザインを引き継ぐために、base.html を拡張します。

HTML
{% extends 'base.html' %}

{% block content %}
<div class="container-fluid">
    <h1>{{ message }}</h1>
    <p>ここにプラグインの独自コンテンツを記述します。</p>
</div>
{% endblock %}
4. Nautobotへの組み込みとテスト
開発中のAppをNautobotに読み込ませるには、以下の設定を行います。

Appのインストール: 開発環境のNautobotと同じ環境（Dockerコンテナ内など）で、作成したAppをインストールします。

Bash
pip install -e /path/to/nautobot-my-plugin
nautobot_config.py への追加:
Nautobotの設定ファイルにある PLUGINS リストにAppを追加します。

Python
PLUGINS = [
    "nautobot_my_plugin",
]
サーバーの再起動:
Nautobotのサービス（またはDockerコンテナ）を再起動すると、/plugins/my-plugin/home/ で作成した画面にアクセスできるようになります。

さらに高度な開発をするには？
シンプルな画面表示ができるようになったら、必要に応じて以下の機能を追加していきます。

Models (models.py): 独自に管理したいデータ（例: 回線情報、機器の独自ステータスなど）のテーブルをDBに作成する。

Navigation (navigation.py): Nautobotの上部メニューやサイドバーに、自分のAppへのリンクを配置する。

API (api/): 外部システムと連携するためのREST APIやGraphQLのエンドポイントを生やす。

まずは「ボタンを押したら文字が表示される」といった簡単な画面作りから始めてみるのがおすすめです。何か具体的に「こういう機能を作りたい」というイメージはありますか？