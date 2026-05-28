import sqlite3

def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABLE: String concatenation in SQL query allows SQL injection
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def search_users(name_filter):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABLE: f-string interpolation in SQL query
    cursor.execute(f"SELECT * FROM users WHERE name LIKE '%{name_filter}%'")
    results = cursor.fetchall()
    conn.close()
    return results

def delete_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABLE: Direct string formatting in DELETE query
    cursor.execute("DELETE FROM users WHERE id = " + str(user_id))
    conn.commit()
    conn.close()