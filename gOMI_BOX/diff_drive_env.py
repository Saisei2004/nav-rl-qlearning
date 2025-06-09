import gymnasium as gym
from gymnasium import spaces

import numpy as np

WIDTH, HEIGHT = 800, 600
ROBOT_RADIUS = 15
GOAL_RADIUS = 20

class DiffDriveEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0]),
            high=np.array([WIDTH, HEIGHT, WIDTH, HEIGHT]),
            dtype=np.float32
        )
        self.action_space = spaces.Discrete(4)
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.robot_x = np.random.uniform(ROBOT_RADIUS, WIDTH - ROBOT_RADIUS)
        self.robot_y = np.random.uniform(ROBOT_RADIUS, HEIGHT - ROBOT_RADIUS)
        self.robot_angle = np.random.uniform(0, 360)
        self.goal_x = np.random.uniform(ROBOT_RADIUS, WIDTH - ROBOT_RADIUS)
        self.goal_y = np.random.uniform(ROBOT_RADIUS, HEIGHT - ROBOT_RADIUS)
        self.t = 0
        self.max_steps = 500
        obs = np.array([self.robot_x, self.robot_y, self.goal_x, self.goal_y], dtype=np.float32)
        return obs, {}


    def step(self, action):
        if action == 0:  # 前進
            self.robot_x += 5 * np.cos(np.deg2rad(self.robot_angle))
            self.robot_y += 5 * np.sin(np.deg2rad(self.robot_angle))
        elif action == 1:  # 左回転
            self.robot_angle = (self.robot_angle - 20) % 360
        elif action == 2:  # 右回転
            self.robot_angle = (self.robot_angle + 20) % 360
        elif action == 3:  # 後退
            self.robot_x -= 5 * np.cos(np.deg2rad(self.robot_angle))
            self.robot_y -= 5 * np.sin(np.deg2rad(self.robot_angle))

        self.robot_x = np.clip(self.robot_x, ROBOT_RADIUS, WIDTH - ROBOT_RADIUS)
        self.robot_y = np.clip(self.robot_y, ROBOT_RADIUS, HEIGHT - ROBOT_RADIUS)

        dist = np.linalg.norm([self.robot_x - self.goal_x, self.robot_y - self.goal_y])
        terminated = dist < GOAL_RADIUS                # ゴール到達で「自然な終了」
        truncated = self.t >= self.max_steps           # ステップ数オーバーで「強制終了」
        reward = 1.0 if terminated else -0.01

        obs = np.array([self.robot_x, self.robot_y, self.goal_x, self.goal_y], dtype=np.float32)
        self.t += 1
        info = {}

        return obs, reward, terminated, truncated, info


    def render(self, mode="human"):
        pass  # 必要なら可視化
