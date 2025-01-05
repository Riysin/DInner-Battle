from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from restaurant import RestaurantBST
from player import PlayerLinkedList
from game_logic import GameLogic
from queue_system import MatchQueue
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 允许所有跨域请求
socketio = SocketIO(app, cors_allowed_origins="*")

server_lock = threading.Lock()  # 保護多線程操作
server = {
    "players": PlayerLinkedList(),
    "restaurants": RestaurantBST(),
    "match_queue": MatchQueue(),
    "history": []
}

# 初始化餐廳
server["restaurants"].add_restaurant("鄰家早午餐", "剪刀")
server["restaurants"].add_restaurant("gogobus", "石頭")
server["restaurants"].add_restaurant("品味", "布")


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "缺少用戶名或密碼"}), 400

    if server["players"].register_player(username, password):
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
    if player:
        server["match_queue"].add_player(player)
        emit('queue_status', {"message": f"{username} 已加入配對隊列"}, broadcast=True)
    else:
        emit('error', {"error": "玩家不存在"})


@socketio.on('start_matchmaking')
def start_matchmaking():
    def match_players():
        while True:
            player1, player2 = server["match_queue"].get_next_match()
            if player1 and player2:
                with server_lock:
                    threading.Thread(target=start_game, args=(player1, player2)).start()

    threading.Thread(target=match_players).start()


def start_game(player1, player2):
    rest1 = server["restaurants"].get_random_restaurant()
    rest2 = server["restaurants"].get_random_restaurant()

    result1, result2 = GameLogic.judge_winner(rest1.symbol, rest2.symbol)

    # 更新玩家紀錄
    player1.record["對戰次數"] += 1
    player2.record["對戰次數"] += 1
    if result1 == "勝利":
        player1.record["勝"] += 1
        player2.record["負"] += 1
    elif result2 == "勝利":
        player2.record["勝"] += 1
        player1.record["負"] += 1

    # 保存歷史並廣播結果
    server["history"].append((player1.username, player2.username, rest1.name, rest2.name, result1))
    socketio.emit('game_result', {
        "player1": player1.username,
        "player2": player2.username,
        "restaurant1": rest1.name,
        "restaurant2": rest2.name,
        "result1": result1,
        "result2": result2
    })


@app.route('/history', methods=['GET'])
def view_history():
    return jsonify(server["history"]), 200


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
