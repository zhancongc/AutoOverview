"""
Migration: 创建 email_contacts 表
"""
from base import Migration
from database import db
from sqlalchemy import text


class AddEmailContactsMigration(Migration):

    def __init__(self):
        super().__init__("011", "add email_contacts table")

    def up(self):
        with next(db.get_session()) as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS email_contacts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200),
                    email VARCHAR(500) NOT NULL,
                    position VARCHAR(200),
                    source_url TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    sent_at TIMESTAMP,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            session.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_email_contacts_email
                ON email_contacts (email)
            """))
            session.commit()
        print("  ✓ email_contacts 表已创建")

    def down(self):
        with next(db.get_session()) as session:
            session.execute(text("DROP TABLE IF EXISTS email_contacts"))
            session.commit()
        print("  ✓ 回滚完成")


migration = AddEmailContactsMigration()
