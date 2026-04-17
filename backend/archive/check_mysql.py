#!/usr/bin/env python3
"""
调试脚本：检查 MySQL 数据库
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.auth', override=True)

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("尝试连接 MySQL 数据库")
print("=" * 80)

try:
    import pymysql

    # MySQL 配置
    db_user = os.getenv("MYSQL_DB_USER", "root")
    db_password = os.getenv("MYSQL_DB_PASSWORD", "security")
    db_host = os.getenv("MYSQL_DB_HOST", "localhost")
    db_port = int(os.getenv("MYSQL_DB_PORT", 3306))
    db_name = os.getenv("MYSQL_DB_NAME", "paper")

    print(f"\n连接到 MySQL: {db_host}:{db_port}/{db_name}")

    # 连接 MySQL
    connection = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )

    print("✓ MySQL 连接成功！")

    try:
        with connection.cursor() as cursor:
            # 查询 review_tasks 表
            print("\n查询 review_tasks 表...")
            cursor.execute("SELECT id, topic, user_id, status, created_at FROM review_tasks ORDER BY created_at DESC LIMIT 20")
            tasks = cursor.fetchall()

            print(f"\n找到 {len(tasks)} 个任务:")
            for task in tasks:
                print(f"  - {task['id']}: {task['topic'][:50]}... (user_id: {task['user_id']}, status: {task['status']})")

                # 如果是我们要找的任务
                if task['id'] == 'f9b9e9f2':
                    print(f"\n✓ 找到任务 f9b9e9f2！")

                    # 查询 params 字段
                    cursor.execute("SELECT params FROM review_tasks WHERE id = %s", (task['id'],))
                    result = cursor.fetchone()
                    if result and result['params']:
                        import json
                        params = json.loads(result['params'])
                        print(f"  Params: {params}")

    finally:
        connection.close()

except ImportError:
    print("pymysql 未安装")
except Exception as e:
    print(f"MySQL 连接失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
