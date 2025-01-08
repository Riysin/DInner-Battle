from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from restaurant import RestaurantAVL
from player import PlayerTree
from game_logic import GameLogic
from queue_system import MatchQueue
from datetime import datetime
import pandas as pd
import threading
import random
import heapq

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

server_lock = threading.Lock()
server = {
    "players": PlayerTree(), # 2-3-4 樹
    "restaurants": RestaurantAVL(), # AVL 樹
    "match_queue": MatchQueue(), # Queue
    "history": [], # Heap
    "ready_players": [], # List
    "battle_data":{}
}

def load_restaurants_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        required_columns = {"name", "stars", "comment_nums"}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"CSV 文件必須包含以下欄位: {required_columns}")

        for _, row in df.iterrows():
            server["restaurants"].add_restaurant(row["name"], float(row["stars"]), int(row["comment_nums"]))
    except Exception as e:
        print(f"加載餐廳數據時發生錯誤: {e}")

load_restaurants_from_csv("restaurants.csv")

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    instagram = data.get("instagram")
    gender = data.get("gender")
    if not username or not password or not instagram or not gender:
        return jsonify({"error": "請填寫完整資訊"}), 400

    if server["players"].register_player(username, password, instagram, gender):
        return jsonify({"message": "註冊成功"}), 200
    return jsonify({"error": "用戶名已存在"}), 409


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    player = server["players"].authenticate_player(username, password)
    if player:
        return jsonify({"message": "登入成功"}), 200
    return jsonify({"error": "登入失敗"}), 401


@socketio.on('join_queue')
def join_queue(data):
    username = data.get("username")
    player = server["players"].find_player(username)

    if player and player not in list(server["match_queue"].queue):
        server["match_queue"].add_player(player)
        emit('queue_status', {"message": f"{username} 已加入配對隊列"}, broadcast=True)

        def match_players():
            while True:
                player1, player2 = server["match_queue"].get_next_match()
                if player1 and player2:
                    with server_lock:
                        socketio.emit(
                            'match_ready',
                            {
                                "message": f"{player1.username} 與 {player2.username} 配對成功",
                                "player1": player1.username,
                                "player1_gender": player1.gender,
                                "player2": player2.username,
                                "player2_gender": player2.gender,
                            }
                        )

        threading.Thread(target=match_players).start()
    else:
        emit('error', {"error": "玩家不存在或你已經正在配對中"}, broadcast=True)

@app.route('/restaurant/random', methods=['GET'])
def random_restaurant():
    restaurants = server["restaurants"].get_all_restaurants()
    if not restaurants:
        return jsonify({"error": "沒有餐廳資料"}), 404
    try:
        random_rest = random.choice(restaurants)
        return jsonify({"name": random_rest.name, "rating": random_rest.rating}), 200
    except IndexError:
        return jsonify({"error": "沒有餐廳資料"}), 404


@app.route('/restaurant/list', methods=['GET'])
def list_restaurants():
    restaurants = server["restaurants"].get_all_restaurants()
    if not restaurants:
        return jsonify([]), 200
    restaurant_data = [{"name": r.name, "rating": r.rating} for r in restaurants]
    return jsonify(restaurant_data), 200


@socketio.on('confirm_ready')
def confirm_ready(data):
    player1 = data.get("player1")
    player2 = data.get("player2")
    user = data.get("user")

    if user not in server['ready_players']:
        server["ready_players"].append(user)

    if player1 in server['ready_players'] and player2 in server['ready_players']:
        server["ready_players"].remove(player1)
        server["ready_players"].remove(player2)

        socketio.emit('start_battle', {
            "message": "雙方已準備好，遊戲開始！",
            "player1": player1,
            "player2": player2
        })


@socketio.on('start_game')
def start_game(data):
    username = data.get("username")
    opponent = data.get("opponent")
    user_option = data.get("opt")
    user_rest = data.get("rest")

    if username not in server["battle_data"]:
        server["battle_data"][username] = {
            "option": user_option,
            "restaurant": user_rest,
            "opponent": opponent
        }

    if opponent in server["battle_data"] and server["battle_data"][opponent]["opponent"] == username:
        opponent_option = server["battle_data"][opponent]["option"]
        opponent_rest = server["battle_data"][opponent]["restaurant"]

        result1, result2 = GameLogic.judge_winner(user_option, opponent_option)

        player1 = server["players"].find_player(username)
        player2 = server["players"].find_player(opponent)
        player1.record["對戰次數"] += 1
        player2.record["對戰次數"] += 1

        if result1 == "勝利":
            player1.record["勝"] += 1
            player2.record["負"] += 1
            winning_restaurant = user_rest
        elif result2 == "勝利":
            player2.record["勝"] += 1
            player1.record["負"] += 1
            winning_restaurant = opponent_rest
        else:
            winning_restaurant = "無"

        opponent_instagram = player2.instagram if hasattr(player2, "instagram") else "無資料"
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        history_entry = {
            "user": username,
            "restaurant1": user_rest,
            "option1": user_option,
            "result1": result1,
            "opponent": opponent,
            "restaurant2": opponent_rest,
            "option2": opponent_option,
            "result2": result2,
            "winning_restaurant": winning_restaurant,
            "opponent_instagram": opponent_instagram,
            "date": current_date
        }
        heapq.heappush(server["history"], history_entry)

        emit('game_result', {
            "message": f"{username} 對戰 {opponent}",
            "details": history_entry
        }, broadcast=True)

        del server["battle_data"][username]
        del server["battle_data"][opponent]
    else:
        emit('waiting_for_opponent', {"message": "等待對手選擇對戰選項..."})


@socketio.on('game_result')
def game_result(data):
    username = data.get("username")
    opponent = data.get("opponent")

    emit('rejoin_option', {
        "message": "對戰結束！是否要重新進入配對？",
        "user": username,
        "opponent": opponent
    }, to=username)

    emit('rejoin_option', {
        "message": "對戰結束！是否要重新進入配對？",
        "user": opponent,
        "opponent": username
    }, to=opponent)


@socketio.on('rejoin_queue')
def rejoin_queue(data):
    username = data.get("username")
    player = server["players"].find_player(username)

    if player:
        if player not in list(server["match_queue"].queue.queue):
            server["match_queue"].add_player(player)
            emit('queue_status', {"message": f"{username} 已重新加入配對隊列"}, broadcast=True)
        else:
            emit('error', {"error": "玩家已在配對隊列中"}, to=username)
    else:
        emit('error', {"error": "玩家不存在"}, to=username)


@app.route('/history', methods=['GET'])
def view_history():
    return jsonify(server["history"]), 200


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
