import sqlite3

# 数据库文件路径
DATABASE = 'users.db'


def create_admin(username, email, password):
    try:
        # 连接数据库
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # 检查 id 为 0 的用户是否已存在
        cursor.execute('SELECT * FROM users WHERE id = 0')
        existing_user = cursor.fetchone()
        if existing_user:
            print("id 为 0 的用户已存在")
            return False

        # 插入 id 为 0 的管理员用户，密码明文保存
        cursor.execute('INSERT INTO users (id, username, email, password, is_active) VALUES (?,?,?,?,?)',
                       (0, username, email, password, 1))
        conn.commit()
        print("id 为 0 的管理员用户创建成功")
        return True
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # 你可以修改以下信息来创建不同的管理员用户
    admin_username = "admin"
    admin_email = "admin@example.com"
    admin_password = "admin123"

    create_admin(admin_username, admin_email, admin_password)