"""
Migration: 创建 user_feedback 表
"""
from base import Migration
from database import db
from sqlalchemy import text


class CreateUserFeedbackMigration(Migration):
    """创建 user_feedback 表"""

    def __init__(self):
        super().__init__("009", "create user_feedback table")

    def up(self):
        with next(db.get_session()) as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    email VARCHAR(255) DEFAULT '',
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.commit()
        print("  ✓ user_feedback 表创建完成")

    def down(self):
        with next(db.get_session()) as session:
            session.execute(text("DROP TABLE IF EXISTS user_feedback"))
            session.commit()
        print("  ✓ user_feedback 表已移除")


migration = CreateUserFeedbackMigration()
