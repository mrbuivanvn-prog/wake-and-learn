
import sqlite3
import os

def migrate():
    db_path = os.path.join(os.getcwd(), 'wakelearn.db')
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Checking database columns...")
    
    try:
        # Add profession column to user_settings if it doesn't exist
        cursor.execute("ALTER TABLE user_settings ADD COLUMN profession VARCHAR(100) DEFAULT 'Tổng quát'")
        print("Added 'profession' column to user_settings")
    except sqlite3.OperationalError as e:
        print(f"Column 'profession' error: {e}")

    try:
        # Add learning_language column to user_settings if it doesn't exist
        cursor.execute("ALTER TABLE user_settings ADD COLUMN learning_language VARCHAR(10) DEFAULT 'en'")
        print("Added 'learning_language' column to user_settings")
    except sqlite3.OperationalError as e:
        print(f"Column 'learning_language' error: {e}")

    conn.commit()
    conn.close()
    print("Migration finished!")

if __name__ == "__main__":
    migrate()
