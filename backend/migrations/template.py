#!/usr/bin/env python3
"""
数据库迁移脚本模板

版本: XXX
用途: [描述此迁移的目的]

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


class TemplateMigration(Migration):
    """迁移模板类"""

    def __init__(self):
        super().__init__("XXX", "迁移名称")

    def up(self):
        """执行迁移"""
        print("  执行迁移...")

        # 示例1: 创建表
        # with next(db.get_session()) as session:
        #     session.execute(text("""
        #         CREATE TABLE example_table (
        #             id SERIAL PRIMARY KEY,
        #             name VARCHAR(100) NOT NULL
        #         )
        #     """))
        #     session.commit()

        # 示例2: 添加字段
        # with next(db.get_session()) as session:
        #     session.execute(text("""
        #         ALTER TABLE users
        #         ADD COLUMN IF NOT EXISTS new_field VARCHAR(50)
        #     """))
        #     session.commit()

        # 示例3: 插入数据
        # with next(db.get_session()) as session:
        #     session.execute(text("""
        #         INSERT INTO config (key, value)
        #         VALUES ('feature_flag', 'true')
        *         ON CONFLICT (key) DO NOTHING
        #     """))
        #     session.commit()

        print("  ✓ 迁移完成")

    def down(self):
        """回滚迁移（可选）"""
        print("  回滚迁移...")

        # 示例回滚操作
        # with next(db.get_session()) as session:
        #     session.execute(text("DROP TABLE IF EXISTS example_table"))
        #     session.commit()

        print("  ✓ 回滚完成")


# 创建迁移实例（供 base.py 调用）
migration = TemplateMigration()


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
