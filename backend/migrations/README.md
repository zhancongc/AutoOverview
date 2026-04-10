# 数据库迁移脚本

此目录包含数据库迁移脚本，用于在生产环境中更新数据库结构。

## 🎯 迁移系统特性

- ✅ **版本控制**：基于版本表的迁移系统，自动跳过已执行的迁移
- ✅ **幂等性**：迁移可重复执行，不会产生错误或重复数据
- ✅ **执行记录**：在 `schema_versions` 表中记录所有已执行的迁移
- ✅ **顺序保证**：按版本号顺序执行迁移，确保依赖关系正确

## 📝 迁移脚本命名规范

使用三位数字版本号 + 描述性名称：
- `001_init_plans.py` - 初始化套餐价格表
- `002_add_user_fields.py` - 添加用户字段
- `003_create_index_table.py` - 创建索引表

## 🚀 使用方式

### 1. 查看迁移状态

```bash
# 查看迁移状态
python backend/migrations/base.py status

# 输出示例：
# 总迁移数: 3
# 已执行: 2
# 待执行: 1
#
# 迁移列表:
# ------------------------------------------------------------
# ✓ 001 - init plans
# ✓ 002 - add user fields
# ⊙ 003 - create index table
```

### 2. 执行所有待执行的迁移

```bash
# 自动执行所有待执行的迁移
python backend/migrations/base.py migrate

# 或在 server-update.sh 中自动执行
sudo ./server-update.sh
```

### 3. 执行指定版本的迁移

```bash
# 执行特定版本的迁移
python backend/migrations/base.py migrate --version 002
```

## 📋 迁移脚本模板

使用 `template.py` 作为新迁移脚本的模板：

```bash
# 复制模板
cp backend/migrations/template.py backend/migrations/002_my_migration.py

# 编辑脚本，实现 Migration 类的 up() 方法
```

### 迁移脚本示例

```python
#!/usr/bin/env python3
"""数据库迁移脚本：XXX"""
from base import Migration
from database import db
from sqlalchemy import text

class MyMigration(Migration):
    def __init__(self):
        super().__init__("002", "我的迁移")

    def up(self):
        """执行迁移"""
        # 创建表
        with next(db.get_session()) as session:
            session.execute(text("""
                CREATE TABLE example_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                )
            """))
            session.commit()

    def down(self):
        """回滚迁移（可选）"""
        with next(db.get_session()) as session:
            session.execute(text("DROP TABLE IF EXISTS example_table"))
            session.commit()

# 创建迁移实例
migration = MyMigration()
```

## 🔧 迁移基类 API

### SchemaVersion 表

```python
class SchemaVersion:
    version: str      # 迁移版本号（主键）
    name: str         # 迁移名称
    applied_at: datetime # 执行时间
```

### 核心函数

- `ensure_version_table()` - 确保 schema_versions 表存在
- `is_applied(version)` - 检查迁移是否已执行
- `record_migration(version, name)` - 记录已执行的迁移
- `get_applied_migrations()` - 获取已执行的迁移列表
- `get_pending_migrations(dir)` - 获取待执行的迁移
- `run_migration(dir, version)` - 运行迁移

### Migration 基类

```python
class Migration:
    def __init__(self, version: str, name: str)
    def up(self)           # 执行迁移（必须实现）
    def down(self)         # 回滚迁移（可选）
    def run(self)           # 运行迁移（自动检查版本）
```

## 📊 版本表结构

```sql
CREATE TABLE schema_versions (
    version VARCHAR(20) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ⚙️ 部署集成

迁移脚本会在 `server-update.sh` 中自动执行：

```bash
# [6/10] 检查并执行数据库迁移...
$PROJECT_DIR/backend/.venv/bin/python $PROJECT_DIR/backend/migrations/base.py migrate
✓ 数据库迁移完成
```

## 📝 已完成的迁移

- ✅ `001_init_plans.py` - 初始化套餐价格表
  - 创建 plans 表
  - 初始化默认套餐数据（体验包、标准包、进阶包）

## ⚠️ 注意事项

1. **版本号唯一性**：每个迁移必须有唯一的版本号
2. **不可变性**：已执行的迁移脚本不应修改（如需修改，创建新版本）
3. **向前兼容**：新迁移应考虑旧数据的存在
4. **测试优先**：在开发环境测试迁移后再部署到生产环境
5. **备份建议**：执行重要迁移前建议备份数据库

## 🔍 故障排查

### 迁移显示"已执行"但数据库未更新

检查 schema_versions 表：
```sql
SELECT * FROM schema_versions;
```

如果需要重新执行，删除对应记录：
```sql
DELETE FROM schema_versions WHERE version = '001';
```

### 迁移执行失败

1. 查看错误日志
2. 检查数据库连接
3. 验证迁移脚本语法
4. 手动执行测试：
   ```bash
   python backend/migrations/001_init_plans.py
   ```
