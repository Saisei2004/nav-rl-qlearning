# evaluate.py (修正版)

import argparse
import time
from stable_baselines3 import PPO

# 作成した環境ファイルをインポート
from navi_env import NaviEnv

def main(args):
    """学習済みモデルを評価するためのメイン処理"""

    # 1. 評価用の環境を作成 (描画モードを "human" に設定)
    env = NaviEnv(render_mode="human", mode=args.mode)

    # 2. 学習済みモデルをロード
    try:
        model = PPO.load(args.model_path, env=env)
        print(f"Model loaded from: {args.model_path}")
    except Exception as e:
        print(f"Error loading model: {e}")
        print(f"Please make sure the model path '{args.model_path}' is correct.")
        return

    # 3. 評価エピソードを指定回数実行
    print(f"Running {args.episodes} evaluation episodes...")
    for i in range(args.episodes):
        obs, info = env.reset()
        done = False
        total_reward = 0
        step_count = 0
        
        while not done:
            # deterministic=Trueで、学習した方策の「最善手」を選択
            action, _states = model.predict(obs, deterministic=True)
            
            # <<< この行を修正しました！ >>>
            # モデルが返すNumpy配列から、中の整数を取り出す
            obs, reward, terminated, truncated, info = env.step(action.item())
            env.render()
            
            total_reward += reward
            step_count += 1
            done = terminated or truncated
            
            # 少し待機して動きを見やすくする
            time.sleep(0.01)
        
        print(f"Episode {i+1} finished in {step_count} steps. Total Reward: {total_reward:.2f}")

    env.close()
    print("Evaluation finished.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate a trained navigation agent.")
    
    parser.add_argument(
        "--model_path", 
        type=str, 
        required=True, 
        help="Path to the saved model .zip file (e.g., ./models/exp01-step2-base.zip)"
    )
    parser.add_argument(
        "--mode", 
        type=str, 
        default="Step_4", 
        help="Environment mode to evaluate on (e.g., Step_2, Step_4)"
    )
    parser.add_argument(
        "--episodes", 
        type=int, 
        default=5, 
        help="Number of episodes to run for evaluation"
    )
    
    args = parser.parse_args()
    main(args)