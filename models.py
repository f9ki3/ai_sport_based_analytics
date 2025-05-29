from connection import *
import hashlib
from datetime import datetime

class Users():
    def createTableUsers():
        with Connection() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fullname TEXT NOT NULL,
                    email TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            print("Users table created successfully.")

    def insertUser(fullname, email, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        with Connection() as cursor:
            cursor.execute('''
                INSERT INTO users (fullname, email, password)
                VALUES (?, ?, ?)
            ''', (fullname, email, hashed_password))
            print("User inserted successfully.")

    def login(email, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        with Connection() as cursor:
            cursor.execute('''
                SELECT * FROM users
                WHERE email = ? AND password = ?
            ''', (email, hashed_password))
            user = cursor.fetchone()
            if user:
                print("Login successful.")
                return {
                    "id": user[0],
                    "fullname": user[1],
                    "email": user[2]
                }
            else:
                print("Invalid email or password.")
                return None
            
    def getUserById(id):
        with Connection() as cursor:
            cursor.execute('''
                SELECT * FROM users
                WHERE id = ?
            ''', (id,))
            user = cursor.fetchone()
            if user:
                return {
                    "id": user[0],
                    "fullname": user[1],
                    "email": user[2]
                }
            else:
                print("User not found.")
                return None
            
    def updateUser(id, fullname, email):
        with Connection() as cursor:
            cursor.execute('''
                UPDATE users
                SET fullname = ?, email = ?
                WHERE id = ?
            ''', (fullname, email, id))
            print("User updated successfully.")
    
    def updatePassword(id, password):
        with Connection() as cursor:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('''
                UPDATE users
                SET password = ?
                WHERE id = ?
            ''', (hashed_password, id))
            print("Password updated successfully.")

class Performance():
    def createTablePerformance():
        with Connection() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    processed_video_url TEXT NOT NULL,
                    stats TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            print("Performance table created successfully.")
    
    def insertPerformance(processed_video_url, stats, user_id):
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with Connection() as cursor:
            cursor.execute('''
                INSERT INTO performance (processed_video_url, stats, user_id, date)
                VALUES (?, ?, ?, ?)
            ''', (processed_video_url, stats, user_id, date))
            print("Performance inserted successfully.")
    
    def deletePerformance(id):
        with Connection() as cursor:
            cursor.execute('''
                DELETE FROM performance
                WHERE id = ?
            ''', (id,))
            print("Performance deleted successfully.")

    def getPerformanceByUserId(user_id):    
        with Connection() as cursor:
            cursor.execute('''
                SELECT * FROM performance
                WHERE user_id = ?
            ''', (user_id,))
            performances = cursor.fetchall()
            return [{
                "id": perf[0],
                "processed_video_url": perf[1],
                "stats": perf[2],
                "user_id": perf[3],
                "date": perf[4]
            } for perf in performances]
            print("Performance retrieved successfully.")
    




if __name__ == "__main__":
    Users.createTableUsers()
    Performance.createTablePerformance()