#!/usr/bin/env python3
"""
数据库迁移脚本：为 plans 表添加国际化字段

版本: 004
用途: 添加 name_en, price_usd, original_price, original_price_usd,
      features_en, badge, badge_en 字段到 plans 表
"""
from base import Migration
from database import db
from sqlalchemy import text


class AddPlanI18nFieldsMigration(Migration):
    """为 plans 表添加国际化和扩展字段"""

    def __init__(self):
        super().__init__("004", "add i18n fields to plans")

    def up(self):
        """执行迁移"""
        print("  执行迁移：为 plans 表添加国际化字段...")

        columns = [
            ("name_en", "VARCHAR(100)"),
            ("price_usd", "FLOAT"),
            ("original_price", "FLOAT"),
            ("original_price_usd", "FLOAT"),
            ("features_en", "TEXT"),
            ("badge", "VARCHAR(50)"),
            ("badge_en", "VARCHAR(50)"),
        ]

        with next(db.get_session()) as session:
            for col_name, col_type in columns:
                session.execute(text(f"""
                    ALTER TABLE plans
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                """))
            session.commit()

        print("    ✓ 国际化字段已添加")
        print("  ✓ 迁移完成")

    def down(self):
        """回滚迁移"""
        print("  回滚迁移：删除 plans 表的国际化字段...")

        columns = [
            "badge_en", "badge", "features_en",
            "original_price_usd", "original_price", "price_usd", "name_en",
        ]

        with next(db.get_session()) as session:
            for col_name in columns:
                session.execute(text(f"""
                    ALTER TABLE plans DROP COLUMN IF EXISTS {col_name}
                """))
            session.commit()

        print("    ✓ 国际化字段已删除")
        print("  ✓ 回滚完成")


migration = AddPlanI18nFieldsMigration()


def main():
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
