"""
Migration: email_contacts 新增 template_variant 和 unsubscribed 字段
"""
from base import Migration
from database import db
from sqlalchemy import text


class AddEmailContactsVariantMigration(Migration):

    def __init__(self):
        super().__init__("013", "add template_variant and unsubscribed to email_contacts")

    def up(self):
        with next(db.get_session()) as session:
            session.execute(text("""
                ALTER TABLE email_contacts
                ADD COLUMN IF NOT EXISTS template_variant VARCHAR(2),
                ADD COLUMN IF NOT EXISTS unsubscribed BOOLEAN DEFAULT FALSE
            """))
            session.commit()
        print("  ✓ email_contacts 新增 template_variant、unsubscribed 字段")

    def down(self):
        with next(db.get_session()) as session:
            session.execute(text("""
                ALTER TABLE email_contacts
                DROP COLUMN IF EXISTS template_variant,
                DROP COLUMN IF EXISTS unsubscribed
            """))
            session.commit()
        print("  ✓ 回滚完成")


migration = AddEmailContactsVariantMigration()
