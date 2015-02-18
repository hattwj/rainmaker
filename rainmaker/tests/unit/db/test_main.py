from rainmaker.main import Application
import rainmaker.db.main

def test_db_init():
    rainmaker.db.main.init_db()
