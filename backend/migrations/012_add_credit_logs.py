"""
Migration: 创建 credit_logs 积分变动记录表
"""
from base import Migration
from database import db
from sqlalchemy import text


class AddCreditLogsMigration(Migration):

    def __init__(self):
        super().__init__("012", "add credit_logs table")

    def up(self):
        with next(db.get_session()) as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS credit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    change INTEGER NOT NULL,
                    balance_before INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    reason VARCHAR(100) NOT NULL,
                    detail TEXT,
                    operator VARCHAR(100) DEFAULT 'system',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_credit_logs_user_id ON credit_logs (user_id)
            """))
            session.commit()
        print("  ✓ credit_logs 表已创建")

    def down(self):
        with next(db.get_session()) as session:
            session.execute(text("DROP TABLE IF EXISTS credit_logs"))
            session.commit()
        print("  ✓ 回滚完成")


migration = AddCreditLogsMigration()
