#!/usr/bin/env python3
"""
数据库迁移脚本

版本: 005
用途: 1) 将用户 review_credits 乘以 2，改为积分系统
      2) 更新 plans 表的 credits 为新的积分体系 (6/20/60)
"""
from base import Migration
from database import db
from sqlalchemy import text
import json


class CreditToPointsMigration(Migration):
    """迁移模板类"""

    def __init__(self):
        super().__init__("005", "migrate_credits_to_points")

    def up(self):
        """执行迁移"""
        with next(db.get_session()) as session:
            # === 第一步：用户积分 ×2 ===
            print("  [1/2] 执行迁移: (review_credits + free_credits) × 2 → 积分...")

            result = session.execute(text("SELECT id, meta_data FROM users"))
            users = result.fetchall()

            updated_count = 0
            for user_id, meta_data_str in users:
                if meta_data_str:
                    try:
                        meta_data = json.loads(meta_data_str)
                        review_credits = meta_data.get("review_credits", 0)
                        free_credits = meta_data.get("free_credits", 0)

                        # 总积分 = (付费 + 免费) * 2
                        total_credits = (review_credits + free_credits) * 2

                        # 更新：全部放到 review_credits，free_credits 清零
                        meta_data["review_credits"] = total_credits
                        meta_data["free_credits"] = 0

                        session.execute(
                            text("UPDATE users SET meta_data = :meta WHERE id = :id"),
                            {"meta": json.dumps(meta_data), "id": user_id}
                        )
                        updated_count += 1
                    except Exception as e:
                        print(f"    警告: 用户 {user_id} 迁移失败: {e}")

            session.commit()
            print(f"  ✓ 用户积分迁移完成，更新了 {updated_count} 个用户")

            # === 第二步：更新 plans 表的 credits ===
            print("  [2/2] 更新 plans 表 credits → 6/20/60...")

            plan_credits = {
                "single": 6,
                "semester": 20,
                "yearly": 60,
            }

            plan_features_en = {
                "single": json.dumps([
                    "6 Credits (3 reviews or 6 comparison matrices)",
                    "Online viewing + Word export",
                    "DOI-verifiable citations",
                    "Export BibTeX, XML, RIS formats",
                ]),
                "semester": json.dumps([
                    "20 Credits (10 reviews or 20 comparison matrices)",
                    "Online viewing + Word export",
                    "DOI-verifiable citations",
                    "Export BibTeX, XML, RIS formats",
                    "~$1.25/Credit",
                ]),
                "yearly": json.dumps([
                    "60 Credits (30 reviews or 60 comparison matrices)",
                    "Online viewing + Word export",
                    "DOI-verifiable citations",
                    "Export BibTeX, XML, RIS formats",
                    "~$0.75/Credit",
                ]),
            }

            for plan_type, credits in plan_credits.items():
                session.execute(
                    text("UPDATE plans SET credits = :credits WHERE type = :ptype"),
                    {"credits": credits, "ptype": plan_type}
                )
                if plan_type in plan_features_en:
                    session.execute(
                        text("UPDATE plans SET features_en = :features WHERE type = :ptype"),
                        {"features": plan_features_en[plan_type], "ptype": plan_type}
                    )

            session.commit()
            print("  ✓ Plans credits 已更新为 6/20/60")
            print("  ✓ 迁移 005 完成")

    def down(self):
        """回滚迁移：将积分除以 2，还原 plans credits"""
        with next(db.get_session()) as session:
            # 回滚用户积分
            print("  回滚迁移: 积分 ÷ 2 → review_credits...")

            result = session.execute(text("SELECT id, meta_data FROM users"))
            users = result.fetchall()

            updated_count = 0
            for user_id, meta_data_str in users:
                if meta_data_str:
                    try:
                        meta_data = json.loads(meta_data_str)
                        total_credits = meta_data.get("review_credits", 0)

                        new_review_credits = total_credits // 2

                        meta_data["review_credits"] = new_review_credits
                        meta_data["free_credits"] = 1

                        session.execute(
                            text("UPDATE users SET meta_data = :meta WHERE id = :id"),
                            {"meta": json.dumps(meta_data), "id": user_id}
                        )
                        updated_count += 1
                    except Exception as e:
                        print(f"    警告: 用户 {user_id} 回滚失败: {e}")

            session.commit()
            print(f"  ✓ 用户积分回滚完成，更新了 {updated_count} 个用户")

            # 回滚 plans credits
            print("  回滚 plans credits → 2/6/12...")
            old_plan_credits = {
                "single": 2,
                "semester": 6,
                "yearly": 12,
            }
            for plan_type, credits in old_plan_credits.items():
                session.execute(
                    text("UPDATE plans SET credits = :credits WHERE type = :ptype"),
                    {"credits": credits, "ptype": plan_type}
                )
            session.commit()
            print("  ✓ Plans credits 已回滚为 2/6/12")
            print("  ✓ 回滚 005 完成")


# 创建迁移实例（供 base.py 调用）
migration = CreditToPointsMigration()


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
