# 強化学習（Q学習）によるロボットナビゲーション

このプロジェクトは、Q学習エージェントを訓練し、差動駆動ロボットが2D環境で指定されたゴールに到達することを目指すものです。シミュレーションはPygameで構築されており、静的・動的な障害物や複雑な迷路など、様々な難易度のレベルが用意されています。訓練プロセスは並列化されており、ハイパーパラメータのチューニングや訓練状況を監視するためのTensorBoard連携機能も含まれています。

[詳細なシミュレーション説明はこちら](sims_md/README.md)



---

## 特徴

**Pygameベースのシミュレータ (`game_simulator.py`)**

* 差動駆動ロボットのための2Dシミュレーション環境
* 環境認識のためのLiDARセンサーシミュレーション
* 複数の難易度レベル（"Step"）による多様なシナリオ:

  * Step 0-2: 基本的なゴール到達タスク
  * Step 3-4: ランダムな数の静的障害物がある環境
  * Step 5-6: 壁と静的障害物のある迷路のような環境
  * Step 7-8: 動的障害物のある複雑な迷路
* 多様な動的障害物:

  * SlowBouncingObstacle: 一定速度で移動し、壁で跳ね返る
  * AppearingObstacle: ランダムな間隔で出現・消滅する
  * CircularObstacle: 円形の軌道で移動する
  * BlinkingObstacle: 開閉するドアとして機能する

**強化学習環境 (`rl_env.py`)**

* シミュレータをラップし、Gymライクなインターフェース（reset, step）を提供
* 状態表現: ゴールまでの距離、ゴールへの角度差、正規化されたLiDARの距離データ
* 報酬関数: カスタマイズ可能

**Q学習エージェントと訓練 (`train_rl.py`)**

* 離散化された状態行動空間から方策を学習
* 並列学習: Pythonのmultiprocessingでグリッドサーチ
* TensorBoard連携: エピソード報酬や成功率を可視化
* ハイパーパラメータチューニング: grid\_search関数で体系的な探索

---

## ファイル概要

* `game_simulator.py`: シミュレーション環境のコア。直接実行でロボットを手動操作可能
* `rl_env.py`: シミュレータをラップした強化学習環境
* `train_rl.py`: Q学習エージェント・訓練・グリッドサーチ・TensorBoard

---

## インストール

1. リポジトリをクローン

```bash
git clone https://github.com/Saisei2004/nav-rl-qlearning.git
cd nav-rl-qlearning
```

2. 必要なPythonライブラリをインストール
   （仮想環境推奨、`requirements.txt`が無い場合は手動で）

```bash
pip install pygame numpy torch tensorboard
```

---

## 使い方

### 1. RLトレーニングの実行

```bash
python train_rl.py
```

* スクリプト内で定義されたハイパーパラメータのグリッドサーチが開始されます。
* 異なるパラメータで並列訓練を実行し、各セットの成功率を出力。
* Ctrl+Cでプロセス停止、その時点までの結果の要約が表示されます。

### 2. TensorBoardでの監視

* 訓練データは自動記録。TensorBoard起動で進捗を視覚化。

```bash
tensorboard --logdir=runs
```

* [http://localhost:6006](http://localhost:6006) でダッシュボード表示。各ワーカープロセスのReward/EpisodeやSuccessRate/Episodeを確認できます。

### 3. シミュレーションの手動実行

* RLエージェントなしで動作確認したい場合、`game_simulator.py` の `mode` を変更して実行。

```python
# game_simulator.py内
if __name__ == "__main__":
    # モードを変更して異なる環境をテスト
    game = Game(obstacle_count=10, mode="Step_8")
    game.run()
```

* 実行:

```bash
python game_simulator.py
```

* キー操作:

  * 左車輪: 2 (高速前進), w (低速前進), s (低速後退), x (高速後退)
  * 右車輪: 1 (高速前進), q (低速前進), a (低速後退), z (高速後退)

---

## カスタマイズ

* **訓練パラメータ**: `train_rl.py` の `grid_search` でエピソード数や並列数を調整
* **ハイパーパラメータ探索空間**: grid\_search内のパラメータリストを変更
* **報酬関数**: train\_rl.pyの `improved_reward` を編集
* **行動空間**: train\_rl.py の `ACTION_SET` を変更
* **環境シナリオ**: game\_simulator.py で新しい "Step" モードを作成

