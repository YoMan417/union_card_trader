import sqlite3

def executesql(db_path, query, close=True):
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        db.commit()
    if close:
        cursor.close()
    return result