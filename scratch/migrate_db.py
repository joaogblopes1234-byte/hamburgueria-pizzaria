import sqlite3
import os

db_path = os.path.join('instance', 'gordin.db')

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check current columns
        cursor.execute("PRAGMA table_info('order')")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in 'order' table: {columns}")

        # Check if user_id is NOT NULL
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='order'")
        schema = cursor.fetchone()[0]
        
        if "user_id INTEGER NOT NULL" in schema or "user_id INTEGER" in schema:
            print("Recreating 'order' table to handle nullable user_id and new columns...")
            
            # Create new table
            cursor.execute("""
                CREATE TABLE order_new (
                    id INTEGER NOT NULL, 
                    date_ordered DATETIME, 
                    status VARCHAR(20), 
                    user_id INTEGER, 
                    customer_name VARCHAR(100), 
                    customer_phone VARCHAR(20), 
                    total_price FLOAT NOT NULL, 
                    delivery_fee FLOAT NOT NULL, 
                    address VARCHAR(255) NOT NULL, 
                    neighborhood_id INTEGER NOT NULL, 
                    PRIMARY KEY (id), 
                    FOREIGN KEY(user_id) REFERENCES user (id), 
                    FOREIGN KEY(neighborhood_id) REFERENCES neighborhood (id)
                )
            """)

            # Copy data
            # Map existing columns
            cols_to_copy = [c for c in columns if c in ['id', 'date_ordered', 'status', 'user_id', 'total_price', 'delivery_fee', 'address', 'neighborhood_id', 'customer_name', 'customer_phone']]
            cols_str = ", ".join(cols_to_copy)
            
            cursor.execute(f"INSERT INTO order_new ({cols_str}) SELECT {cols_str} FROM 'order'")

            # DROP and RENAME
            cursor.execute("DROP TABLE 'order'")
            cursor.execute("ALTER TABLE order_new RENAME TO 'order'")
            
            print("Table 'order' recreated and data migrated.")
        else:
            print("Schema seems already correct or unknown format.")

        conn.commit()
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
