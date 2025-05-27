from connection import *
import hashlib

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





if __name__ == "__main__":
    Users.createTableUsers()