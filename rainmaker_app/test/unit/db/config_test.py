from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *


class ConfigTest(unittest.TestCase):
    
    @inlineCallbacks
    def test_init(self):
        clean_temp_dir()
        db_path = os.path.join(user_dir,'test.sqlite')
        yield initDB(db_path)
        yield tearDownDB()

