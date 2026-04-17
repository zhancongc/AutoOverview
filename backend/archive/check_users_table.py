"""
临时脚本：查看用户表
"""
import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from database import db

def check():
    """检查用户表"""
    print("检查用户表...")

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查看所有表
        print("\n1. 数据库中的所有表：")
        result = session.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        rows = result.fetchall()
        for row in rows:
            print(f"  - {row[0]}")

        # 查找用户相关的表
        print("\n2. 用户相关的表：")
        result = session.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE '%user%'
            ORDER BY tablename
        """))
        rows = result.fetchall()
        for row in rows:
            print(f"  - {row[0]}")

        # 如果找到 users 表，查看结构
        print("\n3. 尝试查看 users 表结构：")
        try:
            result = session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """))
            rows = result.fetchall()
            for row in rows:
                print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        except Exception as e:
            print(f"  错误: {e}")

        # 查看用户数据
        print("\n4. users 表中的数据：")
        try:
            result = session.execute(text("""
                SELECT id, email, nickname
                FROM users
                LIMIT 5
            """))
            rows = result.fetchall()
            for row in rows:
                print(f"  - id: {row[0]}, email: {row[1]}, nickname: {row[2]}")
        except Exception as e:
            print(f"  错误: {e}")

if __name__ == "__main__":
    check()
