#!/usr/bin/env python3
"""
调试脚本：检查任务 28058ddf 的文献数据
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.auth', override=True)

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db
from models import PaperSearchStage

if __name__ == "__main__":
    task_id_to_find = "28058ddf"

    print("=" * 80)
    print(f"查找任务 ID: {task_id_to_find}")
    print("=" * 80)

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查询 PaperSearchStage
        stages = session.query(PaperSearchStage).filter_by(
            task_id=task_id_to_find
        ).order_by(PaperSearchStage.id.desc()).all()

        if stages:
            print(f"\n✓ 找到 {len(stages)} 个 PaperSearchStage 记录！\n")

            stage = stages[0]
            print(f"Stage ID: {stage.id}")
            print(f"Task ID: {stage.task_id}")
            print(f"Papers count: {stage.papers_count}")

            if stage.papers_sample:
                print(f"\nPapers sample 中有 {len(stage.papers_sample)} 篇文献\n")

                for i, paper in enumerate(stage.papers_sample):
                    title = paper.get('title', '')
                    print(f"[{i+1}] Title: {title}")
                    print(f"      Title length: {len(title)} characters")
                    if len(title) > 100:
                        print(f"      First 100 chars: {title[:100]}...")
                    print()
        else:
            print(f"\n未找到任务 ID: {task_id_to_find} 的 PaperSearchStage 记录")

    print("\n" + "=" * 80)
