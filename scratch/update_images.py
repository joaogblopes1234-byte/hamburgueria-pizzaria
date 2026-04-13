import sqlite3
import os

def update_db(db_name):
    path = os.path.join('instance', db_name)
    if not os.path.exists(path): return
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    try:
        cur.execute("UPDATE product SET image_url='/static/img/refri_mini.jpg' WHERE name='Refri Mini'")
        cur.execute("UPDATE product SET image_url='/static/img/cola_1l.jpg' WHERE name='Refrigerante 1L'")
        cur.execute("UPDATE product SET image_url='/static/img/kuat_2l.jpg' WHERE name='Kuat 2L'")
        cur.execute("UPDATE product SET image_url='/static/img/fanta_2l.jpg' WHERE name='Fanta 2L'")
        cur.execute("UPDATE product SET image_url='/static/img/coca_2l.jpg' WHERE name='Coca 2 L'")
        conn.commit()
        print(f"Updated {db_name} to .jpg")
    except Exception as e:
        print(f"Error in {db_name}: {e}")
    finally:
        conn.close()

update_db('gordin_lanches.db')
update_db('gordin.db')
