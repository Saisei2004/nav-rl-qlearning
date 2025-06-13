# train.py

#

import argparse
import os
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

# 作成した環境ファイルをインポート
from navi_env import NaviEnv

def main(args):
    """メインの学習処理（Ctrl+C対応版）"""

    # デバイスの自動選択
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    
    print(f"=========================================")
    print(f"Using device: {device}")
    print(f"Number of parallel CPUs: {args.num_cpu}")
    print(f"Training mode: {args.mode}")
    print(f"=========================================")

    # ログとモデルの保存先ディレクトリを作成
    log_dir = f"./logs/{args.exp_name}/"
    model_dir = "./models/"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    # モデルの最終的な保存パス
    save_path = os.path.join(model_dir, args.exp_name)

    # 複数の環境を並列で実行
    envs = SubprocVecEnv([lambda: NaviEnv(mode=args.mode) for _ in range(args.num_cpu)])

    # 定期的にモデルを保存するためのコールバック（念のため残しておきます）
    checkpoint_callback = CheckpointCallback(
        save_freq=100_000,
        save_path=log_dir,
        name_prefix="rl_model",
        save_replay_buffer=True,
        save_vecnormalize=True,
    )

    if args.load_model:
        print(f"Loading model from {args.load_model} and continue training.")
        model = PPO.load(
            args.load_model, 
            env=envs, 
            device=device, 
            tensorboard_log=log_dir
        )
    else:
        print("Creating a new model.")
        # model = PPO("MlpPolicy", envs, verbose=1, device=device, tensorboard_log=log_dir)
        model = PPO(
            "MlpPolicy", 
            envs, 
            verbose=1, 
            device=device,
            tensorboard_log=log_dir,
            n_steps=2048,       # 各CPUが更新までに実行するステップ数
            batch_size=64,       # 1回の更新で使うデータサイズ
            n_epochs=10,         # 1回の更新でエポックを何回まわすか
            gamma=0.99,          # 割引率
            gae_lambda=0.95,     # GAEのラムダ
            clip_range=0.2,      # PPOのクリップ範囲
            ent_coef=0.03,       # <<< 0.0から0.01に変更。探索を促します。
            learning_rate=3e-4,  # 学習率
        )

    try:
        # 学習を実行
        model.learn(
            total_timesteps=args.timesteps,
            callback=checkpoint_callback,
            reset_num_timesteps=False if args.load_model else True
        )
    except KeyboardInterrupt:
        # Ctrl+Cで学習を中断した場合の処理
        print("\nTraining interrupted by user.")
    finally:
        # 学習が完了した場合も、中断した場合も、必ず最後にモデルを保存する
        print(f"Saving final model to {save_path}.zip")
        model.save(save_path)
        print("Model saved successfully.")
    
    print("=========================================")
    print("Script finished!")
    print(f"Model saved at: {save_path}.zip")
    print(f"Logs saved in: {log_dir}")
    print("=========================================")

if __name__ == '__main__':
    # このファイルが直接実行されたときに以下の処理を行う
    parser = argparse.ArgumentParser(description="Train a reinforcement learning agent for navigation.")
    
    # あなたのPCスペック(20スレッド)に合わせて推奨されるCPU並列数を自動計算
    try:
        default_num_cpu = max(1, os.cpu_count() - 2)
    except TypeError:
        default_num_cpu = 8 # os.cpu_count()が取得できない場合の予備

    # --- コマンドライン引数の設定 ---
    parser.add_argument("--mode", type=str, default="Step_4", help="Environment mode defined in NaviEnv (e.g., Step_2, Step_4)")
    parser.add_argument("--timesteps", type=int, default=1_000_000, help="Total number of steps for training")
    parser.add_argument("--num_cpu", type=int, default=default_num_cpu, help=f"Number of parallel environments (default: {default_num_cpu} for this machine)")
    parser.add_argument("--exp_name", type=str, required=True, help="A unique name for the experiment. Logs and models will be saved under this name.")
    parser.add_argument("--load_model", type=str, default=None, help="Path to a pre-trained model to continue training (e.g., ./models/exp01.zip)")
    parser.add_argument("--device", type=str, default="auto", choices=["cuda", "cpu", "auto"], help="Device to use for training (cuda, cpu, or auto-detect)")
    
    args = parser.parse_args()
    main(args)