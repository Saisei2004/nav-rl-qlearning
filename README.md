強化学習Q学習並列プロジェクト

概要

このプロジェクトは、自作強化学習環境（GameEnv）を用いて、13プロセス並列で1つのQテーブル（エージェント）を共有しながら学習を行うものです。学習の進捗や成功率はTensorBoardで可視化できます。

📁 ディレクトリ構成

/home/saisei/SDKD/
├── train_rl.py         # メインの学習実行スクリプト
├── rl_env.py           # GameEnvなど環境クラス
├── ...                 # その他依存ファイル

🚀 実行方法

1. 必要なパッケージのインストール（初回のみ）

pip install numpy torch tensorboard pygame

※KITの学内プロキシを利用する場合:

pip install --proxy=http://wwwproxy.kanazawa-it.ac.jp:8080 numpy torch tensorboard pygame

2. スクリプトディレクトリに移動

cd ~/SDKD

3. 学習スクリプトの実行

python3 train_rl.py

4. TensorBoardで学習ログを可視化

スクリプト実行後、自動でTensorBoardが立ち上がります。
もし手動で起動する場合は以下を実行してください：

tensorboard --logdir runs

ブラウザで http://localhost:6006/ にアクセスし、学習の進捗グラフを確認できます。

🔑 補足

train_rl.pyを実行すると、13プロセスで同じQテーブルを共有しながら効率的に学習します。

TensorBoardに表示されるseed_0〜seed_12は各worker（プロセス）ごとのログ名ですが、実際はQテーブル（知識）は1つです。

Qテーブルや報酬関数などのパラメータはtrain_rl.py内で調整可能です。

ログをリセットしたい場合はruns/フォルダを削除してから再実行してください（rm -rf runs/）。

📧 問い合わせ

不明点やバグ報告は、松田再生まで。

👑 著作権

本プロジェクトは金沢工業大学 松田再生が作成しました。

