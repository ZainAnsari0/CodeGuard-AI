import sqlite3

def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # SAFE: Parameterized query prevents SQL injection
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result

def search_users(name_filter):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # SAFE: Parameterized query with LIKE
    cursor.execute("SELECT * FROM users WHERE name LIKE ?", (f"%{name_filter}%",))
    results = cursor.fetchall()
    conn.close()
    return results

def delete_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # SAFE: Parameterized query for DELETE
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()