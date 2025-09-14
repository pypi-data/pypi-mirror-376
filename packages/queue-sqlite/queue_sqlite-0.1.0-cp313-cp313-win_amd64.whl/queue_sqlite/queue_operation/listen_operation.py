from ..mounter.listen_mounter import ListenMounter
import sqlite3
from typing import List, Tuple, Union


class ListenOperation:
    def __init__(self, db_dir):
        self.db_dir = db_dir
        self.listen_fields = ListenMounter.get_Listener_list()
        self.create_table()

    def create_table(self):
        if len(self.listen_fields) == 0:
            return
        sql = f"""
            CREATE TABLE IF NOT EXISTS listen_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key Text,
                value JSON
            );
            CREATE TABLE IF NOT EXISTS change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                row_id INTEGER,
                column_name TEXT,
                old_value TEXT,
                new_value TEXT,
                is_delete integer DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TRIGGER IF NOT EXISTS track_value_change
            AFTER UPDATE OF value ON listen_table  -- 监听特定列
            FOR EACH ROW
            WHEN OLD.value <> NEW.value    -- 仅当值实际变化时触发
            BEGIN
                INSERT INTO change_log (table_name, row_id, column_name, old_value, new_value)
                VALUES ('listen_table', NEW.id, 'key', OLD.key, NEW.key);
            END;
        """
        self.conn = sqlite3.connect(
            self.db_dir,
            check_same_thread = False,
        )
        self.conn.executescript(sql)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA cache_size=-20000;")
        self.conn.execute("PRAGMA mmap_size=1073741824;")
        self.conn.execute("PRAGMA temp_store=MEMORY;")
        self.conn.execute("PRAGMA busy_timeout=5000;")
        self.conn.commit()

        # 删除原有数据
        # sql = f"""
        #     DELETE FROM listen_table
        # """
        # self.conn.execute(sql)
        # self.conn.commit()

        for listen_field in self.listen_fields:
            sql = f"""
                INSERT INTO 
                    listen_table (key, value)
                VALUES 
                    (?, ?)
            """
            self.conn.execute(sql, (listen_field, "null"))
            self.conn.commit()
    
    def listen_data(self) -> Tuple[bool, Union[List[Tuple], str]]:
        sql = f"""
            SELECT * FROM change_log where is_delete = 0 ORDER BY id DESC LIMIT 100
        """
        result = self.conn.execute(sql).fetchall()
        if len(result) == 0:
            return False, "No data found"
        return True, result
        
        
    def delete_change_log(self, delete_id):
        sql = f"""
            DELETE FROM change_log WHERE id = {delete_id}
        """
        self.conn.execute(sql)
        
    def update_listen_data(self, key, value):
        sql = f"""
            UPDATE listen_table SET value = '{value}' WHERE key = '{key}'
        """
        self.conn.execute(sql)
        self.conn.commit()

    def get_value(self, key):
        sql = f"""
            SELECT value FROM listen_table WHERE key = '{key}'
        """
        result = self.conn.execute(sql).fetchone()
        if result is None:
            return None
        return result[0]
    
    def get_values(self):
        sql = f"""
            SELECT key, value FROM listen_table
        """
        result = self.conn.execute(sql).fetchall()
        return result
