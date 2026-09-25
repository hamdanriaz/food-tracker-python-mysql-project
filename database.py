import mysql.connector
from mysql.connector import Error

def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="NeelyBetter", # <--- Replace with your MySQL root password
            database="food_tracker"
        )
        return conn
    except Error as e:
        print("DB Error:", e)
        return None


def signup_user(username, password, gender, height_cm, weight_kg, age, activity_level):
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, gender, height_cm, weight_kg, age, activity_level) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (username, password, gender, height_cm, weight_kg, age, activity_level))
        conn.commit()
        return True
    except Error as e:
        print("Signup Error:", e)
        return False
    finally:
        cursor.close()
        conn.close()

def login_user(username, password):
    conn = connect_db()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        return result
    finally:
        cursor.close()
        conn.close()


def add_meal(meal, grams, calories, user_id):
    conn = connect_db()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO meals (meal_name, grams, calories, user_id) VALUES (%s, %s, %s, %s)",
            (meal, grams, calories, user_id)
        )
        conn.commit()
    except Error as e:
        print("Insert Error:", e)
    finally:
        cursor.close()
        conn.close()

def fetch_meals_today(user_id):
    conn = connect_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT meal_name, grams, calories, date_added
            FROM meals
            WHERE DATE(date_added) = CURDATE() AND user_id = %s
        """, (user_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def clear_meals_table(user_id):
    conn = connect_db()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM meals WHERE user_id = %s", (user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def remove_users(u):
    conn = connect_db()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM users
            WHERE username = %s
        """, (u,))
        conn.commit()
        return True
    except Error as e:
        print("Remove Error:", e)
    finally:
        cursor.close()
        conn.close()
