"""
添加性能优化索引
执行方式: python3 migrations/002_add_indexes.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from sqlalchemy import text

INDEXES = [
    # ReviewRecord: 用户记录按时间查询
    "CREATE INDEX IF NOT EXISTS idx_review_records_user_id_created_at ON review_records (user_id, created_at)",

    # ReviewTask: 用户任务按时间查询
    "CREATE INDEX IF NOT EXISTS idx_review_tasks_user_id_created_at ON review_tasks (user_id, created_at)",

    # ReviewTask: 用户按状态过滤
    "CREATE INDEX IF NOT EXISTS idx_review_tasks_user_id_status ON review_tasks (user_id, status)",
]

if __name__ == "__main__":
    if db.engine is None:
        db.connect()

    with db.engine.connect() as conn:
        for sql in INDEXES:
            print(f"Executing: {sql}")
            conn.execute(text(sql))
        conn.commit()

    print("Done. All indexes created.")
