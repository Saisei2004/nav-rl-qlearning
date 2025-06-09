import pickle
import numpy as np
import random
import itertools
import multiprocessing as mp
import signal
import sys
import os
from rl_env import GameEnv
from torch.utils.tensorboard import SummaryWriter

ACTION_SET = [
    (4, 4), (2, 2), (0, 0), (-2, -2), (-4, -4),
    (4, 2), (2, 4), (-4, -2), (-2, -4),
    (4, 0), (0, 4), (-4, 0), (0, -4),
    (2, 0), (0, 2), (-2, 0), (0, -2),
    (2, -2), (-2, 2), (4, -4), (-4, 4),
]

def improved_reward(env, state, done,
    angle_bonus=20, angle_penalty=-20,
    step_penalty=-0.1, goal_reward=100, goal_margin=30,
    forward_bonus=2, backward_penalty=-1,
    obstacle_avoid_bonus=1):

    robot_angle = int(env.game.robot.angle) % 360
    goal_angle = int(env.game.goal_angle) % 360
    angle_diff = abs((robot_angle - goal_angle + 180) % 360 - 180)
    angle_norm = angle_diff / 180

    # ゴール判定
    if hasattr(env.game, "check_goal"):
        if env.game.check_goal(margin=goal_margin):
            return goal_reward
    else:
        if angle_diff <= goal_margin:
            return goal_reward

    reward = step_penalty
    reward += angle_bonus * (1.0 - angle_norm)
    reward += angle_penalty * angle_norm

    # 1. 前進/後退アクションに応じて報酬
    last_action = env.last_action if hasattr(env, 'last_action') else (0, 0)
    if sum(last_action) > 0:
        reward += forward_bonus
    elif sum(last_action) < 0:
        reward += backward_penalty

    # 2. 障害物との最短距離によって報酬（例: 50px以上離れてたら加点）
    lidar = env.game.get_lidar_distances()
    min_dist = min(lidar) if lidar else 9999
    if min_dist > 50:
        reward += obstacle_avoid_bonus

    return reward

class QAgent:
    def __init__(self, action_set):
        self.q_table = dict()  # 独立辞書
        self.action_set = action_set

    def to_key(self, state):
        # 離散化が荒い例
        return tuple(np.round(state, 2))

    def select_action(self, state, eval_mode=False):
        key = self.to_key(state)
        if eval_mode or random.random() > 0.1:  # 固定epsilon=0.1
            if key in self.q_table:
                return self.action_set[np.argmax(self.q_table[key])]
            else:
                return random.choice(self.action_set)
        else:
            return random.choice(self.action_set)

    def update(self, state, action, reward, next_state, alpha=0.1, gamma=0.99):
        key = self.to_key(state)
        idx = self.action_set.index(action)
        next_key = self.to_key(next_state)
        if key not in self.q_table:
            self.q_table[key] = np.zeros(len(self.action_set))  # numpy配列で保存
        if next_key in self.q_table:
            max_next = np.max(self.q_table[next_key])
        else:
            max_next = 0.0
        self.q_table[key][idx] += alpha * (reward + gamma * max_next - self.q_table[key][idx])

def worker(seed, action_set, episodes, max_steps, q_table_queue,
           angle_bonus, angle_penalty, step_penalty,
           forward_bonus, backward_penalty, obstacle_avoid_bonus,
           goal_reward, goal_margin):

    random.seed(seed)
    np.random.seed(seed)
    agent = QAgent(action_set)

    # --- TensorBoardログディレクトリ作成 ---
    log_dir = f"runs/seed_{seed}"
    os.makedirs(log_dir, exist_ok=True)
    writer = SummaryWriter(log_dir=log_dir)

    def reward_fn(env, state, done):
        return improved_reward(
            env, state, done,
            angle_bonus=angle_bonus,
            angle_penalty=angle_penalty,
            step_penalty=step_penalty,
            forward_bonus=forward_bonus,
            backward_penalty=backward_penalty,
            obstacle_avoid_bonus=obstacle_avoid_bonus,
            goal_reward=goal_reward,
            goal_margin=goal_margin,
        )

    env = GameEnv(reward_fn=reward_fn)
    goal_count = 0
    for ep in range(episodes):
        state = env.reset()
        episode_reward = 0
        for _ in range(max_steps):
            action = agent.select_action(state)
            next_state, reward, done, info = env.step(action)
            agent.update(state, action, reward, next_state)
            state = next_state
            episode_reward += reward
            if done:
                if reward == goal_reward:
                    goal_count += 1
                break
        # --- TensorBoardログに出力 ---
        writer.add_scalar('Reward/Episode', episode_reward, ep)
        writer.add_scalar('SuccessRate/Episode', goal_count / (ep + 1), ep)
    writer.close()
    q_table_queue.put(goal_count)

def analyze_and_report(results):
    results_sorted = sorted(results, key=lambda x: x[1], reverse=True)
    print("\n==== 成功回数の多い組み合わせ TOP3 ====")
    for params, score in results_sorted[:3]:
        print(f"成功回数={score} → {params}")
    print("\n==== 成功回数の少ない組み合わせ WORST3 ====")
    for params, score in results_sorted[-3:]:
        print(f"成功回数={score} → {params}")
    all_scores = [score for _, score in results]
    print(f"\n全体統計: 最大={max(all_scores)}, 最小={min(all_scores)}, 平均={np.mean(all_scores):.2f}")

def grid_search():
    import itertools
    import signal
    import sys

    angle_bonus_list = [30]
    angle_penalty_list = [-35]
    step_penalty_list = [-0.05]
    goal_reward_list = [100]
    goal_margin_list = [30]
    forward_bonus_list = [0]
    backward_penalty_list = [0]
    obstacle_avoid_bonus_list = [0]

    N_PROCS = 13
    EPISODES = 260
    episodes_per_proc = EPISODES // N_PROCS
    MAX_STEPS = 200

    best_score = -1
    best_params = None
    results = []

    param_grid = list(itertools.product(
        angle_bonus_list, angle_penalty_list, step_penalty_list,
        forward_bonus_list, backward_penalty_list, obstacle_avoid_bonus_list,
        goal_reward_list, goal_margin_list
    ))

    def signal_handler(sig, frame):
        print("\n[Ctrl+C] 中断されました。ここまでの集計を表示します。")
        analyze_and_report(results)
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    for i, params in enumerate(param_grid):
        (
            angle_bonus, angle_penalty, step_penalty,
            forward_bonus, backward_penalty, obstacle_avoid_bonus,
            goal_reward, goal_margin
        ) = params

        print(
            f"\n[{i+1}/{len(param_grid)}] Testing: "
            f"angle_bonus={angle_bonus}, angle_penalty={angle_penalty}, step_penalty={step_penalty}, "
            f"forward_bonus={forward_bonus}, backward_penalty={backward_penalty}, "
            f"obstacle_avoid_bonus={obstacle_avoid_bonus}, "
            f"goal_reward={goal_reward}, goal_margin={goal_margin}"
        )

        q_table_queue = mp.Queue()
        procs = []
        for j in range(N_PROCS):
            p = mp.Process(
                target=worker,
                args=(
                    j, ACTION_SET, episodes_per_proc, MAX_STEPS, q_table_queue,
                    angle_bonus, angle_penalty, step_penalty,
                    forward_bonus, backward_penalty, obstacle_avoid_bonus,
                    goal_reward, goal_margin
                )
            )
            procs.append(p)
            p.start()

        goal_count_total = 0
        for _ in range(N_PROCS):
            worker_goal_count = q_table_queue.get()
            goal_count_total += worker_goal_count
        for p in procs:
            p.join()

        print(f"成功回数: {goal_count_total} / {episodes_per_proc * N_PROCS}")

        results.append((params, goal_count_total))

        if goal_count_total > 30:
            print("\n✅ 成功回数が30を超えたため中断します。")
            break

    analyze_and_report(results)

import subprocess
import webbrowser
import time

def launch_tensorboard(logdir="runs", port=6006):
    tb_proc = subprocess.Popen(
        ["tensorboard", f"--logdir={logdir}", f"--port={port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)
    webbrowser.open(f"http://localhost:{port}")
    print(f"TensorBoard started at http://localhost:{port}")
    return tb_proc

if __name__ == "__main__":
    grid_search()
    launch_tensorboard(logdir="runs")
