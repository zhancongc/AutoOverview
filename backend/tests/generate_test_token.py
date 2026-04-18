#!/usr/bin/env python3
"""
生成测试用 JWT Token

用法：
    cd backend
    .venv/bin/python tests/generate_test_token.py              # 列出用户，为第一个生成 token
    .venv/bin/python tests/generate_test_token.py --user-id 3  # 指定用户 ID
    .venv/bin/python tests/generate_test_token.py --email test@example.com  # 指定邮箱

生成的 token 可用于 API 测试：
    TEST_AUTH_TOKEN=eyJ... .venv/bin/python -m pytest tests/test_api_endpoints.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()
load_dotenv('.env.auth', override=True)

from datetime import timedelta
from authkit.core.security import create_access_token
from authkit.core.config import config


def list_users(session):
    """列出数据库中的用户"""
    from authkit.models import User
    users = session.query(User).order_by(User.id).limit(20).all()
    if not users:
        print("数据库中没有用户")
        return []
    print(f"{'ID':<5} {'邮箱':<35} {'积分':<8} {'已购买':<8}")
    print("-" * 60)
    result = []
    for u in users:
        credits = u.get_meta("review_credits", 0)
        free = u.get_meta("free_credits", 0)
        purchased = u.get_meta("has_purchased", False)
        print(f"{u.id:<5} {u.email:<35} {credits + free:<8} {'✓' if purchased else '✗':<8}")
        result.append(u)
    return result


def generate_token(user_id: int, email: str, long_lived: bool = True):
    """生成 JWT token"""
    if long_lived:
        # 30 天有效
        token = create_access_token(
            {"sub": str(user_id), "email": email},
            expires_delta=timedelta(days=30)
        )
    else:
        token = create_access_token({"sub": str(user_id), "email": email})
    return token


def main():
    import argparse
    parser = argparse.ArgumentParser(description="生成测试用 JWT Token")
    parser.add_argument("--user-id", type=int, help="指定用户 ID")
    parser.add_argument("--email", type=str, help="指定用户邮箱")
    args = parser.parse_args()

    from database import db

    with next(db.get_session()) as session:
        users = list_users(session)

        target_user = None

        if args.user_id:
            from authkit.models import User
            target_user = session.query(User).filter(User.id == args.user_id).first()
            if not target_user:
                print(f"用户 ID {args.user_id} 不存在")
                sys.exit(1)

        elif args.email:
            from authkit.models import User
            target_user = session.query(User).filter(User.email == args.email).first()
            if not target_user:
                print(f"用户 {args.email} 不存在")
                sys.exit(1)

        elif users:
            target_user = users[0]
            print(f"\n默认使用第一个用户: {target_user.email} (ID: {target_user.id})")

        if not target_user:
            print("\n没有可用的用户。请先注册一个测试用户。")
            sys.exit(1)

        token = generate_token(target_user.id, target_user.email)

        print(f"\n{'=' * 60}")
        print(f"用户: {target_user.email} (ID: {target_user.id})")
        print(f"Token 有效期: 30 天")
        print(f"{'=' * 60}")
        print(f"\n{token}")
        print(f"\n{'=' * 60}")
        print("使用方式：")
        print(f"  export TEST_AUTH_TOKEN={token}")
        print(f"  .venv/bin/python -m pytest tests/test_api_endpoints.py -v")
        print(f"{'=' * 60}")

        # 写入 .env 文件
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                content = f.read()
            lines = content.split("\n")
            new_lines = []
            found = False
            for line in lines:
                if line.startswith("TEST_AUTH_TOKEN="):
                    new_lines.append(f"TEST_AUTH_TOKEN={token}")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"\nTEST_AUTH_TOKEN={token}")
            with open(env_file, "w") as f:
                f.write("\n".join(new_lines))
            print(f"\n✓ 已写入 {env_file}")


if __name__ == "__main__":
    main()
