"""
修复 ReviewTask.user_id 为空的记录

策略：
1. 有 review_record_id 的 → 从关联的 ReviewRecord.user_id 回填
2. 无 review_record_id 的 → 无法确认归属，保持为空（这些任务会在权限检查中被拒绝）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import get_db
from models import ReviewTask, ReviewRecord


def fix():
    db = next(get_db())

    try:
        tasks = db.query(ReviewTask).filter(ReviewTask.user_id.is_(None)).all()
        print(f"找到 {len(tasks)} 条 user_id 为空的 ReviewTask")

        fixed = 0
        skipped = 0

        for task in tasks:
            if task.review_record_id:
                record = db.query(ReviewRecord).filter_by(id=task.review_record_id).first()
                if record and record.user_id:
                    task.user_id = record.user_id
                    fixed += 1
                    print(f"  [{task.id}] user_id <- {record.user_id} (from ReviewRecord #{record.id})")
                else:
                    skipped += 1
                    print(f"  [{task.id}] ReviewRecord #{task.review_record_id} 也无 user_id，跳过")
            else:
                skipped += 1
                print(f"  [{task.id}] 无 review_record_id，跳过")

        db.commit()
        print(f"\n完成：修复 {fixed} 条，跳过 {skipped} 条")

    except Exception as e:
        db.rollback()
        print(f"错误：{e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    fix()
