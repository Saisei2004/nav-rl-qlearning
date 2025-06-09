import pygame
import random
import math
import numpy as np
""
WIDTH, HEIGHT = 1000, 800
FPS = 120
ROBOT_RADIUS = 15
WHEEL_BASE = 30

WHITE = (255, 255, 255)
ROBOT_COLOR = (0, 200, 255)
GOAL_COLOR = (0, 255, 0)
WALL_COLOR = (100, 100, 100)
DIRECTION_COLOR = (0, 0, 255)

LIDAR_STEP = 2  # 線の本数を半分に！
LIDAR_ANGLE_MIN = -90
LIDAR_ANGLE_MAX = 90
LIDAR_RESOLUTION = ((LIDAR_ANGLE_MAX - LIDAR_ANGLE_MIN) // LIDAR_STEP) + 1
LIDAR_MAX_DISTANCE = 300  # 最大検出距離


GAME_WIDTH = 1000
GAME_HEIGHT = 800
LIDAR_WIDTH = 0
WIDTH = GAME_WIDTH + LIDAR_WIDTH
HEIGHT = GAME_HEIGHT

class Obstacle:
    def __init__(self, x, y, w, h, color=WALL_COLOR):
        self.rect = pygame.Rect(x, y, w, h)
        self.visible = True
        self.color = color
#
    def update(self): pass

    def draw(self, screen):
        if self.visible:
            pygame.draw.rect(screen, self.color, self.rect)
        # step_text = self.font.render(f"Step: {self.step_count}", True, (0, 0, 0))
        # self.screen.blit(step_text, (10, 10))  # 左上に表示（座標はお好みで）
        # pygame.display.flip()

class SlowBouncingObstacle(Obstacle):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, color=(180, 120, 60))
        # 速度はゆっくり
        self.vx = random.choice([-1, 1])
        self.vy = random.choice([-1, 1])

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        # 壁や画面端で反射
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.vx *= -1
        if self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.vy *= -1

class AppearingObstacle(Obstacle):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, color=(120, 80, 200))
        self.visible = True
        self.timer = 0
        self.show_time = random.randint(60, 150)   # 表示時間（フレーム）
        self.hide_time = random.randint(60, 150)   # 非表示時間（フレーム）

    def update(self):
        self.timer += 1
        if self.visible and self.timer >= self.show_time:
            self.visible = False
            self.timer = 0
            # 次の非表示期間をランダムに
            self.hide_time = random.randint(60, 150)
        elif not self.visible and self.timer >= self.hide_time:
            self.visible = True
            self.timer = 0
            # 次の表示期間をランダムに
            self.show_time = random.randint(60, 150)

class CircularObstacle(Obstacle):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, color=(60, 180, 120))
        self.center_x = x + w // 2
        self.center_y = y + h // 2
        self.radius = 30  # 円運動の半径
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = 0.03  # 円運動の角速度

    def update(self):
        self.angle += self.speed
        self.rect.x = int(self.center_x + self.radius * math.cos(self.angle) - self.rect.width // 2)
        self.rect.y = int(self.center_y + self.radius * math.sin(self.angle) - self.rect.height // 2)


class BlinkingObstacle(Obstacle):
    def __init__(self, x, y, w, h, color=WALL_COLOR):
        super().__init__(x, y, w, h, color)
        self.blink_timer = random.randint(200, 500)
        self.counter = 0

    def update(self):
        self.counter += 1
        if self.counter >= self.blink_timer:
            if random.random() < 1/3:
                self.visible = not self.visible
            self.counter = 0

class Robot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0

    def update(self, v_left, v_right):
        v = (v_left + v_right) / 2
        omega = (v_right - v_left) / WHEEL_BASE
        rad = math.radians(self.angle)
        self.x += v * math.cos(rad)
        self.y += v * math.sin(rad)
        self.angle += math.degrees(omega)

    def draw(self, screen):
        rad = math.radians(self.angle)
        tip = (self.x + ROBOT_RADIUS * math.cos(rad), self.y + ROBOT_RADIUS * math.sin(rad))
        left = (self.x + ROBOT_RADIUS * math.cos(math.radians(self.angle + 120)),
                self.y + ROBOT_RADIUS * math.sin(math.radians(self.angle + 120)))
        right = (self.x + ROBOT_RADIUS * math.cos(math.radians(self.angle - 120)),
                 self.y + ROBOT_RADIUS * math.sin(math.radians(self.angle - 120)))
        pygame.draw.polygon(screen, ROBOT_COLOR, [tip, left, right])
        dot_x = self.x + (ROBOT_RADIUS + 5) * math.cos(rad)
        dot_y = self.y + (ROBOT_RADIUS + 5) * math.sin(rad)
        pygame.draw.circle(screen, DIRECTION_COLOR, (int(dot_x), int(dot_y)), 3)

    def get_rect(self):
        return pygame.Rect(self.x - ROBOT_RADIUS, self.y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2)

class Game:
    def __init__(self, obstacle_count=10, mode="normal"):
        pygame.init()
        self.mode = mode
        self.lidar_log_counter = 0 
        self.step_count = 0
        pygame.font.init()
        self.font = pygame.font.SysFont("sans-serif", 28)

        self.screen = pygame.display.set_mode((GAME_WIDTH + LIDAR_WIDTH, GAME_HEIGHT))
#qww
        pygame.display.set_caption("差動駆動ロボット")
        self.clock = pygame.time.Clock()
        self.running = True
        if mode == "Step_0":
            self.setup_step_0()
        elif self.mode == "Step_1":
            self.wall_obstacles = []
            self.blinking_doors = []
            avoid_rects = []
            # ロボットの初期位置は画面中央
            self.robot = Robot(WIDTH // 2, HEIGHT // 2)
            # ゴールはロボットの向きに150ピクセル進んだところに置く
            goal_distance = 50
            angle_rad = math.radians(self.robot.angle)  # デフォルトで0度=右向き
            gx = int(self.robot.x + goal_distance * math.cos(angle_rad))
            gy = int(self.robot.y + goal_distance * math.sin(angle_rad))
            # 画面外にはみ出さないように
            self.goal_x = max(30, min(WIDTH - 30, gx))
            self.goal_y = max(30, min(HEIGHT - 30, gy))
            self.goal_angle = random.randint(0, 359)
            self.obstacles = []
            self.dynamic_obstacles = []
        elif self.mode == "Step_2":
            # Step_2：ゴールがマップ上のランダムな場所
            self.wall_obstacles = []
            self.blinking_doors = []
            avoid_rects = []
            # ロボット初期位置は画面中央
            self.robot = Robot(WIDTH // 2, HEIGHT // 2)
            # ゴールはマップ上のランダムな位置（画面端に寄りすぎないように調整）
            self.goal_x = random.randint(40, WIDTH - 40)
            self.goal_y = random.randint(40, HEIGHT - 40)
            self.goal_angle = random.randint(0, 359)
            self.obstacles = []
            self.dynamic_obstacles = []
        elif self.mode == "Step_3":
            # Step_3: ランダムなゴール位置、ランダムな障害物5個
            self.wall_obstacles = []
            self.blinking_doors = []
            avoid_rects = []

            # ロボット初期位置（画面中央）
            self.robot = Robot(WIDTH // 2, HEIGHT // 2)
            avoid_rects.append(pygame.Rect(self.robot.x - ROBOT_RADIUS, self.robot.y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2))

            # ゴールをランダムに配置（画面端に寄りすぎないように）
            self.goal_x = random.randint(40, WIDTH - 40)
            self.goal_y = random.randint(40, HEIGHT - 40)
            self.goal_angle = random.randint(0, 359)
            # ゴールの範囲もavoidに追加
            avoid_rects.append(pygame.Rect(self.goal_x - 20, self.goal_y - 20, 40, 40))

            # ランダムな障害物5個を配置（ロボットやゴールに重ならないように）
            self.obstacles = []
            for _ in range(5):
                for _ in range(100):  # 100回までトライして被らない位置を探す
                    x = random.randint(0, WIDTH - 60)
                    y = random.randint(0, HEIGHT - 60)
                    w = random.randint(30, 60)
                    h = random.randint(30, 60)
                    rect = pygame.Rect(x, y, w, h)
                    if not any(rect.colliderect(ar) for ar in avoid_rects):
                        self.obstacles.append(Obstacle(x, y, w, h))
                        avoid_rects.append(rect)
                        break

            self.dynamic_obstacles = []  # 動的障害物はなし

        elif self.mode == "Step_4":
            # Step_4：ランダムなゴール＋ランダムな障害物15個
            self.wall_obstacles = []
            self.blinking_doors = []
            avoid_rects = []

            # ロボットの初期位置（中央固定）
            self.robot = Robot(WIDTH // 2, HEIGHT // 2)
            avoid_rects.append(pygame.Rect(self.robot.x - ROBOT_RADIUS, self.robot.y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2))

            # ゴールをランダム配置
            self.goal_x = random.randint(40, WIDTH - 40)
            self.goal_y = random.randint(40, HEIGHT - 40)
            self.goal_angle = random.randint(0, 359)
            avoid_rects.append(pygame.Rect(self.goal_x - 20, self.goal_y - 20, 40, 40))

            # 障害物15個を、ロボットやゴールと重ならない場所に設置
            self.obstacles = []
            for _ in range(20):
                for _ in range(100):  # 最大100回試す
                    x = random.randint(0, WIDTH - 60)
                    y = random.randint(0, HEIGHT - 60)
                    w = random.randint(30, 60)
                    h = random.randint(30, 60)
                    rect = pygame.Rect(x, y, w, h)
                    if not any(rect.colliderect(ar) for ar in avoid_rects):
                        self.obstacles.append(Obstacle(x, y, w, h))
                        avoid_rects.append(rect)
                        break

            self.dynamic_obstacles = []

        elif self.mode == "Step_5":
            self.wall_thick = 8
            self.wall_obstacles = self.generate_walls_and_double_big_doors(door_len=200)
            self.blinking_doors = []

            avoid_rects = [w.rect for w in self.wall_obstacles]

            # ロボットの初期位置をランダムに（壁に重ならないようにする）
            for _ in range(1000):
                x = random.randint(ROBOT_RADIUS + 1, WIDTH - ROBOT_RADIUS - 1)
                y = random.randint(ROBOT_RADIUS + 1, HEIGHT - ROBOT_RADIUS - 1)
                spawn_rect = pygame.Rect(x - ROBOT_RADIUS, y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2)
                if not any(spawn_rect.colliderect(rect) for rect in avoid_rects):
                    self.robot = Robot(x, y)
                    avoid_rects.append(spawn_rect)
                    break
            else:
                raise Exception("ロボットの安全な初期位置が確保できません。")

            # ゴールをランダム配置（壁・ロボットと重ならない場所）
            for _ in range(1000):
                gx = random.randint(40, WIDTH - 40)
                gy = random.randint(40, HEIGHT - 40)
                goal_rect = pygame.Rect(gx - 20, gy - 20, 40, 40)
                if not any(goal_rect.colliderect(rect) for rect in avoid_rects):
                    self.goal_x = gx
                    self.goal_y = gy
                    avoid_rects.append(goal_rect)
                    break
            else:
                raise Exception("ゴールの安全な位置が確保できません。")

            self.goal_angle = random.randint(0, 359)
            self.obstacles = []
            self.dynamic_obstacles = []

        elif self.mode == "Step_6":
            self.wall_thick = 8
            self.wall_obstacles = self.generate_walls_and_double_big_doors(door_len=200)
            self.blinking_doors = []

            avoid_rects = [w.rect for w in self.wall_obstacles]

            # ロボットの初期位置をランダム（壁や障害物に重ならない場所）
            for _ in range(1000):
                x = random.randint(ROBOT_RADIUS + 1, WIDTH - ROBOT_RADIUS - 1)
                y = random.randint(ROBOT_RADIUS + 1, HEIGHT - ROBOT_RADIUS - 1)
                spawn_rect = pygame.Rect(x - ROBOT_RADIUS, y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2)
                if not any(spawn_rect.colliderect(rect) for rect in avoid_rects):
                    self.robot = Robot(x, y)
                    avoid_rects.append(spawn_rect)
                    break
            else:
                raise Exception("ロボットの安全な初期位置が確保できません。")

            # ゴールをランダムに配置（壁やロボットに重ならない場所）
            for _ in range(1000):
                gx = random.randint(40, WIDTH - 40)
                gy = random.randint(40, HEIGHT - 40)
                goal_rect = pygame.Rect(gx - 20, gy - 20, 40, 40)
                if not any(goal_rect.colliderect(rect) for rect in avoid_rects):
                    self.goal_x = gx
                    self.goal_y = gy
                    avoid_rects.append(goal_rect)
                    break
            else:
                raise Exception("ゴールの安全な位置が確保できません。")

            self.goal_angle = random.randint(0, 359)

            # ランダムな障害物（3〜10個）
            num_obs = random.randint(3, 10)
            self.obstacles = []
            for _ in range(num_obs):
                for _ in range(100):
                    x = random.randint(0, WIDTH - 60)
                    y = random.randint(0, HEIGHT - 60)
                    w = random.randint(30, 60)
                    h = random.randint(30, 60)
                    rect = pygame.Rect(x, y, w, h)
                    if not any(rect.colliderect(ar) for ar in avoid_rects):
                        self.obstacles.append(Obstacle(x, y, w, h))
                        avoid_rects.append(rect)
                        break
            self.dynamic_obstacles = []
            for _ in range(3):
                for _ in range(100):
                    x = random.randint(50, WIDTH - 90)
                    y = random.randint(50, HEIGHT - 90)
                    w = random.randint(30, 60)
                    h = random.randint(30, 60)
                    rect = pygame.Rect(x, y, w, h)
                    if not any(rect.colliderect(ar) for ar in avoid_rects):
                        self.dynamic_obstacles.append(CircularObstacle(x, y, w, h))
                        avoid_rects.append(rect)
                        break

            

        elif self.mode == "Step_7":
            self.room_w = WIDTH // 2
            self.room_h = HEIGHT // 2
            self.wall_thick = 8
            self.door_len = 60  # 本来のドアサイズ

            # 4部屋
            self.rooms = [
                pygame.Rect(0, 0, self.room_w, self.room_h),  # 左上
                pygame.Rect(self.room_w, 0, self.room_w, self.room_h),  # 右上
                pygame.Rect(0, self.room_h, self.room_w, self.room_h),  # 左下
                pygame.Rect(self.room_w, self.room_h, self.room_w, self.room_h)  # 右下
            ]

            # 壁とドアの生成
            self.wall_obstacles = self.generate_walls_and_double_big_doors(door_len=60)
            self.blinking_doors = []  # 今回は使わない

            # プレイヤーの初期位置（壁に被らないランダム）
            avoid_rects = [w.rect for w in self.wall_obstacles]
            x, y = self.find_safe_spawn(avoid_rects)
            self.robot = Robot(x, y)
            avoid_rects.append(pygame.Rect(x - ROBOT_RADIUS, y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2))

            # ゴールの初期位置（壁とロボットに被らないランダム）
            self.goal_x, self.goal_y = self.find_safe_spawn(avoid_rects)
            self.goal_angle = random.randint(0, 359)
            avoid_rects.append(pygame.Rect(self.goal_x - 20, self.goal_y - 20, 40, 40))

            # 障害物3～7個（ランダム個数で生成）
            obstacle_count = random.randint(3, 10)
            self.obstacles = self.generate_static_obstacles(obstacle_count, avoid_rects)
            self.dynamic_obstacles = []  # 今回は使わない
            for _ in range(2):
                for _ in range(100):
                    x = random.randint(50, WIDTH - 90)
                    y = random.randint(50, HEIGHT - 90)
                    w = random.randint(30, 60)
                    h = random.randint(30, 60)
                    rect = pygame.Rect(x, y, w, h)
                    if not any(rect.colliderect(ar) for ar in avoid_rects):
                        self.dynamic_obstacles.append(AppearingObstacle(x, y, w, h))
                        avoid_rects.append(rect)
                        break

            # ドアが動的ならこの辺の記述が必要ですが今回は空
            unique_door_list = self.generate_unique_doors()
            random.shuffle(unique_door_list)
            num_blink = max(1, len(unique_door_list) // 3)
            self.blinking_doors = [BlinkingObstacle(*d) for d in unique_door_list[:num_blink]]
            self.open_doors = unique_door_list[num_blink:]

        elif self.mode == "Step_8":
            self.wall_thick = 8
            # ドアの大きさは必要に応じて変更（例：中くらいのドア長さ100）
            self.wall_obstacles = self.generate_walls_and_double_big_doors(door_len=100)
            self.blinking_doors = []

            avoid_rects = [w.rect for w in self.wall_obstacles]

            # スタート位置ランダム
            for _ in range(1000):
                x = random.randint(ROBOT_RADIUS + 1, WIDTH - ROBOT_RADIUS - 1)
                y = random.randint(ROBOT_RADIUS + 1, HEIGHT - ROBOT_RADIUS - 1)
                spawn_rect = pygame.Rect(x - ROBOT_RADIUS, y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2)
                if not any(spawn_rect.colliderect(rect) for rect in avoid_rects):
                    self.robot = Robot(x, y)
                    avoid_rects.append(spawn_rect)
                    break
            else:
                raise Exception("ロボットの安全な初期位置が確保できません。")

            # ゴール位置ランダム
            for _ in range(1000):
                gx = random.randint(40, WIDTH - 40)
                gy = random.randint(40, HEIGHT - 40)
                goal_rect = pygame.Rect(gx - 20, gy - 20, 40, 40)
                if not any(goal_rect.colliderect(rect) for rect in avoid_rects):
                    self.goal_x = gx
                    self.goal_y = gy
                    avoid_rects.append(goal_rect)
                    break
            else:
                raise Exception("ゴールの安全な位置が確保できません。")

            self.goal_angle = random.randint(0, 359)

            # 動的障害物（ランダムなクラスを混ぜて3～7個）
            num_dynamic = random.randint(3, 7)
            dynamic_classes = [SlowBouncingObstacle, AppearingObstacle, CircularObstacle]
            self.dynamic_obstacles = []
            for _ in range(num_dynamic):
                for _ in range(100):
                    x = random.randint(50, WIDTH - 90)
                    y = random.randint(50, HEIGHT - 90)
                    w = random.randint(30, 60)
                    h = random.randint(30, 60)
                    rect = pygame.Rect(x, y, w, h)
                    if not any(rect.colliderect(ar) for ar in avoid_rects):
                        cls = random.choice(dynamic_classes)
                        self.dynamic_obstacles.append(cls(x, y, w, h))
                        avoid_rects.append(rect)
                        break

            self.obstacles = []  # 静的障害物は無し or ここで個数指定すればOK


        else:
            self.room_w = WIDTH // 2
            self.room_h = HEIGHT // 2
            self.wall_thick = 8
            self.door_len = 60
            

            # 4部屋
            self.rooms = [
                pygame.Rect(0, 0, self.room_w, self.room_h),  # 左上
                pygame.Rect(self.room_w, 0, self.room_w, self.room_h),  # 右上
                pygame.Rect(0, self.room_h, self.room_w, self.room_h),  # 左下
                pygame.Rect(self.room_w, self.room_h, self.room_w, self.room_h)  # 右下
            ]

            # すべての壁と独立ドアをリストで管理
            # すべての壁（開口含む）をリストで管理
            self.wall_obstacles = self.generate_walls_and_double_big_doors(door_len=60)
            # ↓ドア開閉関連（door_candidates, blinking_doors）は全て不要
            self.blinking_doors = []  # 空リストでOK

            # プレイヤーの初期位置
            avoid_rects = [w.rect for w in self.wall_obstacles] + [b.rect for b in self.blinking_doors if b.visible]
            x, y = self.find_safe_spawn(avoid_rects)
            self.robot = Robot(x, y)
            # ゴール
            avoid_rects.append(pygame.Rect(x - ROBOT_RADIUS, y - ROBOT_RADIUS, ROBOT_RADIUS*2, ROBOT_RADIUS*2))
            self.goal_x, self.goal_y = self.find_safe_spawn(avoid_rects)
            self.goal_angle = random.randint(0, 359)
            avoid_rects.append(pygame.Rect(self.goal_x - 20, self.goal_y - 20, 40, 40))
            self.obstacles = self.generate_static_obstacles(obstacle_count, avoid_rects)
            self.dynamic_obstacles = self.generate_dynamic_obstacles(avoid_rects)
                    # --- __init__などで ---
            unique_door_list = self.generate_unique_doors()
            random.shuffle(unique_door_list)
            num_blink = max(1, len(unique_door_list) // 3)
            self.blinking_doors = [BlinkingObstacle(*d) for d in unique_door_list[:num_blink]]
            self.open_doors = unique_door_list[num_blink:]
        self.goal_direction = self.calc_goal_direction()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.lidar_surface = pygame.Surface((400, 400))

    def setup_step_0(self):
        # スタート座標をランダムに決める（または中央などでもOK）
        x = random.randint(ROBOT_RADIUS + 1, WIDTH - ROBOT_RADIUS - 1)
        y = random.randint(ROBOT_RADIUS + 1, HEIGHT - ROBOT_RADIUS - 1)
        # プレイヤーの初期向きをランダム（0~359）
        start_angle = random.randint(0, 359)
        self.robot = Robot(x, y)
        self.robot.angle = start_angle

        # ゴールの座標はプレイヤーと同じ
        self.goal_x = x
        self.goal_y = y

        # ゴールの向きは、プレイヤーの向きから±40度以上ずれたランダムな角度
        while True:
            goal_angle = random.randint(0, 359)
            diff = abs((goal_angle - start_angle + 180) % 360 - 180)
            if diff >= 40:
                break
        self.goal_angle = goal_angle

        # 壁・障害物はなし
        self.wall_obstacles = []
        self.blinking_doors = []
        self.obstacles = []
        self.dynamic_obstacles = []


    def get_lidar_distances(self):
        distances = []
        px, py = self.robot.x, self.robot.y
        base_angle = self.robot.angle  # ロボットの角度（0度が正面）

        for delta_angle in range(LIDAR_ANGLE_MIN, LIDAR_ANGLE_MAX+1, LIDAR_STEP):
            angle = base_angle + delta_angle
            rad = math.radians(angle)
            for dist in range(1, LIDAR_MAX_DISTANCE, 2):  # 2px間隔でサンプリング
                x = int(px + dist * math.cos(rad))
                y = int(py + dist * math.sin(rad))
                point_rect = pygame.Rect(x, y, 2, 2)
                collision = False
                for obs in self.wall_obstacles + self.blinking_doors + self.obstacles + self.dynamic_obstacles:
                    if obs.visible and obs.rect.colliderect(point_rect):
                        collision = True
                        break
                if collision:
                    break
            distances.append(dist if collision else LIDAR_MAX_DISTANCE)
        return distances
    
    def calc_goal_direction(self):
        # ゴールの向きを0～359度で算出（真上0度、時計回り）
        dx = self.goal_x - self.robot.x
        dy = self.goal_y - self.robot.y
        angle = math.degrees(math.atan2(dx, -dy)) % 360  # 真上0度に合わせるためdyとdxを逆
        return int(angle)



    def log_status(self, v_left, v_right):
        # ログ出力用メソッド
        x = round(self.robot.x, 2)
        y = round(self.robot.y, 2)
        gx = self.goal_x
        gy = self.goal_y
        dist = round(math.hypot(gx - x, gy - y), 2)
        robot_angle = int(self.robot.angle) % 360
        goal_dir = self.calc_goal_direction()
        print(f"座標=({x}, {y}) | ゴール=({gx}, {gy}) | 距離={dist} | 向き={robot_angle}° | ゴール方向={goal_dir}° | v_left={v_left}, v_right={v_right}")

    def generate_walls_and_big_doors(self):
        wall_obs = []
        # ドア幅を大きくする（例：200ピクセル）
        big_door_len = 200

        # 上側壁（中央に大きなドア）
        upper_door_x = WIDTH // 2
        wall_obs.append(Obstacle(0, 0, upper_door_x - big_door_len // 2, self.wall_thick))
        wall_obs.append(Obstacle(upper_door_x + big_door_len // 2, 0, WIDTH - (upper_door_x + big_door_len // 2), self.wall_thick))

        # 下側壁（中央に大きなドア）
        wall_obs.append(Obstacle(0, HEIGHT - self.wall_thick, upper_door_x - big_door_len // 2, self.wall_thick))
        wall_obs.append(Obstacle(upper_door_x + big_door_len // 2, HEIGHT - self.wall_thick, WIDTH - (upper_door_x + big_door_len // 2), self.wall_thick))

        # 左側壁（中央に大きなドア）
        left_door_y = HEIGHT // 2
        wall_obs.append(Obstacle(0, 0, self.wall_thick, left_door_y - big_door_len // 2))
        wall_obs.append(Obstacle(0, left_door_y + big_door_len // 2, self.wall_thick, HEIGHT - (left_door_y + big_door_len // 2)))

        # 右側壁（中央に大きなドア）
        wall_obs.append(Obstacle(WIDTH - self.wall_thick, 0, self.wall_thick, left_door_y - big_door_len // 2))
        wall_obs.append(Obstacle(WIDTH - self.wall_thick, left_door_y + big_door_len // 2, self.wall_thick, HEIGHT - (left_door_y + big_door_len // 2)))

        # 中央の縦壁（上下中央に1本・中央部に大きなドア）
        vert_x = WIDTH // 2 - self.wall_thick // 2
        vert_door_y = HEIGHT // 2
        wall_obs.append(Obstacle(vert_x, 0, self.wall_thick, vert_door_y - big_door_len // 2))
        wall_obs.append(Obstacle(vert_x, vert_door_y + big_door_len // 2, self.wall_thick, HEIGHT - (vert_door_y + big_door_len // 2)))

        # 中央の横壁（左右中央に1本・中央部に大きなドア）
        hori_y = HEIGHT // 2 - self.wall_thick // 2
        hori_door_x = WIDTH // 2
        wall_obs.append(Obstacle(0, hori_y, hori_door_x - big_door_len // 2, self.wall_thick))
        wall_obs.append(Obstacle(hori_door_x + big_door_len // 2, hori_y, WIDTH - (hori_door_x + big_door_len // 2), self.wall_thick))

        return wall_obs



    def generate_unique_doors(self):
        unique_doors = {}
        # for d in self.door_candidates:
        #     unique_doors[d] = None  # dは(x, y, w, h)のtuple
        return list(unique_doors.keys())

    def generate_walls_and_doors(self):
        wall_obs = []
        # --- 外周壁（上下左右：開口部あり） ---

        # 上側壁（真ん中にドア＝開口部）
        upper_door_x = GAME_WIDTH // 2
        door_len = 80
        wall_obs.append(Obstacle(0, 0, upper_door_x - door_len//2, self.wall_thick))
        wall_obs.append(Obstacle(upper_door_x + door_len//2, 0, GAME_WIDTH - (upper_door_x + door_len//2), self.wall_thick))

        # 下側壁（ここではドアなしで囲いたいなら従来通りでOK）
        wall_obs.append(Obstacle(0, GAME_HEIGHT - self.wall_thick, GAME_WIDTH, self.wall_thick))

        # 左側壁（ここではドアなしで囲いたいなら従来通りでOK）
        wall_obs.append(Obstacle(0, 0, self.wall_thick, GAME_HEIGHT))

        # 右側壁（真ん中にドア＝開口部）
        right_door_y = GAME_HEIGHT // 2
        wall_obs.append(Obstacle(GAME_WIDTH - self.wall_thick, 0, self.wall_thick, right_door_y - door_len//2))
        wall_obs.append(Obstacle(GAME_WIDTH - self.wall_thick, right_door_y + door_len//2, self.wall_thick, GAME_HEIGHT - (right_door_y + door_len//2)))

        # --- 中央の縦壁（開口ドア付き） ---
        vert_x = GAME_WIDTH // 2 - self.wall_thick // 2
        vert_door_y = GAME_HEIGHT // 4 * 3
        vert_door_len = 80
        wall_obs.append(Obstacle(vert_x, 0, self.wall_thick, vert_door_y - vert_door_len // 2))
        wall_obs.append(Obstacle(vert_x, vert_door_y + vert_door_len // 2, self.wall_thick, GAME_HEIGHT - (vert_door_y + vert_door_len // 2)))

        # --- 中央の横壁（開口ドア付き） ---
        hori_y = GAME_HEIGHT // 2 - self.wall_thick // 2
        hori_door_x = GAME_WIDTH // 4
        hori_door_len = 80
        wall_obs.append(Obstacle(0, hori_y, hori_door_x - hori_door_len // 2, self.wall_thick))
        wall_obs.append(Obstacle(hori_door_x + hori_door_len // 2, hori_y, GAME_WIDTH - (hori_door_x + hori_door_len // 2), self.wall_thick))

        return wall_obs

    def generate_walls_and_double_big_doors(self, door_len=200):
        wall_obs = []
        thick = self.wall_thick
        W, H = WIDTH, HEIGHT

        # --- 外周壁 ---
        # 上壁
        wall_obs.append(Obstacle(0, 0, W//2 - door_len//2, thick))
        wall_obs.append(Obstacle(W//2 + door_len//2, 0, W//2 - door_len//2, thick))
        # 下壁
        wall_obs.append(Obstacle(0, H-thick, W//2 - door_len//2, thick))
        wall_obs.append(Obstacle(W//2 + door_len//2, H-thick, W//2 - door_len//2, thick))
        # 左壁
        wall_obs.append(Obstacle(0, 0, thick, H//2 - door_len//2))
        wall_obs.append(Obstacle(0, H//2 + door_len//2, thick, H//2 - door_len//2))
        # 右壁
        wall_obs.append(Obstacle(W-thick, 0, thick, H//2 - door_len//2))
        wall_obs.append(Obstacle(W-thick, H//2 + door_len//2, thick, H//2 - door_len//2))

        # --- 中央の縦壁 ---
        vert_x = W//2 - thick//2
        # 上半分
        wall_obs.append(Obstacle(vert_x, 0, thick, H//4 - door_len//2))
        wall_obs.append(Obstacle(vert_x, H//4 + door_len//2, thick, H//4 - door_len//2))
        # 下半分
        wall_obs.append(Obstacle(vert_x, H//2, thick, H//4 - door_len//2))
        wall_obs.append(Obstacle(vert_x, H*3//4 + door_len//2, thick, H//4 - door_len//2))

        # --- 中央の横壁 ---
        hori_y = H//2 - thick//2
        # 左半分
        wall_obs.append(Obstacle(0, hori_y, W//4 - door_len//2, thick))
        wall_obs.append(Obstacle(W//4 + door_len//2, hori_y, W//4 - door_len//2, thick))
        # 右半分
        wall_obs.append(Obstacle(W//2, hori_y, W//4 - door_len//2, thick))
        wall_obs.append(Obstacle(W*3//4 + door_len//2, hori_y, W//4 - door_len//2, thick))

        return wall_obs


    def generate_independent_room_walls_and_doors(self):
        wall_obs = []
        door_candidates = []

        # 外周壁（4辺）
        wall_obs.append(Obstacle(0, 0, GAME_WIDTH, self.wall_thick))
        wall_obs.append(Obstacle(0, GAME_HEIGHT - self.wall_thick, GAME_WIDTH, self.wall_thick))
        wall_obs.append(Obstacle(0, 0, self.wall_thick, GAME_HEIGHT))
        wall_obs.append(Obstacle(GAME_WIDTH - self.wall_thick, 0, self.wall_thick, GAME_HEIGHT))

        # ★中央の縦壁（左右中央に1本）
        wall_obs.append(Obstacle(GAME_WIDTH // 2 - self.wall_thick // 2, 0, self.wall_thick, GAME_HEIGHT))
        # ★中央の横壁（上下中央に1本）
        wall_obs.append(Obstacle(0, GAME_HEIGHT // 2 - self.wall_thick // 2, GAME_WIDTH, self.wall_thick))

        # 必要ならドアも中央壁の任意の位置に作成（片側だけでOK、もしくはドア情報のみ登録）
        # ...（ドア処理は元のやり方を参考にする）...

        return wall_obs, door_candidates

    def find_safe_spawn(self, avoid_rects, max_trials=1000):
        for _ in range(max_trials):
            x = random.randint(ROBOT_RADIUS + 1, WIDTH - ROBOT_RADIUS - 1)
            y = random.randint(ROBOT_RADIUS + 1, HEIGHT - ROBOT_RADIUS - 1)
            spawn_rect = pygame.Rect(x - ROBOT_RADIUS, y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2)
            if not any(spawn_rect.colliderect(rect) for rect in avoid_rects):
                return x, y
        raise Exception("ロボットの安全な初期位置が確保できません。")

    def generate_static_obstacles(self, count, avoid_rects):
        obstacles = []
        for _ in range(count):
            for _ in range(100):
                x = random.randint(0, WIDTH - 60)
                y = random.randint(0, HEIGHT - 60)
                w = random.randint(30, 60)
                h = random.randint(30, 60)
                rect = pygame.Rect(x, y, w, h)
                # 壁・ゴール・ロボット・他障害物禁止
                near_normal = any(rect.colliderect(ar) for ar in avoid_rects)
                if not near_normal:
                    obstacles.append(Obstacle(x, y, w, h))
                    avoid_rects.append(rect)
                    break
        return obstacles

    
    def generate_dynamic_obstacles(self, avoid_rects):
        classes = [SlowBouncingObstacle, AppearingObstacle, CircularObstacle]
        count = random.randint(2, 5)
        obstacles = []
        for _ in range(count):
            cls = random.choice(classes)
            for _ in range(100):
                x = random.randint(50, WIDTH - 90)
                y = random.randint(50, HEIGHT - 90)
                w = random.randint(30, 60)
                h = random.randint(30, 60)
                rect = pygame.Rect(x, y, w, h)
                near = any(rect.colliderect(ar) for ar in avoid_rects)
                if not near:
                    obstacles.append(cls(x, y, w, h))
                    avoid_rects.append(rect)
                    break
        return obstacles


    def get_tire_speed(self, keys):
        v_right = 0
        if keys[pygame.K_1]: v_right = 4
        elif keys[pygame.K_q]: v_right = 2
        elif keys[pygame.K_a]: v_right = -2
        elif keys[pygame.K_z]: v_right = -4
        v_left = 0
        if keys[pygame.K_2]: v_left = 4
        elif keys[pygame.K_w]: v_left = 2
        elif keys[pygame.K_s]: v_left = -2
        elif keys[pygame.K_x]: v_left = -4
        return v_left, v_right

    def check_collision(self):
        rect = self.robot.get_rect()
        for obs in self.wall_obstacles + self.blinking_doors + self.obstacles + self.dynamic_obstacles:
            if obs.visible and rect.colliderect(obs.rect):
                return True
        return False

    def check_goal(self, margin=20):
        # marginは「許容する角度の幅」（デフォルト20度など）
        robot_angle = int(self.robot.angle) % 360
        goal_angle = int(self.goal_angle) % 360
        angle_diff = abs((robot_angle - goal_angle + 180) % 360 - 180)
        # 位置の距離
        distance = math.hypot(self.goal_x - self.robot.x, self.goal_y - self.robot.y)
        return distance < ROBOT_RADIUS + 10 and angle_diff <= margin

    def draw_goal_with_direction(self):
        # ゴールの円を描画
        pygame.draw.circle(self.screen, GOAL_COLOR, (self.goal_x, self.goal_y), 10)
        # ゴール向きの矢印を描画
        length = 30  # 矢印の長さ
        rad = math.radians(self.goal_angle)
        end_x = int(self.goal_x + length * math.cos(rad))
        end_y = int(self.goal_y + length * math.sin(rad))
        pygame.draw.line(self.screen, (255, 0, 0), (self.goal_x, self.goal_y), (end_x, end_y), 4)
        # 矢印の先端（三角形のようなものを描くなら下記）
        head_length = 8
        left_rad = rad + math.radians(150)
        right_rad = rad - math.radians(150)
        left = (int(end_x + head_length * math.cos(left_rad)), int(end_y + head_length * math.sin(left_rad)))
        right = (int(end_x + head_length * math.cos(right_rad)), int(end_y + head_length * math.sin(right_rad)))
        pygame.draw.polygon(self.screen, (255, 0, 0), [(end_x, end_y), left, right])

    def draw_lidar(self, distances):
        px = int(self.robot.x)
        py = int(self.robot.y)
        base_angle = self.robot.angle
        for idx, delta_angle in enumerate(range(LIDAR_ANGLE_MIN, LIDAR_ANGLE_MAX+1, LIDAR_STEP)):
            angle = base_angle + delta_angle
            rad = math.radians(angle)
            dist = distances[idx]
            x = int(px + dist * math.cos(rad))
            y = int(py + dist * math.sin(rad))
            pygame.draw.line(self.screen, (0,200,100), (px, py), (x, y), 1)
        pygame.draw.circle(self.screen, (60,60,255), (px, py), 4)
    
    def draw(self):
        # --- ゲーム画面エリア（左） ---
        self.screen.fill(WHITE, rect=pygame.Rect(0, 0, GAME_WIDTH, GAME_HEIGHT))
        for wall in self.wall_obstacles:
            wall.draw(self.screen)
        for door in self.blinking_doors:
            door.update()
            door.draw(self.screen)
        for obs in self.obstacles + self.dynamic_obstacles:
            obs.draw(self.screen)
        self.robot.draw(self.screen)
        self.draw_goal_with_direction()
        step_text = self.font.render(f"Step: {self.step_count}", True, (0, 0, 0))
        self.screen.blit(step_text, (10, 10))
        # --- ライダー可視化エリア（右） ---
        lidar_distances = self.get_lidar_distances()
        self.draw_lidar(lidar_distances)

        pygame.display.flip()


    def run(self):
        while self.running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            keys = pygame.key.get_pressed()
            v_left, v_right = self.get_tire_speed(keys)
            self.robot.update(v_left, v_right)
            for obs in self.dynamic_obstacles:
                obs.update()

            # LIDAR取得と出力（ここを追加！）
            lidar_distances = self.get_lidar_distances()
            self.lidar_log_counter += 1
            if self.lidar_log_counter % 50 == 0:
                print(f"[LIDAR] {lidar_distances[:10]} ...（全{len(lidar_distances)}本）")  # 先頭10本＋総本数だけ表示

            # ログ出力
            self.log_status(v_left, v_right)
            if self.check_collision():
                print("💥 衝突しました！")
                self.running = False
            if self.check_goal():
                print("🎉 ゴール達成！（向きも条件OK）")
                self.running = False
            self.draw()
        pygame.quit()

    # def get_state(self):
    #     # 座標・向き
    #     x, y = self.robot.x, self.robot.y
    #     theta = self.robot.angle  # 0～360°

    #     # ゴールの相対座標
    #     goal_dx = self.goal_x - x
    #     goal_dy = self.goal_y - y

    #     # ゴールまでの距離と方向差
    #     goal_dist = math.hypot(goal_dx, goal_dy)
    #     goal_dir = math.degrees(math.atan2(goal_dx, -goal_dy)) % 360
    #     goal_dir_diff = (goal_dir - theta + 180) % 360 - 180

    #     # ライダー情報（np.arrayにすると学習が楽）
    #     lidar = np.array(self.get_lidar_distances()) / LIDAR_MAX_DISTANCE  # 0～1に正規化

    #     # 状態を1つのベクトルとして返す（例：numpy配列にまとめる）
    #     state = np.concatenate([
    #         np.array([goal_dist / LIDAR_MAX_DISTANCE, goal_dir_diff / 180]),  # 正規化
    #         lidar
    #     ])
    #     return state

    def reset(self):
    # ゲームを初期化し、初期状態を返す
        ...
        return self.get_state()
    
    def step(self, action):
        # action = (v_left, v_right) など
        self.robot.update(*action)
        for obs in self.dynamic_obstacles:
            obs.update()
        reward = -1 # 報酬関数を自作
        done = self.check_collision() or self.check_goal()
        state = self.get_state()
        info = {}  # 任意の追加情報
        self.step_count += 1
        return state, reward, done, info


if __name__ == "__main__":
    game = Game(obstacle_count=10, mode="Step_9")
    game.run()

