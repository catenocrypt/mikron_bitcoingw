import bitcoingw_db
import os

def reinit_db():
    if os.path.exists(bitcoingw_db.get_db_name()):
        os.remove(bitcoingw_db.get_db_name())
    bitcoingw_db.create_dbs()

### reinit_db()