"""
数据库迁移脚本：为 review_tasks 表添加 is_public 字段

版本: 005
用途: 添加 is_public 布尔字段，标记任务是否公开分享
"""
from base import Migration
from database import db
from sqlalchemy import text


class AddReviewTaskIsPublicMigration(Migration):
    """为 review_tasks 表添加 is_public 字段"""

    def __init__(self):
        super().__init__("007", "add is_public to review_tasks")

    def up(self):
        """执行迁移"""
        print("  执行迁移：为 review_tasks 表添加 is_public 字段...")

        with next(db.get_session()) as session:
            session.execute(text("""
                ALTER TABLE review_tasks
                ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE
            """))
            session.commit()

        print("  ✓ is_public 字段添加完成")

    def down(self):
        """回滚迁移"""
        print("  回滚迁移：移除 review_tasks.is_public 字段...")

        with next(db.get_session()) as session:
            session.execute(text("""
                ALTER TABLE review_tasks
                DROP COLUMN IF EXISTS is_public
            """))
            session.commit()

        print("  ✓ is_public 字段已移除")
