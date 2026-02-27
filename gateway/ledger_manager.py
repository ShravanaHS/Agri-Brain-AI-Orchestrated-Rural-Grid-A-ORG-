import sqlite3
import os
import time

class LedgerManager:
    def __init__(self, db_path="gateway/farm_ledger.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                raw_text TEXT,
                action TEXT,
                material TEXT,
                quantity TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_entry(self, raw_text, action, material, quantity):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ledger (raw_text, action, material, quantity)
            VALUES (?, ?, ?, ?)
        ''', (raw_text, action, material, quantity))
        conn.commit()
        conn.close()
        return True

    def get_history(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ledger ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows

if __name__ == "__main__":
    lm = LedgerManager()
    lm.add_entry("Added 5kg Potash", "ADD", "POTASH", "5KG")
    print(lm.get_history())
