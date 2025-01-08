from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from restaurant import RestaurantAVL
from player import PlayerTree
from game_logic import GameLogic
from queue_system import MatchQueue
import threading
import random
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

server_lock = threading.Lock()
server = {
    "players": PlayerTree(),
    "restaurants": RestaurantAVL(),
    "match_queue": MatchQueue(),
    "history": [],
    "ready_players": []
}

# Initialize restaurant data
server["restaurants"].add_restaurant("鄰家早午餐", 4.5, 230)
server["restaurants"].add_restaurant("沒料鐵哥", 2.9, 364)
server["restaurants"].add_restaurant("gogobus", 4.4, 356)
server["restaurants"].add_restaurant("明哥滷味(忠孝)", 4.6, 520)
server["restaurants"].add_restaurant("品味", 3.9, 26)
server["restaurants"].add_restaurant("龍哥", 3.6, 120)
server["restaurants"].add_restaurant("禾社", 4.5, 431)
server["restaurants"].add_restaurant("狸匠", 4.3, 2788)
server["restaurants"].add_restaurant("麵麵", 4.4, 675)
server["restaurants"].add_restaurant("玩麵", 4.1, 1283)
server["restaurants"].add_restaurant("餃佼者", 4.0, 1437)
server["restaurants"].add_restaurant("好燙鍋物", 4.4, 1734)
server["restaurants"].add_restaurant("麻辣香干鍋", 4.3, 1234)
server["restaurants"].add_restaurant("麥當勞", 4, 2352)
server["restaurants"].add_restaurant("築崎相撲鍋物", 4.3, 1882)
server["restaurants"].add_restaurant("摩斯漢堡", 4.2, 1234)
server["restaurants"].add_restaurant("SUBWAY", 3.8, 324)
server["restaurants"].add_restaurant("小木屋鬆餅", 4.4, 854)
server["restaurants"].add_restaurant("麥味登", 4.5, 1339)
server["restaurants"].add_restaurant("協力旺", 2.9, 70)
server["restaurants"].add_restaurant("台灣味蔥抓餅飯糰", 3.7, 36)
server["restaurants"].add_restaurant("極品軒", 4.2, 421)
server["restaurants"].add_restaurant("無名燒肉丼飯", 4.3, 54)
server["restaurants"].add_restaurant("清一色", 4.0, 1900)
server["restaurants"].add_restaurant("聞香牛肉麵", 4.1, 1717)
server["restaurants"].add_restaurant("烤茶亭", 4.2, 150)
server["restaurants"].add_restaurant("斗六門當歸鴨", 3.6, 46)
server["restaurants"].add_restaurant("越南安安河粉", 4.9, 409)
server["restaurants"].add_restaurant("Oh! 小麵店", 4.3, 466)
server["restaurants"].add_restaurant("麻娘子麻辣燙", 4.8, 200)
server["restaurants"].add_restaurant("一中豪大雞排", 4.4, 257)
server["restaurants"].add_restaurant("咖哩魂蛋", 4.9, 759)
server["restaurants"].add_restaurant("麻醬滷味", 3.3, 265)
server["restaurants"].add_restaurant("四季軒", 3.6, 138)
server["restaurants"].add_restaurant("中華滷味", 4.1, 145)

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

    if player and player not in list(server["match_queue"].queue.queue):
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

        # Start a new thread for matchmaking
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

    # Mark player as ready
    if user not in server['ready_players']:
        server["ready_players"].append(user)

    # Check if both players are ready
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
    username = data.get("username")  # Current player's username
    opponent = data.get("opponent")  # Opponent's username
    user_option = data.get("opt")  # Current player's battle option
    user_rest = data.get("rest")  # Current player's restaurant choice

    # Store user options temporarily
    if "battle_data" not in server:
        server["battle_data"] = {}

    # Save current user's option and restaurant
    if username not in server["battle_data"]:
        server["battle_data"][username] = {
            "option": user_option,
            "restaurant": user_rest,
            "opponent": opponent
        }

    # Check if opponent has submitted their option
    if opponent in server["battle_data"] and server["battle_data"][opponent]["opponent"] == username:
        opponent_option = server["battle_data"][opponent]["option"]
        opponent_rest = server["battle_data"][opponent]["restaurant"]

        # Both players have submitted their options; compare them
        result1, result2 = GameLogic.judge_winner(user_option, opponent_option)

        # Record statistics
        player1 = server["players"].find_player(username)
        player2 = server["players"].find_player(opponent)
        player1.record["對戰次數"] += 1
        player2.record["對戰次數"] += 1

        if result1 == "勝利":
            player1.record["勝"] += 1
            player2.record["負"] += 1
            winner = username
            winning_restaurant = user_rest
        elif result2 == "勝利":
            player2.record["勝"] += 1
            player1.record["負"] += 1
            winner = opponent
            winning_restaurant = opponent_rest
        else:
            winner = "平手"
            winning_restaurant = "無"

        # Get opponent's Instagram handle
        opponent_instagram = player2.instagram if hasattr(player2, "instagram") else "無資料"
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create match history entry
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
        server["history"].append(history_entry)

        # Broadcast results to all clients
        emit('game_result', {
            "message": f"{username} 對戰 {opponent}",
            "details": history_entry
        }, broadcast=True)

        # Clear temporary battle data for these players
        del server["battle_data"][username]
        del server["battle_data"][opponent]
    else:
        # Notify the player that we are waiting for the opponent
        emit('waiting_for_opponent', {"message": "等待對手選擇對戰選項..."})


@socketio.on('game_result')
def game_result(data):
    username = data.get("username")  # 發起對戰的玩家
    opponent = data.get("opponent")  # 對手玩家

    # 在對戰結果後，發送重新配對的選項給雙方
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
        # 確保玩家重新加入隊列
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
