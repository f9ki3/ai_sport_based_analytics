from connection import *
import hashlib
from datetime import datetime
import json
from collections import defaultdict

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

    def getPerformanceById(id):    
        with Connection() as cursor:
            cursor.execute('''
                SELECT * FROM performance
                WHERE id = ?
            ''', (id,))
            perf = cursor.fetchone()

            if perf is None:
                # Return default structure if nothing is found
                return {
                    "processed_video_url": None,
                    "stats": {}
                }

            try:
                stats_dict = json.loads(perf[2]) if perf[2] else {}
            except json.JSONDecodeError:
                stats_dict = {}

            return {
                "processed_video_url": perf[1],
                "stats": stats_dict
            }

    def getPerformandashboard(user_id):
        with Connection() as cursor:
            cursor.execute('''
                SELECT stats, user_id, date
                FROM performance
                WHERE user_id = ?
            ''', (user_id,))
            performances = cursor.fetchall()

        data_by_date = defaultdict(lambda: {"player1_sum": 0, "player1_count": 0, "player2_sum": 0, "player2_count": 0})

        for stats_json, _, date in performances:
            stats = json.loads(stats_json) if stats_json else {}

            p1_strength = stats.get("Player_1", {}).get("average_smash_strength")
            p2_strength = stats.get("Player_2", {}).get("average_smash_strength")

            if p1_strength is not None:
                data_by_date[date]["player1_sum"] += p1_strength
                data_by_date[date]["player1_count"] += 1

            if p2_strength is not None:
                data_by_date[date]["player2_sum"] += p2_strength
                data_by_date[date]["player2_count"] += 1


        # Build the response dictionary
        response = {
            "dates": [],
            "player1": [],
            "player2": []
        }

        for date in sorted(data_by_date.keys()):
            response["dates"].append(date)
            p1_data = data_by_date[date]
            p1_avg = (p1_data["player1_sum"] / p1_data["player1_count"]) if p1_data["player1_count"] > 0 else None
            response["player1"].append(p1_avg)

            p2_avg = (p1_data["player2_sum"] / p1_data["player2_count"]) if p1_data["player2_count"] > 0 else None
            response["player2"].append(p2_avg)

        return response

if __name__ == "__main__":
    # Users.createTableUsers()
    # Performance.createTablePerformance()
    data = Performance.getPerformandashboard(1)
    print(data)