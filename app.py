import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)  # 启用 CORS，允许所有来源的跨域请求

# 数据库文件路径
USERS_DATABASE = 'users.db'
SETTINGS_DATABASE = 'settings.db'
PLAYERS_DATABASE = 'player.db'

# 初始化用户数据库
def init_users_db():
    conn = sqlite3.connect(USERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()


# 初始化设置数据库
def init_settings_db():
    conn = sqlite3.connect(SETTINGS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            minecraftServerIP TEXT NOT NULL,
            mcsmApiAddress TEXT NOT NULL,
            emailServiceHost TEXT NOT NULL,
            mcsmDaemonId TEXT NOT NULL,
            emailServicePort TEXT NOT NULL,
            mcsmInstanceId TEXT NOT NULL,
            emailServiceUsername TEXT NOT NULL,
            mcsmApikey TEXT NOT NULL,
            emailServicePassword TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 初始化玩家数据库
def init_players_db():
    conn = sqlite3.connect(PLAYERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            game_id TEXT PRIMARY KEY,
            qq TEXT,
            email TEXT,
            permission_group TEXT CHECK(permission_group IN ('Player', 'Graduate Engineer', 'Engineer', 'Senior Engineer', 'Admin')),
            join_date TEXT,
            leave_date TEXT,
            leave_reason TEXT
        )
    ''')
    conn.commit()
    conn.close()


# 注册用户（用于测试，实际应用中可能需要更完善的注册逻辑）
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 连接数据库
    conn = sqlite3.connect(USERS_DATABASE)
    cursor = conn.cursor()

    # 检查用户是否已存在
    cursor.execute('SELECT * FROM users WHERE username =? OR email =?', (username, email))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return jsonify({"message": "用户名或邮箱已存在"}), 400

    # 插入新用户，密码明文保存
    cursor.execute('INSERT INTO users (username, email, password, is_active) VALUES (?,?,?,?)',
                   (username, email, password, 1))
    conn.commit()
    conn.close()

    return jsonify({"message": "注册成功"}), 201


# 登录接口
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 连接数据库
    conn = sqlite3.connect(USERS_DATABASE)
    cursor = conn.cursor()

    # 查询用户
    cursor.execute('SELECT * FROM users WHERE username =?', (username,))
    user = cursor.fetchone()

    if user:
        user_id, user_username, user_email, user_password, is_active = user
        # 检查用户是否被封禁
        if is_active == 0:
            conn.close()
            return jsonify({"message": "该用户已被封禁，无法登录"}), 403

        # 验证密码，直接比较明文密码
        if password == user_password:
            conn.close()
            return jsonify({"message": "登录成功"}), 200

    conn.close()
    return jsonify({"message": "用户名或密码错误"}), 401


# 保存设置接口
@app.route('/settings/save', methods=['POST'])
def save_settings():
    data = request.get_json()
    minecraftServerIP = data.get('minecraftServerIP')
    mcsmApiAddress = data.get('mcsmApiAddress')
    emailServiceHost = data.get('emailServiceHost')
    mcsmDaemonId = data.get('mcsmDaemonId')
    emailServicePort = data.get('emailServicePort')
    mcsmInstanceId = data.get('mcsmInstanceId')
    emailServiceUsername = data.get('emailServiceUsername')
    mcsmApikey = data.get('mcsmApikey')
    emailServicePassword = data.get('emailServicePassword')

    # 连接设置数据库
    conn = sqlite3.connect(SETTINGS_DATABASE)
    cursor = conn.cursor()

    # 先检查是否已有设置记录，如果有则更新，没有则插入
    cursor.execute('SELECT * FROM settings')
    existing_settings = cursor.fetchone()
    if existing_settings:
        cursor.execute('''
            UPDATE settings SET 
            minecraftServerIP =?,
            mcsmApiAddress =?,
            emailServiceHost =?,
            mcsmDaemonId =?,
            emailServicePort =?,
            mcsmInstanceId =?,
            emailServiceUsername =?,
            mcsmApikey =?,
            emailServicePassword =?
            WHERE id =?
        ''', (
            minecraftServerIP,
            mcsmApiAddress,
            emailServiceHost,
            mcsmDaemonId,
            emailServicePort,
            mcsmInstanceId,
            emailServiceUsername,
            mcsmApikey,
            emailServicePassword,
            existing_settings[0]
        ))
    else:
        cursor.execute('''
            INSERT INTO settings (
                minecraftServerIP,
                mcsmApiAddress,
                emailServiceHost,
                mcsmDaemonId,
                emailServicePort,
                mcsmInstanceId,
                emailServiceUsername,
                mcsmApikey,
                emailServicePassword
            ) VALUES (?,?,?,?,?,?,?,?,?)
        ''', (
            minecraftServerIP,
            mcsmApiAddress,
            emailServiceHost,
            mcsmDaemonId,
            emailServicePort,
            mcsmInstanceId,
            emailServiceUsername,
            mcsmApikey,
            emailServicePassword
        ))

    conn.commit()
    conn.close()

    return jsonify({"message": "设置保存成功"}), 200


# 获取设置接口
@app.route('/settings/get', methods=['GET'])
def get_settings():
    # 连接设置数据库
    conn = sqlite3.connect(SETTINGS_DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM settings')
    settings = cursor.fetchone()

    if settings:
        settings_data = {
            "minecraftServerIP": settings[1],
            "mcsmApiAddress": settings[2],
            "emailServiceHost": settings[3],
            "mcsmDaemonId": settings[4],
            "emailServicePort": settings[5],
            "mcsmInstanceId": settings[6],
            "emailServiceUsername": settings[7],
            "mcsmApikey": settings[8],
            "emailServicePassword": settings[9]
        }
        conn.close()
        return jsonify(settings_data), 200
    else:
        conn.close()
        return jsonify({}), 200


# 获取所有用户
@app.route('/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect(USERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, is_active FROM users')
    users = cursor.fetchall()
    conn.close()

    user_list = []
    for user in users:
        user_dict = {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "is_banned": not user[3]
        }
        user_list.append(user_dict)

    return jsonify(user_list), 200


# 删除用户
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = sqlite3.connect(USERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id =?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "用户删除成功"}), 200


# 编辑用户
@app.route('/users/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect(USERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET username =?, email =?, password =? WHERE id =?',
                   (username, email, password, user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "用户信息修改成功"}), 200


# 封禁用户
@app.route('/users/<int:user_id>/ban', methods=['PUT'])
def ban_user(user_id):
    conn = sqlite3.connect(USERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_active = 0 WHERE id =?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "用户封禁成功"}), 200


# 解封用户
@app.route('/users/<int:user_id>/unban', methods=['PUT'])
def unban_user(user_id):
    conn = sqlite3.connect(USERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_active = 1 WHERE id =?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "用户解封成功"}), 200

# 获取所有玩家信息
@app.route('/players', methods=['GET'])
def get_players():
    conn = sqlite3.connect(PLAYERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT game_id, qq, email, permission_group, join_date, leave_date FROM players')
    players = cursor.fetchall()
    conn.close()

    player_list = []
    for player in players:
        player_dict = {
            "game_id": player[0],
            "qq": player[1],
            "email": player[2],
            "permission_group": player[3],
            "join_date": player[4],
            "leave_date": player[5]
        }
        player_list.append(player_dict)

    return jsonify(player_list), 200

# 添加玩家
@app.route('/players', methods=['POST'])
def add_player():
    data = request.get_json()
    game_id = data.get('game_id')
    qq = data.get('qq')
    email = data.get('email')
    permission_group = data.get('permission_group')
    join_date = data.get('join_date')
    leave_date = data.get('leave_date')
    leave_reason = data.get('leave_reason')

    # 验证 permission_group 是否合法
    if permission_group not in ['Player', 'Graduate Engineer', 'Engineer', 'Senior Engineer', 'Admin']:
        return jsonify({"message": "无效的权限组"}), 400

    conn = sqlite3.connect(PLAYERS_DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO players (game_id, qq, email, permission_group, join_date, leave_date, leave_reason) VALUES (?,?,?,?,?,?,?)',
                       (game_id, qq, email, permission_group, join_date, leave_date, leave_reason))
        conn.commit()
        return jsonify({"message": "玩家添加成功"}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({"message": "游戏 ID 已存在"}), 400
    finally:
        conn.close()

# 删除玩家
@app.route('/players/<string:game_id>', methods=['DELETE'])
def delete_player(game_id):
    conn = sqlite3.connect(PLAYERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM players WHERE game_id =?', (game_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "玩家删除成功"}), 200

# 编辑玩家
@app.route('/players/<string:game_id>', methods=['PUT'])
def edit_player(game_id):
    data = request.get_json()
    qq = data.get('qq')
    email = data.get('email')
    permission_group = data.get('permission_group')
    join_date = data.get('join_date')
    leave_date = data.get('leave_date')
    leave_reason = data.get('leave_reason')

    # 验证 permission_group 是否合法
    if permission_group not in ['Player', 'Graduate Engineer', 'Engineer', 'Senior Engineer', 'Admin']:
        return jsonify({"message": "无效的权限组"}), 400

    conn = sqlite3.connect(PLAYERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('UPDATE players SET qq =?, email =?, permission_group =?, join_date =?, leave_date =?, leave_reason =? WHERE game_id =?',
                   (qq, email, permission_group, join_date, leave_date, leave_reason, game_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "玩家信息修改成功"}), 200

# 批量删除玩家
@app.route('/players/batch-delete', methods=['POST'])
def batch_delete_players():
    data = request.get_json()
    game_ids = data.get('game_ids')

    conn = sqlite3.connect(PLAYERS_DATABASE)
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in game_ids)
    cursor.execute(f'DELETE FROM players WHERE game_id IN ({placeholders})', game_ids)
    conn.commit()
    conn.close()
    return jsonify({"message": "玩家批量删除成功"}), 200

# 搜索玩家
@app.route('/players/search', methods=['GET'])
def search_players():
    keyword = request.args.get('keyword')
    conn = sqlite3.connect(PLAYERS_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT game_id, qq, email, permission_group, join_date, leave_date FROM players WHERE game_id LIKE? OR qq LIKE? OR email LIKE?',
                   (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    players = cursor.fetchall()
    conn.close()

    player_list = []
    for player in players:
        player_dict = {
            "game_id": player[0],
            "qq": player[1],
            "email": player[2],
            "permission_group": player[3],
            "join_date": player[4],
            "leave_date": player[5]
        }
        player_list.append(player_dict)

    return jsonify(player_list), 200

# 获取特定权限组（Graduate Engineer, Engineer, Senior Engineer）的玩家
@app.route('/players/engineer-groups', methods=['GET'])
def get_players_by_engineer_groups():
    # 连接玩家数据库
    conn = sqlite3.connect(PLAYERS_DATABASE)
    cursor = conn.cursor()
    # 查询特定权限组的玩家
    cursor.execute('SELECT game_id, qq, email, permission_group, join_date, leave_date FROM players WHERE permission_group IN (?,?,?)', ('Graduate Engineer', 'Engineer', 'Senior Engineer'))
    players = cursor.fetchall()
    conn.close()

    player_list = []
    for player in players:
        player_dict = {
            "game_id": player[0],
            "qq": player[1],
            "email": player[2],
            "permission_group": player[3],
            "join_date": player[4],
            "leave_date": player[5]
        }
        player_list.append(player_dict)

    return jsonify(player_list), 200

# 修改玩家权限组
@app.route('/players/<string:game_id>/permission-group', methods=['PUT'])
def update_player_permission_group(game_id):
    data = request.get_json()
    new_permission_group = data.get('permission_group')

    # 检查新权限组是否合法
    if new_permission_group not in ['Player', 'Graduate Engineer', 'Engineer', 'Senior Engineer', 'Admin']:
        return jsonify({"message": "无效的权限组"}), 400

    conn = sqlite3.connect(PLAYERS_DATABASE)
    cursor = conn.cursor()
    # 更新玩家的权限组
    cursor.execute('UPDATE players SET permission_group =? WHERE game_id =?', (new_permission_group, game_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "玩家权限组修改成功"}), 200

if __name__ == '__main__':
    init_users_db()  # 初始化用户数据库
    init_settings_db()  # 初始化设置数据库
    init_players_db()  # 初始化玩家数据库
    app.run(debug=True, host='127.0.0.1', port=5000)