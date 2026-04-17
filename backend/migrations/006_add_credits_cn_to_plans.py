#!/usr/bin/env python3
"""
数据库迁移脚本：为 plans 表添加 credits_cn 字段

版本: 006
用途: 支持中英文站积分分离，中文站积分独立于英文站 credits
"""
from base import Migration
from database import db
from sqlalchemy import text


PLAN_CREDITS_CN = {
    "single": 2,
    "semester": 6,
    "yearly": 18,
    "unlock": 0,
}


class AddCreditsCnToPlansMigration(Migration):
    """为 plans 表添加 credits_cn 字段（中文站积分额度）"""

    def __init__(self):
        super().__init__("006", "add credits_cn to plans")

    def up(self):
        print("  执行迁移：为 plans 表添加 credits_cn 字段...")

        with next(db.get_session()) as session:
            session.execute(text("""
                ALTER TABLE plans
                ADD COLUMN IF NOT EXISTS credits_cn INTEGER
            """))

            for plan_type, credits_cn in PLAN_CREDITS_CN.items():
                session.execute(text("""
                    UPDATE plans SET credits_cn = :credits_cn WHERE type = :ptype
                """), {"credits_cn": credits_cn, "ptype": plan_type})

            session.commit()

        print("    ✓ credits_cn 字段已添加并初始化")
        print("  ✓ 迁移完成")

    def down(self):
        print("  回滚迁移：删除 plans 表 credits_cn 字段...")

        with next(db.get_session()) as session:
            session.execute(text("ALTER TABLE plans DROP COLUMN IF EXISTS credits_cn"))
            session.commit()

        print("    ✓ credits_cn 字段已删除")
        print("  ✓ 回滚完成")


migration = AddCreditsCnToPlansMigration()


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
