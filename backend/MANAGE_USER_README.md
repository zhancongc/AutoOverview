# 用户管理工具

用户管理脚本 `manage_user.py` 用于管理用户和综述记录。

## 功能

### 1. 查看用户信息
显示用户的邮箱、ID、额度信息和综述记录列表。

```bash
python manage_user.py show-user --email user@example.com
```

### 2. 设置综述状态

将综述设置为免费生成待解锁状态（有水印、不能导出Word）：
```bash
python manage_user.py set-record-status --email user@example.com --record-id 136 --unpaid
```

将综述设置为付费生成已解锁状态（无水印、可以导出Word）：
```bash
python manage_user.py set-record-status --email user@example.com --topic "xxx" --paid
```

### 3. 更新用户额度

增加免费额度：
```bash
python manage_user.py update-credits --email user@example.com --free-credits +1
```

减少免费额度：
```bash
python manage_user.py update-credits --email user@example.com --free-credits -1
```

设置免费额度：
```bash
python manage_user.py update-credits --email user@example.com --free-credits 5
```

增加付费额度：
```bash
python manage_user.py update-credits --email user@example.com --paid-credits +3
```

同时更新免费额度和付费额度：
```bash
python manage_user.py update-credits --email user@example.com --free-credits +1 --paid-credits +3
```

## 参数说明

### 通用参数
- `--email`: 用户邮箱（必需）

### set-record-status 参数
- `--topic`: 综述主题（可选，与 --record-id 二选一）
- `--record-id`: 综述ID（可选，与 --topic 二选一）
- `--paid`: 设置为已付费状态
- `--unpaid`: 设置为待付费状态

### update-credits 参数
- `--free-credits`: 免费额度，支持 `+1`、`-1`、`5` 等格式
- `--paid-credits`: 付费额度，支持 `+1`、`-1`、`5` 等格式

## 示例

查看用户信息：
```bash
python manage_user.py show-user --email zhancongc@icloud.com
```

输出：
```
============================================================
用户信息
============================================================
ID: 1
邮箱: zhancongc@icloud.com

额度信息:
  免费额度 (free_credits): 0
  付费额度 (review_credits): 0
  已购买 (has_purchased): False

综述记录 (1 条):
  [136] 基于专利文本挖掘的健康建筑技术主题识别分析
      状态: 🔒 待付费 | 创建时间: 2026-04-07 01:32:21
============================================================
```

设置综述为待付费状态：
```bash
python manage_user.py set-record-status --email zhancongc@icloud.com --record-id 136 --unpaid
```

增加用户额度：
```bash
python manage_user.py update-credits --email zhancongc@icloud.com --free-credits +1 --paid-credits +3
```
