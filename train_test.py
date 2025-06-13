# test_train.py

import time
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv

# 作成した環境ファイルをインポート
from navi_env import NaviEnv

# --- テスト用の設定 ---
TOTAL_STEPS = 10_000  # 計測する合計ステップ数
NUM_CPU = 18          # あなたのPCの推奨並列数
MODE = "Step_4"       # 平均的な複雑さのモード
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# DEVICE = "cpu"

def measure_speed():
    """学習速度を計測するメイン処理"""

    print("=========================================")
    print(f"Starting performance test...")
    print(f"Device: {DEVICE}, Parallel CPUs: {NUM_CPU}, Mode: {MODE}")
    print(f"Total steps to run: {TOTAL_STEPS}")
    print("=========================================")

    # 複数の環境を並列で実行
    # if __name__ == '__main__' の中にないとエラーになるため、この関数内で実行
    envs = SubprocVecEnv([lambda: NaviEnv(mode=MODE) for _ in range(NUM_CPU)])

    # モデルを作成
    model = PPO("MlpPolicy", envs, device=DEVICE)

    # 学習開始時間を記録
    start_time = time.time()

    # 学習を実行
    model.learn(total_timesteps=TOTAL_STEPS)

    # 学習終了時間を記録
    end_time = time.time()

    # --- 結果の計算と表示 ---
    duration = end_time - start_time
    steps_per_second = TOTAL_STEPS / duration

    print("\n=========================================")
    print(f"Performance test finished!")
    print(f"Total time taken: {duration:.2f} seconds")
    print(f"Total steps: {TOTAL_STEPS}")
    print(f"Steps Per Second (SPS): {steps_per_second:.2f}")
    print("=========================================")
    
    envs.close()

if __name__ == '__main__':
    # WindowsやmacOSでSubprocVecEnvを使う場合、このおまじないが必須です。
    # Linuxでも安全のため記述しておきます。
    measure_speed()
