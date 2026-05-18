
import sqlite3
import os

def migrate():
    db_path = os.path.join(os.getcwd(), 'wakelearn.db')
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns_to_add = [
        ("word_en", "VARCHAR(200)"),
        ("word_zh", "VARCHAR(200)"),
        ("pinyin", "VARCHAR(200)"),
        ("example_zh", "TEXT")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE vocabularies ADD COLUMN {col_name} {col_type}")
            print(f"Added column '{col_name}' to vocabularies")
        except sqlite3.OperationalError:
            print(f"Column '{col_name}' already exists")

    conn.commit()
    conn.close()
    print("Migration finished!")

if __name__ == "__main__":
    migrate()
