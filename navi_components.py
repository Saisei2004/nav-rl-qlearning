# navi_components.py (最終確定版)
import pygame
import random
import math

# --- 定数定義 ---
WIDTH, HEIGHT = 1000, 800
FPS = 120
ROBOT_RADIUS = 15
WHEEL_BASE = 30
WHITE = (255, 255, 255)
ROBOT_COLOR = (0, 200, 255)
GOAL_COLOR = (0, 255, 0)
WALL_COLOR = (100, 100, 100)
LIDAR_COLOR = (0, 200, 100)
DIRECTION_COLOR = (0, 0, 255)
LIDAR_STEP = 2
LIDAR_ANGLE_MIN = -90
LIDAR_ANGLE_MAX = 90
LIDAR_RESOLUTION = ((LIDAR_ANGLE_MAX - LIDAR_ANGLE_MIN) // LIDAR_STEP) + 1
LIDAR_MAX_DISTANCE = 300

# --- 部品クラス ---
class Obstacle:
    def __init__(self, x, y, w, h, color=WALL_COLOR):
        self.rect = pygame.Rect(x, y, w, h)
        self.visible = True
        self.color = color
    def update(self): pass
    def draw(self, screen):
        if self.visible:
            pygame.draw.rect(screen, self.color, self.rect)

class SlowBouncingObstacle(Obstacle):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, color=(180, 120, 60))
        self.vx = random.choice([-1, 1])
        self.vy = random.choice([-1, 1])
    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.left < 0 or self.rect.right > WIDTH: self.vx *= -1
        if self.rect.top < 0 or self.rect.bottom > HEIGHT: self.vy *= -1

class AppearingObstacle(Obstacle):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, color=(120, 80, 200))
        self.visible = True
        self.timer, self.show_time, self.hide_time = 0, random.randint(60, 150), random.randint(60, 150)
    def update(self):
        self.timer += 1
        if self.visible and self.timer >= self.show_time: self.visible, self.timer = False, 0
        elif not self.visible and self.timer >= self.hide_time: self.visible, self.timer = True, 0

class CircularObstacle(Obstacle):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, color=(60, 180, 120))
        self.center_x, self.center_y = x + w // 2, y + h // 2
        self.radius, self.angle, self.speed = 30, random.uniform(0, 2 * math.pi), 0.03
    def update(self):
        self.angle += self.speed
        self.rect.x = int(self.center_x + self.radius * math.cos(self.angle) - self.rect.width / 2)
        self.rect.y = int(self.center_y + self.radius * math.sin(self.angle) - self.rect.height / 2)

class Robot:
    def __init__(self, x, y, angle=0.0):
        self.x, self.y, self.angle = float(x), float(y), float(angle)
    def update(self, v_left, v_right):
        v = (v_left + v_right) / 2.0
        omega = (v_right - v_left) / WHEEL_BASE
        rad = math.radians(self.angle)
        self.x += v * math.cos(rad)
        self.y += v * math.sin(rad)
        self.angle = (self.angle + math.degrees(omega)) % 360
    def draw(self, screen):
        rad = math.radians(self.angle)
        tip = (self.x + ROBOT_RADIUS * math.cos(rad), self.y + ROBOT_RADIUS * math.sin(rad))
        left = (self.x + ROBOT_RADIUS * math.cos(math.radians(self.angle + 120)), self.y + ROBOT_RADIUS * math.sin(math.radians(self.angle + 120)))
        right = (self.x + ROBOT_RADIUS * math.cos(math.radians(self.angle - 120)), self.y + ROBOT_RADIUS * math.sin(math.radians(self.angle - 120)))
        pygame.draw.polygon(screen, ROBOT_COLOR, [tip, left, right])
        dot_x = self.x + (ROBOT_RADIUS + 5) * math.cos(rad)
        dot_y = self.y + (ROBOT_RADIUS + 5) * math.sin(rad)
        pygame.draw.circle(screen, DIRECTION_COLOR, (int(dot_x), int(dot_y)), 3)
    def get_rect(self):
        return pygame.Rect(self.x - ROBOT_RADIUS, self.y - ROBOT_RADIUS, ROBOT_RADIUS * 2, ROBOT_RADIUS * 2)