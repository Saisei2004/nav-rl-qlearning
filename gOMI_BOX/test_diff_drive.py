from stable_baselines3 import PPO
from gOMI_BOX.diff_drive_env import DiffDriveEnv

env = DiffDriveEnv()
model = PPO.load("ppo_diff_drive")

obs, _ = env.reset()
done = False
while not done:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
    print(f"obs={obs}, reward={reward}")
    env.render()  # ← もし可視化したければここに追加
