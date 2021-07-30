import ast, sqlite3

def create_table():
    with sqlite3.connect('current_results.db') as db:
        c = db.cursor()
        c.execute("""CREATE TABLE current_results (
            chat_id integer,
            results text
            )""")

def insert_results(chat_id, results):
    with sqlite3.connect('current_results.db') as db:
        c = db.cursor()
        c.execute("INSERT INTO current_results VALUES (?,?)", (chat_id, results))

def exists(chat_id):
    with sqlite3.connect('current_results.db') as db:
        c = db.cursor()
        c.execute("SELECT * FROM current_results WHERE chat_id=(?)", (chat_id,))
        return len(c.fetchall()) > 0

def update_results(chat_id, results):
    with sqlite3.connect('current_results.db') as db:
        c = db.cursor()
        c.execute("UPDATE current_results SET results = ? WHERE chat_id = ?", (results, chat_id))

def get_results(chat_id):
    with sqlite3.connect('current_results.db') as db:
        c = db.cursor()
        c.execute("SELECT * FROM current_results WHERE chat_id = ?", (chat_id,))
        tmp = c.fetchall()
        if len(tmp) > 1:
            raise Exception("Multiple records found!")
        results = tmp[0][1]
        return ast.literal_eval(results)

if __name__ == 'db':
    db = sqlite3.connect('current_results.db')
    c = db.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='current_results'")
    if len(c.fetchall()) == 0:
        create_table()

