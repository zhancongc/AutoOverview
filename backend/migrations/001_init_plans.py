#!/usr/bin/env python3
"""
数据库迁移脚本：初始化套餐价格表

版本: 001
用途:
  - 创建 plans 表
  - 初始化默认套餐数据

注意: 由版本控制系统管理，无需手动检查重复执行
"""
from base import Migration
from database import db
from authkit.models.payment import Plan, PaymentBase, init_plans_in_db


class InitPlansMigration(Migration):
    """初始化套餐价格表"""

    def __init__(self):
        super().__init__("001", "初始化套餐价格表")

    def up(self):
        """执行迁移"""
        # 创建表
        print("  [1/2] 创建 plans 表...")
        PaymentBase.metadata.create_all(bind=db.engine)
        print("  ✓ plans 表已创建")

        # 初始化数据（不需要检查是否已存在，版本号会控制）
        print("  [2/2] 初始化套餐数据...")
        with next(db.get_session()) as session:
            init_plans_in_db(session)

        print("  ✓ 套餐数据初始化完成")
        print()
        print("  当前套餐列表：")
        plans = session.query(Plan).order_by(Plan.sort_order).all()
        for plan in plans:
            status = "推荐" if plan.recommended else "  "
            print(f"    [{status}] {plan.name} ({plan.type})")
            print(f"        价格: ¥{plan.price}")
            print(f"        额度: {plan.credits} 篇")

    def down(self):
        """回滚迁移"""
        print("  回滚套餐价格表...")
        from sqlalchemy import text
        session = next(db.get_session())
        try:
            session.execute(text("DROP TABLE IF EXISTS plans CASCADE"))
            session.commit()
            print("  ✓ plans 表已删除")
        finally:
            session.close()


# 创建迁移实例（供 base.py 调用）
migration = InitPlansMigration()


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
