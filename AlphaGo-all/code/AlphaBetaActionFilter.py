"""
独立的五子棋α-β剪枝动作筛选器，参考 gobang_AI.py 的实现逻辑。
不依赖全局变量，所有棋盘状态通过参数传递。
"""

import copy

COLUMN = 8
ROW = 8

# 棋型的评估分数
shape_score = [
    (50, (0, 1, 1, 0, 0)),
    (50, (0, 0, 1, 1, 0)),
    (200, (1, 1, 0, 1, 0)),
    (500, (0, 0, 1, 1, 1)),
    (500, (1, 1, 1, 0, 0)),
    (5000, (0, 1, 1, 1, 0)),
    (5000, (0, 1, 0, 1, 1, 0)),
    (5000, (0, 1, 1, 0, 1, 0)),
    (5000, (1, 1, 1, 0, 1)),
    (5000, (1, 1, 0, 1, 1)),
    (5000, (1, 0, 1, 1, 1)),
    (5000, (1, 1, 1, 1, 0)),
    (5000, (0, 1, 1, 1, 1)),
    (50000, (0, 1, 1, 1, 1, 0)),
    (99999999, (1, 1, 1, 1, 1))
]

def is_forbidden(move, my_list, enemy_list):
    """
    检查黑棋(先手)落子move后是否为禁手（三三、四四、长连）
    my_list: 当前玩家所有落子
    enemy_list: 对手所有落子
    """
    # 1. 模拟落子
    temp_list = my_list + [move]
    # 2. 检查长连
    if count_continuous(move, temp_list) >= 6:
        return True
    # 3. 检查活三和四的数量
    live3 = count_live_n(move, temp_list, enemy_list, n=3)
    live4 = count_live_n(move, temp_list, enemy_list, n=4)
    if live3 >= 2:  # 三三禁手
        return True
    if live4 >= 2:  # 四四禁手
        return True
    return False

def count_continuous(move, my_list):
    """统计move点在四个方向上的最大连续己子数"""
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    max_count = 1
    for dx, dy in directions:
        count = 1
        for d in [1, -1]:
            x, y = move
            while True:
                x += dx * d
                y += dy * d
                if (x, y) in my_list:
                    count += 1
                else:
                    break
        max_count = max(max_count, count)
    return max_count

def count_live_n(move, my_list, enemy_list, n=3):
    """
    统计move点落下后，形成的活n（如活三、活四）数量
    """
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    count = 0
    for dx, dy in directions:
        line = []
        for i in range(-4, 5):
            x, y = move[0] + dx*i, move[1] + dy*i
            if (x, y) == move:
                line.append(1)
            elif (x, y) in my_list:
                line.append(1)
            elif (x, y) in enemy_list:
                line.append(2)
            else:
                line.append(0)
        # 检查活n
        for i in range(len(line)-n-1):
            window = line[i:i+n+2]
            if window[0]==0 and window[-1]==0 and window[1:-1]==[1]*n:
                count += 1
    return count

def alpha_beta_search(list1, list2, list3, list_all, depth=2, ratio=1, top_n=5):
    """
    返回评分最高的前top_n个动作
    list1: AI棋子坐标 [(x, y), ...]
    list2: 对手棋子坐标 [(x, y), ...]
    list3: 所有已落子点 [(x, y), ...]
    list_all: 棋盘所有点 [(x, y), ...]
    """
    blank_list = list(set(list_all).difference(set(list3)))
    move_scores = []
    for move in blank_list:
        # 拷贝棋盘状态
        # 只对黑棋（先手）判断禁手
        if len(list1) == len(list2):  # 黑棋落子
            if is_forbidden(move, list1, list2):
                continue
        l1 = list1.copy()
        l2 = list2.copy()
        l3 = list3.copy()
        l1.append(move)
        l3.append(move)
        score = -negamax(l2, l1, l3, list_all, depth-1, -99999999, 99999999, False, ratio)
        move_scores.append((move, score))
    move_scores.sort(key=lambda x: x[1], reverse=True)
    return [m for m, s in move_scores[:top_n]]

def negamax(list1, list2, list3, list_all, depth, alpha, beta, is_me, ratio):
    # list1: 当前玩家
    # list2: 对手
    # list3: 所有已落子点
    if game_win(list1) or game_win(list2) or depth == 0:
        return evaluation(list1, list2, ratio)
    blank_list = list(set(list_all).difference(set(list3)))
    order(blank_list, list3)
    for next_step in blank_list:
        if not has_neightnor(next_step, list3):
            continue
        # 只对黑棋（先手）判断禁手
        if is_me and len(list1) == len(list2):  # 当前递归层是黑棋
            if is_forbidden(next_step, list1, list2):
                continue
        if is_me:
            list1.append(next_step)
        else:
            list2.append(next_step)
        list3.append(next_step)
        value = -negamax(list2, list1, list3, list_all, depth - 1, -beta, -alpha, not is_me, ratio)
        if is_me:
            list1.pop()
        else:
            list2.pop()
        list3.pop()
        if value > alpha:
            if value >= beta:
                return beta
            alpha = value
    return alpha

def order(blank_list, list3):
    if not list3:
        return
    last_pt = list3[-1]
    for item in blank_list[:]:
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                pt = (last_pt[0] + i, last_pt[1] + j)
                if pt in blank_list:
                    blank_list.remove(pt)
                    blank_list.insert(0, pt)

def has_neightnor(pt, list3):
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            if (pt[0] + i, pt[1] + j) in list3:
                return True
    return False

def evaluation(my_list, enemy_list, ratio):
    # 参考 gobang_AI.py 的 evaluation
    score_all_arr = []
    my_score = 0
    for pt in my_list:
        m, n = pt
        my_score += cal_score(m, n, 0, 1, enemy_list, my_list, score_all_arr)
        my_score += cal_score(m, n, 1, 0, enemy_list, my_list, score_all_arr)
        my_score += cal_score(m, n, 1, 1, enemy_list, my_list, score_all_arr)
        my_score += cal_score(m, n, -1, 1, enemy_list, my_list, score_all_arr)
    score_all_arr_enemy = []
    enemy_score = 0
    for pt in enemy_list:
        m, n = pt
        enemy_score += cal_score(m, n, 0, 1, my_list, enemy_list, score_all_arr_enemy)
        enemy_score += cal_score(m, n, 1, 0, my_list, enemy_list, score_all_arr_enemy)
        enemy_score += cal_score(m, n, 1, 1, my_list, enemy_list, score_all_arr_enemy)
        enemy_score += cal_score(m, n, -1, 1, my_list, enemy_list, score_all_arr_enemy)
    total_score = my_score - enemy_score * ratio * 0.1
    return total_score

def cal_score(m, n, x_decrict, y_derice, enemy_list, my_list, score_all_arr):
    add_score = 0
    max_score_shape = (0, None)
    for item in score_all_arr:
        for pt in item[1]:
            if m == pt[0] and n == pt[1] and x_decrict == item[2][0] and y_derice == item[2][1]:
                return 0
    for offset in range(-5, 1):
        pos = []
        for i in range(0, 6):
            pt = (m + (i + offset) * x_decrict, n + (i + offset) * y_derice)
            if pt in enemy_list:
                pos.append(2)
            elif pt in my_list:
                pos.append(1)
            else:
                pos.append(0)
        tmp_shap5 = tuple(pos[:5])
        tmp_shap6 = tuple(pos[:6])
        for (score, shape) in shape_score:
            if tmp_shap5 == shape or tmp_shap6 == shape:
                if score > max_score_shape[0]:
                    max_score_shape = (
                        score,
                        tuple((m + (j + offset) * x_decrict, n + (j + offset) * y_derice) for j in range(5)),
                        (x_decrict, y_derice)
                    )
    if max_score_shape[1] is not None:
        for item in score_all_arr:
            for pt1 in item[1]:
                for pt2 in max_score_shape[1]:
                    if pt1 == pt2 and max_score_shape[0] > 10 and item[0] > 10:
                        add_score += item[0] + max_score_shape[0]
        score_all_arr.append(max_score_shape)
    return add_score + max_score_shape[0]

def game_win(lst):
    for m in range(COLUMN):
        for n in range(ROW):
            if n < ROW - 4 and all((m, n + k) in lst for k in range(5)):
                return True
            elif m < ROW - 4 and all((m + k, n) in lst for k in range(5)):
                return True
            elif m < ROW - 4 and n < ROW - 4 and all((m + k, n + k) in lst for k in range(5)):
                return True
            elif m < ROW - 4 and n > 3 and all((m + k, n - k) in lst for k in range(5)):
                return True
    return False

# # 用法示例
# if __name__ == "__main__":
#     # 初始化棋盘
#     list_all = [(i, j) for i in range(COLUMN) for j in range(ROW)]
#     list1 = []  # AI
#     list2 = []  # human
#     list3 = []  # all
#     # 假设AI先手
#     best_moves = alpha_beta_search(list1, list2, list3, list_all, depth=2, ratio=1, top_n=5)
#     print("推荐动作：", best_moves)