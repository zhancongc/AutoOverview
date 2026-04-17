"""
临时脚本：查看特定任务的详细数据
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from database import db

def check():
    """检查任务详情"""
    print("查看任务 1b095d28 的详细数据...")

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查看 paper_search_stages 数据
        print("\n1. Paper Search Stages 数据：")
        result = session.execute(text("""
            SELECT id, task_id, papers_count, papers_summary, papers_sample, status
            FROM paper_search_stages
            WHERE task_id = '1b095d28'
        """))
        stages = result.fetchall()

        if stages:
            for stage in stages:
                print(f"  - id: {stage[0]}")
                print(f"    task_id: {stage[1]}")
                print(f"    papers_count: {stage[2]}")
                print(f"    status: {stage[5]}")
                if stage[3]:
                    print(f"    papers_summary: {stage[3]}")
                if stage[4]:
                    try:
                        papers_sample = stage[4]
                        if isinstance(papers_sample, str):
                            papers_sample = json.loads(papers_sample)
                        print(f"    papers_sample count: {len(papers_sample)}")
                    except Exception as e:
                        print(f"    解析 papers_sample 失败: {e}")
        else:
            print("  没有找到相关记录")

if __name__ == "__main__":
    check()
