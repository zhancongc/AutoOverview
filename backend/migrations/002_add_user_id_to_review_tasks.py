#!/usr/bin/env python3
"""
数据库迁移脚本：添加 user_id 字段到 review_tasks 表

版本: 002
用途: 为 review_tasks 表添加 user_id 字段和索引，用于关联登录用户的搜索任务

命名规范: XXX_name.py
  - XXX: 三位数字版本号（001, 002, 003...）
  - name: 描述性名称，使用下划线分隔
  - 示例: 001_init_plans.py, 002_add_user_fields.py

注意:
  - 由版本控制系统管理，无需检查重复执行
  - SQL 直接执行即可，版本号会控制是否跳过
  - 如需回滚，实现 down() 方法
"""
from base import Migration
from database import db
from sqlalchemy import text


class AddUserIdToReviewTasksMigration(Migration):
    """添加 user_id 字段到 review_tasks 表"""

    def __init__(self):
        super().__init__("002", "add user_id to review_tasks")

    def up(self):
        """执行迁移"""
        print("  执行迁移：添加 user_id 字段到 review_tasks 表...")

        # 添加字段
        with next(db.get_session()) as session:
            session.execute(text("""
                ALTER TABLE review_tasks
                ADD COLUMN IF NOT EXISTS user_id INTEGER
            """))
            session.commit()
        print("    ✓ user_id 字段已添加")

        # 添加索引
        with next(db.get_session()) as session:
            # 检查索引是否已存在
            result = session.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'review_tasks'
                AND indexname = 'idx_review_tasks_user_id'
            """))
            exists = result.fetchone()

            if not exists:
                session.execute(text("""
                    CREATE INDEX idx_review_tasks_user_id ON review_tasks (user_id)
                """))
                session.commit()
                print("    ✓ idx_review_tasks_user_id 索引已添加")
            else:
                print("    - idx_review_tasks_user_id 索引已存在，跳过")

        print("  ✓ 迁移完成")

    def down(self):
        """回滚迁移（可选）"""
        print("  回滚迁移：删除 review_tasks 表的 user_id 字段...")

        # 删除索引
        with next(db.get_session()) as session:
            session.execute(text("""
                DROP INDEX IF EXISTS idx_review_tasks_user_id
            """))
            session.commit()
        print("    ✓ idx_review_tasks_user_id 索引已删除")

        # 删除字段
        with next(db.get_session()) as session:
            session.execute(text("""
                ALTER TABLE review_tasks
                DROP COLUMN IF EXISTS user_id
            """))
            session.commit()
        print("    ✓ user_id 字段已删除")

        print("  ✓ 回滚完成")


# 创建迁移实例（供 base.py 调用）
migration = AddUserIdToReviewTasksMigration()


# 保留独立的 main 函数用于手动执行
def main():
    """手动执行迁移"""
    migration.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print(f"错误：迁移失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
