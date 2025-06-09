# rl_env.py
from game_simulator import LIDAR_MAX_DISTANCE
from game_simulator import Game   # Gameクラス本体（game_simulator.py）が同じディレクトリにあること
import numpy as np
print(LIDAR_MAX_DISTANCE)
class GameEnv:
    def __init__(self, reward_fn=None):
        self.game = Game(mode="Step_0")
        self.reward_fn = reward_fn if reward_fn else self.default_reward
        self.done = False

    def reset(self):
        # ゲーム状態を初期化
        self.game = Game(mode="Step_0")
        self.done = False
        return self.get_state()

    def step(self, action):
        # action: (v_left, v_right)のタプル
        self.game.robot.update(*action)
        done = self.game.check_goal() or self.game.check_collision()
        self.done = done
        state = self.get_state()
        reward = self.reward_fn(self, state, done)
        info = {}
        return state, reward, done, info

    def get_state(self):
        # 必要な状態変数をまとめて返す（ゴール距離/方向差/ライダー配列）
        x, y = self.game.robot.x, self.game.robot.y
        theta = self.game.robot.angle
        goal_dx = self.game.goal_x - x
        goal_dy = self.game.goal_y - y
        goal_dist = np.hypot(goal_dx, goal_dy)
        goal_dir = np.degrees(np.arctan2(goal_dx, -goal_dy)) % 360
        goal_dir_diff = (goal_dir - theta + 180) % 360 - 180
        # lidar = np.array(self.game.get_lidar_distances()) / LIDAR_MAX_DISTANCE
        lidar = np.array(self.game.get_lidar_distances()) / LIDAR_MAX_DISTANCE

        # 状態ベクトルとして結合して返す
        return np.concatenate([
            np.array([goal_dist / LIDAR_MAX_DISTANCE, goal_dir_diff / 180]),  # 正規化
            lidar
        ])

    def set_reward_function(self, fn):
        self.reward_fn = fn

    def default_reward(self, env, state, done):
        # シンプルな報酬例
        if self.game.check_goal():
            return 100
        if self.game.check_collision():
            return -100
        return -1


