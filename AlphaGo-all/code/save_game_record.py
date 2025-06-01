import json
import os

def save_game_record(moves, winner, winner_color, winner_is_first, save_dir, game_idx):
    """
    moves: [('b', (x, y)), ('w', (x, y)), ...]
    winner: 1/2（1为黑，2为白）
    winner_color: 'b' or 'w'
    winner_is_first: True/False
    save_dir: 保存目录
    game_idx: 第几局
    """
    os.makedirs(save_dir, exist_ok=True)
    record = {
        "moves": moves,
        "winner": winner,
        "winner_color": winner_color,
        "winner_is_first": winner_is_first
    }
    with open(os.path.join(save_dir, f"game_{game_idx}.json"), "w", encoding="utf-8") as f:
        json.dump(record, f)

def query_personalized_records(current_moves, current_color, current_is_first, records):
    """
    current_moves: [(x, y), ...]
    current_color: 'b' or 'w'
    current_is_first: True/False
    records: 读取的所有棋谱（list of dict）
    返回推荐落子 (x, y) 或 None
    """
    for rec in records:
        if rec["winner_color"] == current_color and rec["winner_is_first"] == current_is_first:
            sgf_coords = [move for _, move in rec["moves"]]
            if len(current_moves) < len(sgf_coords) and current_moves == sgf_coords[:len(current_moves)]:
                return sgf_coords[len(current_moves)]
    return None

def load_all_records(record_dir):
    import glob
    records = []
    for file in glob.glob(os.path.join(record_dir, "*.json")):
        with open(file, "r", encoding="utf-8") as f:
            records.append(json.load(f))
    return records