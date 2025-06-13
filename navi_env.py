# navi_env.py (最終確定版)

####################################################
'''
# Step_0のモデルを元に、新しいゴール条件のStep_2を学習
python3 train.py --mode Step_2 --timesteps 1500000 --exp_name "exp09-step2-stop-goal" --load_model "./models/exp06-step0-lr-fix.zip"


# 新しく学習したモデルの動きを確認
python3 evaluate.py --model_path "./models/exp09-step2-stop-goal.zip" --mode Step_2

'''
####################################################

import pygame
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import math
import random

from navi_components import *

class NaviEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": FPS}

    def __init__(self, render_mode=None, mode="Step_4"):
        super().__init__()
        self.mode = mode
        self.render_mode = render_mode
        self.action_space = spaces.Discrete(5)
        self.action_to_velocity = {
            0: (2.0, 2.0), 1: (-2.0, -2.0), 2: (-1.5, 1.5),
            3: (1.5, -1.5), 4: (0.0, 0.0)
        }
        observation_dim = 2 + LIDAR_RESOLUTION
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(observation_dim,), dtype=np.float32)
        self.screen = None
        self.clock = None
        self.font = None
        if self.render_mode == "human": self._init_pygame()

    def _init_pygame(self):
        if self.screen is None and self.render_mode == "human":
            pygame.init()
            pygame.font.init()
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("NaviEnv")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont("sans-serif", 28)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._setup_scenario()
        self.prev_distance_to_goal = math.hypot(self.goal_x - self.robot.x, self.goal_y - self.robot.y)
        return self._get_obs(), self._get_info()

# navi_env.py の step メソッド全体を、以下のコードで置き換えてください

    def step(self, action):
        v_left, v_right = self.action_to_velocity[action]
        self.robot.update(v_left, v_right)
        for obs in self.dynamic_obstacles: obs.update()
        self.step_count += 1

        # --- 終了判定ロジック ---
        # ご指摘通り、最大ステップ数を500に変更
        max_steps = 300 if self.mode == "Step_0" else 500
        
        collided = self._check_collision()
        
        position_margin, angle_margin = 15, 20
        is_position_ok = (math.hypot(self.goal_x - self.robot.x, self.goal_y - self.robot.y) < position_margin)
        angle_diff = abs((self.robot.angle - self.goal_angle + 180) % 360 - 180)
        is_angle_ok = (angle_diff <= angle_margin)

        # ゴール判定（タイマー方式）
        STAY_TIME_FOR_GOAL = 15
        if is_position_ok and is_angle_ok:
            self.goal_zone_timer += 1
        else:
            self.goal_zone_timer = 0
        reached_goal = (self.goal_zone_timer >= STAY_TIME_FOR_GOAL)
        
        terminated = collided or reached_goal
        truncated = self.step_count >= max_steps

        # --- 報酬計算ロジック（最終版） ---
        reward = 0
        observation = self._get_obs()
        angle_diff_normalized = observation[1]

        # 【道しるべの報酬】ゴールに近づき、正しい方向を向くことを常にご褒美として与える
        current_distance = math.hypot(self.goal_x - self.robot.x, self.goal_y - self.robot.y)
        reward += (self.prev_distance_to_goal - current_distance)  # 距離を縮める報酬
        self.prev_distance_to_goal = current_distance
        
        # 向きを合わせる報酬（ゴールに近づいた時ほど重要になる）
        if current_distance < ROBOT_RADIUS * 5: # ゴールに近い時だけ向きを評価
             reward += (1 - abs(angle_diff_normalized)) * 0.2

        # 【ペナルティと最終ボーナス】
        reward -= 0.02  # 時間ペナルティ（少し重くして、ウロウロするのを防ぐ）
        if collided: reward -= 10.0
        if reached_goal: reward += 50.0 # 最後までやり遂げたら特大ボーナス
            
        return observation, reward, terminated, truncated, self._get_info()

    def render(self):
        if self.render_mode is None: return
        self._init_pygame()
        self.screen.fill(WHITE)
        all_obstacles = self.wall_obstacles + self.obstacles + self.dynamic_obstacles
        for obs in all_obstacles: obs.draw(self.screen)
        self._draw_goal_with_direction()
        self.robot.draw(self.screen)
        self._draw_lidar(self._get_lidar_distances())
        step_text = self.font.render(f"Step: {self.step_count}", True, (0, 0, 0))
        self.screen.blit(step_text, (10, 10))
        if self.render_mode == "human":
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.close()
            pygame.display.flip()
            self.clock.tick(self.metadata["render_fps"])
        elif self.render_mode == "rgb_array":
            return np.transpose(np.array(pygame.surfarray.pixels3d(self.screen)), axes=(1, 0, 2))

    def close(self):
        if self.screen is not None: pygame.display.quit(); self.screen = None

    def _setup_scenario(self):
        self.step_count = 0
        self.wall_obstacles, self.obstacles, self.dynamic_obstacles = [], [], []
        avoid_rects = []
        if self.mode == "Step_0":
            x, y, start_angle = random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50), random.randint(0, 359)
            self.robot, self.goal_x, self.goal_y = Robot(x, y, start_angle), x, y
            while True:
                goal_angle = random.randint(0, 359)
                if abs((goal_angle - start_angle + 180) % 360 - 180) >= 40: break
            self.goal_angle = goal_angle
        else: # Step_1以降
            self.robot = Robot(WIDTH // 2, HEIGHT // 2); avoid_rects.append(self.robot.get_rect().inflate(50, 50))
            self.goal_x, self.goal_y = self._find_safe_spawn(avoid_rects); self.goal_angle = random.randint(0, 359)
            avoid_rects.append(pygame.Rect(self.goal_x - 50, self.goal_y - 50, 100, 100))
            
            scenarios = {"Step_3": (5, 0), "Step_4": (15, 0), "Step_6": (10, 3), "Step_7": (5, 2), "Step_8": (0, 5)}
            num_obs, num_dyn = scenarios.get(self.mode, (0, 0))
            
            if self.mode in ["Step_5", "Step_6", "Step_7", "Step_8"]:
                self.wall_thick = 8
                door_len = 60 if self.mode == "Step_7" else 100
                self.wall_obstacles = self._generate_walls(door_len); avoid_rects.extend([w.rect for w in self.wall_obstacles])

            for _ in range(num_obs): self.obstacles.append(self._get_random_obstacle(avoid_rects))
            for _ in range(num_dyn): self.dynamic_obstacles.append(self._get_random_obstacle(avoid_rects, True))

    def _get_obs(self):
        goal_dx, goal_dy = self.goal_x - self.robot.x, self.goal_y - self.robot.y
        dist_to_goal = math.hypot(goal_dx, goal_dy)
        angle_to_goal = math.atan2(goal_dy, goal_dx)
        angle_diff = (angle_to_goal - math.radians(self.robot.angle) + np.pi) % (2 * np.pi) - np.pi
        obs = np.concatenate([
            np.array([dist_to_goal / LIDAR_MAX_DISTANCE, angle_diff / np.pi], dtype=np.float32),
            np.array(self._get_lidar_distances(), dtype=np.float32) / LIDAR_MAX_DISTANCE])
        return np.clip(obs, -1.0, 1.0)

    def _get_info(self):
        return {"distance": math.hypot(self.goal_x - self.robot.x, self.goal_y - self.robot.y)}

    def _check_collision(self):
        if not (0 <= self.robot.x < WIDTH and 0 <= self.robot.y < HEIGHT): return True
        all_obs = self.wall_obstacles + self.obstacles + self.dynamic_obstacles
        return any(self.robot.get_rect().colliderect(obs.rect) for obs in all_obs if obs.visible)

    def _check_goal(self, position_margin=15, angle_margin=20):
        is_pos_ok = math.hypot(self.goal_x - self.robot.x, self.goal_y - self.robot.y) < position_margin
        angle_diff = abs((self.robot.angle - self.goal_angle + 180) % 360 - 180)
        is_angle_ok = angle_diff <= angle_margin
        return is_angle_ok if self.mode == "Step_0" else is_pos_ok and is_angle_ok

    def _get_lidar_distances(self):
        distances, all_obs = [LIDAR_MAX_DISTANCE] * LIDAR_RESOLUTION, self.wall_obstacles + self.obstacles + self.dynamic_obstacles
        for i, delta_angle in enumerate(range(LIDAR_ANGLE_MIN, LIDAR_ANGLE_MAX + 1, LIDAR_STEP)):
            rad = math.radians(self.robot.angle + delta_angle)
            for dist in range(1, LIDAR_MAX_DISTANCE, 2):
                x, y = self.robot.x + dist * math.cos(rad), self.robot.y + dist * math.sin(rad)
                if not (0 <= x < WIDTH and 0 <= y < HEIGHT): distances[i] = dist; break
                if any(obs.rect.collidepoint(x, y) for obs in all_obs if obs.visible): distances[i] = dist; break
        return distances

    def _draw_goal_with_direction(self):
        if self.screen:
            pygame.draw.circle(self.screen, GOAL_COLOR, (int(self.goal_x), int(self.goal_y)), 10)
            rad = math.radians(self.goal_angle)
            end_x = int(self.goal_x + 30 * math.cos(rad)); end_y = int(self.goal_y + 30 * math.sin(rad))
            pygame.draw.line(self.screen, (255, 0, 0), (self.goal_x, self.goal_y), (end_x, end_y), 4)

    def _draw_lidar(self, distances):
        if self.screen:
            for i, dist in enumerate(distances):
                angle = math.radians(self.robot.angle + LIDAR_ANGLE_MIN + i * LIDAR_STEP)
                end_x = self.robot.x + dist * math.cos(angle); end_y = self.robot.y + dist * math.sin(angle)
                pygame.draw.line(self.screen, LIDAR_COLOR, (self.robot.x, self.robot.y), (end_x, end_y), 1)

    def _find_safe_spawn(self, avoid_rects):
        for _ in range(1000):
            x, y = random.randint(ROBOT_RADIUS + 1, WIDTH - ROBOT_RADIUS - 1), random.randint(ROBOT_RADIUS + 1, HEIGHT - ROBOT_RADIUS - 1)
            if not any(pygame.Rect(x - ROBOT_RADIUS, y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2).colliderect(r) for r in avoid_rects): return x, y
        raise Exception("安全なスポーン位置が見つかりません。")

    def _get_random_obstacle(self, avoid_rects, is_dynamic=False, cls_list=None):
        if cls_list is None: cls_list = [SlowBouncingObstacle, AppearingObstacle, CircularObstacle] if is_dynamic else [Obstacle]
        for _ in range(100):
            w, h, x, y = random.randint(30, 60), random.randint(30, 60), random.randint(0, WIDTH - 60), random.randint(0, HEIGHT - 60)
            rect = pygame.Rect(x, y, w, h)
            if not any(rect.colliderect(ar) for ar in avoid_rects):
                avoid_rects.append(rect); return random.choice(cls_list)(x, y, w, h)
        raise Exception("安全な障害物設置位置が見つかりません。")
    
    def _generate_walls(self, door_len):
        walls, thick = [], self.wall_thick
        W, H = WIDTH, HEIGHT
        walls.extend([Obstacle(0,0,W,thick), Obstacle(0,H-thick,W,thick), Obstacle(0,0,thick,H), Obstacle(W-thick,0,thick,H)])
        walls.extend([Obstacle(0, H//2 - thick//2, W, thick), Obstacle(W//2 - thick//2, 0, thick, H)])
        return walls