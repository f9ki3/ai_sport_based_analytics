import sqlite3

class Connection:
    def __init__(self):
        self.conn = sqlite3.connect('database.db')
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self.cursor
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        self.conn.commit()
        self.conn.close()

if __name__ == "__main__":
    Connection()