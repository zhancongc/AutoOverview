#!/usr/bin/env python3
"""
导入联系人 CSV 到数据库

用法:
    cd backend && python3 scripts/import_contacts.py contacts.csv
    cd backend && python3 scripts/import_contacts.py data.csv --reset  # 清空后重新导入

CSV 格式:
    name,email,position,source_url
    Sophie Green,sophie@manchester.ac.uk,PhD Student,https://...
"""
import argparse
import csv
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.auth"))

from database import db
from sqlalchemy import text


def main():
    parser = argparse.ArgumentParser(description="导入联系人 CSV")
    parser.add_argument("csv_file", help="CSV 文件路径")
    parser.add_argument("--reset", action="store_true", help="清空表后重新导入")
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        print(f"文件不存在: {args.csv_file}")
        sys.exit(1)

    # 连接数据库
    for session in db.get_session():
        if args.reset:
            session.execute(text("DELETE FROM email_contacts"))
            session.commit()
            print("已清空 email_contacts 表")

        # 读取已有邮箱（去重）
        existing = {row[0] for row in session.execute(text("SELECT email FROM email_contacts")).fetchall()}

        total = 0
        added = 0
        skipped = 0
        errors = 0

        with open(args.csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                total += 1
                name = (row.get("name") or "").strip()
                email = (row.get("email") or "").strip().lower()
                position = (row.get("position") or "").strip()
                source_url = (row.get("source_url") or "").strip()

                if not email or "@" not in email:
                    print(f"  跳过（邮箱无效）: {email or row}")
                    errors += 1
                    continue

                if email in existing:
                    skipped += 1
                    continue

                session.execute(text("""
                    INSERT INTO email_contacts (name, email, position, source_url)
                    VALUES (:name, :email, :position, :source_url)
                """), dict(name=name, email=email, position=position, source_url=source_url))
                existing.add(email)
                added += 1

        session.commit()

        print(f"\n导入完成:")
        print(f"  CSV 总行数: {total}")
        print(f"  新增: {added}")
        print(f"  跳过（已存在）: {skipped}")
        print(f"  跳过（格式错误）: {errors}")
        print(f"  数据库总计: {session.execute(text('SELECT COUNT(*) FROM email_contacts')).scalar()}")


if __name__ == "__main__":
    main()
