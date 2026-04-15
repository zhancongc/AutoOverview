#!/usr/bin/env python3
"""
数据库迁移脚本：添加 currency 字段到 subscriptions 表

版本: 003
用途: 为 subscriptions 表添加 currency 字段，用于区分 CNY 和 USD

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


class AddCurrencyToSubscriptionsMigration(Migration):
    """添加 currency 字段到 subscriptions 表"""

    def __init__(self):
        super().__init__("003", "add currency to subscriptions")

    def up(self):
        """执行迁移"""
        print("  执行迁移：添加 currency 字段到 subscriptions 表...")

        # 添加字段
        with next(db.get_session()) as session:
            session.execute(text("""
                ALTER TABLE subscriptions
                ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY'
            """))
            session.commit()
        print("    ✓ currency 字段已添加")

        # 为现有数据设置默认值
        with next(db.get_session()) as session:
            # 根据 order_no 前缀判断货币类型
            # - AO 开头（支付宝）：CNY
            # - PP 开头（PayPal）：USD
            # - PD 开头（Paddle）：USD
            session.execute(text("""
                UPDATE subscriptions
                SET currency = CASE
                    WHEN order_no LIKE 'PP%' THEN 'USD'
                    WHEN order_no LIKE 'PD%' THEN 'USD'
                    ELSE 'CNY'
                END
                WHERE currency IS NULL
            """))
            session.commit()
        print("    ✓ 现有数据已更新")

        print("  ✓ 迁移完成")

    def down(self):
        """回滚迁移（可选）"""
        print("  回滚迁移：删除 subscriptions 表的 currency 字段...")

        # 删除字段
        with next(db.get_session()) as session:
            session.execute(text("""
                ALTER TABLE subscriptions
                DROP COLUMN IF EXISTS currency
            """))
            session.commit()
        print("    ✓ currency 字段已删除")

        print("  ✓ 回滚完成")


# 创建迁移实例（供 base.py 调用）
migration = AddCurrencyToSubscriptionsMigration()


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
