# 用户数据结构（参考 snappicker 项目）

## users 表

### 基础字段
| 字段 | 类型 | 说明 | 参考 snappicker |
|------|------|------|----------------|
| id | Integer | 用户ID（主键） | ✓ |
| email | String(255) | 邮箱（唯一索引） | - |
| hashed_password | String(255) | 加密后的密码 | - |

### 用户信息（参考 snappicker）
| 字段 | 类型 | 说明 | snappicker 同名字段 |
|------|------|------|-------------------|
| nickname | String(100) | 昵称 | ✓ |
| avatar_url | String(500) | 头像URL | ✓ |
| gender | Integer | 性别：0-未知，1-男，2-女 | ✓ |
| country | String(50) | 国家 | ✓ |
| province | String(50) | 省份 | ✓ |
| city | String(50) | 城市 | ✓ |
| language | String(20) | 语言 | ✓ |
| phone_number | String(20) | 手机号（加密存储） | ✓ |

### 账号状态
| 字段 | 类型 | 说明 |
|------|------|------|
| is_active | Boolean | 是否活跃 |
| is_verified | Boolean | 邮箱是否验证 |
| is_superuser | Boolean | 是否超级管理员 |
| is_staff | Boolean | 是否员工（新增） |

### 论文综述相关（新增）
| 字段 | 类型 | 说明 |
|------|------|------|
| review_count | Integer | 已生成综述数量 |
| review_quota | Integer | 综述生成配额 |
| total_papers_used | Integer | 累计使用文献数量 |

### 时间字段
| 字段 | 类型 | 说明 |
|------|------|------|
| last_login_at | DateTime | 最后登录时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## review_records 表（新增）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 记录ID |
| user_id | Integer | 用户ID（外键） |
| topic | String(500) | 论文主题 |
| review | Text | 综述内容 |
| statistics | Text | 统计信息（JSON） |
| target_count | Integer | 目标文献数量 |
| recent_years_ratio | Float | 近5年占比 |
| english_ratio | Float | 英文文献占比 |
| status | String(20) | 状态 |
| error_message | Text | 错误信息 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 关联关系

```python
User.review_records → ReviewRecord (一对多)
ReviewRecord.user → User (多对一)
```

## 与 snappicker 的差异

### 移除的字段（微信小程序特有）
- `openid` - 微信用户唯一标识
- `unionid` - 开放平台唯一标识
- `session_key` - 会话密钥

### 新增的字段（论文综述业务）
- `email` - 邮箱登录
- `hashed_password` - 密码登录
- `is_staff` - 员工标识
- `review_count` - 综述数量统计
- `review_quota` - 生成配额
- `total_papers_used` - 文献使用统计

## 默认值

| 字段 | 默认值 | 说明 |
|------|--------|------|
| gender | 0 | 未知 |
| language | zh_CN | 简体中文 |
| is_active | True | 激活状态 |
| is_verified | False | 未验证 |
| is_staff | False | 非员工 |
| review_quota | 10 | 默认10次配额 |
