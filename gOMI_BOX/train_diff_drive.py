from stable_baselines3 import PPO
from gOMI_BOX.diff_drive_env import DiffDriveEnv

env = DiffDriveEnv()
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100_000)
model.save("ppo_diff_drive")
