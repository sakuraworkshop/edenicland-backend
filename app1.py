import re
import sqlite3
import bcrypt
from flask import Flask, request, jsonify, session
from flask_cors import CORS

# 数据库文件路径
USERS_DB_PATH = 'users.db'
SETTINGS_DB_PATH = 'settings.db'

app = Flask(__name__)
# 添加跨域支持，允许所有来源的请求
CORS(app)

# 初始化 users.db 数据库
def init_users_db():
    conn = sqlite3.connect(USERS_DB_PATH)
    c = conn.cursor()

    # 创建 users 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password BLOB,  # 修改为 BLOB 类型以存储二进制数据
            email TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')

    conn.commit()
    conn.close()

# 初始化 settings.db 数据库
def init_settings_db():
    conn = sqlite3.connect(SETTINGS_DB_PATH)
    c = conn.cursor()

    # 创建 settings 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            minecraftServerIP TEXT,
            mcsmApiAddress TEXT,
            emailServiceHost TEXT,
            mcsmDaemonId TEXT,
            emailServicePort TEXT,
            mcsmInstanceId TEXT,
            emailServiceUsername TEXT,
            mcsmApikey TEXT,
            emailServicePassword TEXT
        )
    ''')

    conn.commit()
    conn.close()

# 创建管理员用户
def create_admin_user():
    admin_username = "admin"
    admin_password = "admin123"
    admin_email = "admin@example.com"

    # 对密码进行哈希处理
    hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())

    try:
        # 获取数据库连接
        conn = sqlite3.connect(USERS_DB_PATH)
        c = conn.cursor()

        # 检查管理员用户是否已经存在
        c.execute("SELECT * FROM users WHERE username =?", (admin_username,))
        existing_user = c.fetchone()

        if existing_user:
            print("Admin user already exists.")
        else:
            # 插入管理员用户记录
            c.execute("INSERT INTO users (username, password, email, is_active) VALUES (?,?,?,?)",
                      (admin_username, sqlite3.Binary(hashed_password), admin_email, 1))
            conn.commit()
            print("Admin user created successfully.")
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    finally:
        # 关闭数据库连接
        if conn:
            conn.close()

# 获取 users.db 数据库连接
def get_users_db_connection():
    return sqlite3.connect(USERS_DB_PATH)

# 获取 settings.db 数据库连接
def get_settings_db_connection():
    return sqlite3.connect(SETTINGS_DB_PATH)

# 调用初始化函数确保数据库表存在
init_users_db()
init_settings_db()

# 调用创建管理员用户函数
create_admin_user()

# 模拟用户注册（可根据需求完善）
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 输入验证
    if not username or not email or not password:
        return jsonify({"message": "Username, email and password are required"}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"message": "Invalid email format"}), 400
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters long"}), 400

    try:
        # 传入数据库文件的完整路径
        conn = get_users_db_connection()
        c = conn.cursor()
        # 对密码进行哈希处理
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            # 插入用户数据
            c.execute("INSERT INTO users (username, email, password, is_active) VALUES (?,?,?,?)", 
                      (username, email, sqlite3.Binary(hashed_password), 1))
            conn.commit()
            return jsonify({"message": "User registered successfully"}), 201
        except sqlite3.IntegrityError:
            return jsonify({"message": "Username already exists"}), 409
        except sqlite3.Error as e:
            return jsonify({"message": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"message": f"Failed to connect to database: {str(e)}"}), 500

# 登录接口
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 输入验证
    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    try:
        # 传入数据库文件的完整路径
        conn = get_users_db_connection()
        c = conn.cursor()
        try:
            c.execute("SELECT * FROM users WHERE username =?", (username,))
            user = c.fetchone()
            if user:
                if user[3] == 0:  # 检查用户是否被封禁
                    return jsonify({"message": "Your account has been banned"}), 403
                else:
                    # 验证密码
                    stored_password = user[2]
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                        session['user_id'] = username  # 记录用户名到 session 中
                        return jsonify({"message": "Login successful"}), 200
                    else:
                        return jsonify({"message": "Username or password is incorrect"}), 401
            else:
                return jsonify({"message": "Username or password is incorrect"}), 401
        except sqlite3.Error as e:
            return jsonify({"message": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"message": f"Failed to connect to database: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)