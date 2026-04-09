#!/usr/bin/env python
"""
支付宝应用私钥格式转换脚本
将 PKCS#8 格式私钥转换为 PKCS#1 格式（rsa 库需要）

使用方法：
    python convert_private_key.py
"""
import os


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    secrets_path = os.path.join(base_dir, "secrets.txt")

    if not os.path.exists(secrets_path):
        print(f"错误: 找不到 secrets.txt: {secrets_path}")
        return

    print(f"读取私钥文件: {secrets_path}")

    # 读取原始内容
    with open(secrets_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    print(f"原始内容长度: {len(content)}")

    # 准备 PKCS#8 PEM 格式
    if '-----BEGIN' not in content:
        # 纯 base64 内容，添加 PKCS#8 标记
        pkcs8_pem = f"-----BEGIN PRIVATE KEY-----\n{content}\n-----END PRIVATE KEY-----"
        print("检测到纯 base64 内容，已添加 PKCS#8 标记")
    else:
        pkcs8_pem = content
        if 'BEGIN RSA PRIVATE KEY' in pkcs8_pem:
            print("私钥已经是 PKCS#1 格式，无需转换")
            return
        print("检测到 PKCS#8 格式私钥")

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
    except ImportError:
        print("\n错误: 需要安装 cryptography 库")
        print("运行: pip install cryptography")
        return

    # 加载 PKCS#8 私钥
    private_key_obj = serialization.load_pem_private_key(
        pkcs8_pem.encode(),
        password=None,
        backend=default_backend()
    )

    # 转换为 PKCS#1 格式 (TraditionalOpenSSL)
    pkcs1_pem = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    print("\n转换成功！")

    # 提取 base64 内容（不含标记）保存回 secrets.txt
    lines = pkcs1_pem.decode().split('\n')
    base64_content = '\n'.join([l for l in lines if l and not l.startswith('-----')])

    with open(secrets_path, 'w', encoding='utf-8') as f:
        f.write(base64_content)

    print(f"已保存 PKCS#1 格式私钥到: {secrets_path}")
    print(f"新内容长度: {len(base64_content)}")


if __name__ == "__main__":
    main()
