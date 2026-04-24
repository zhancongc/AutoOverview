"""
Migration: site_stats 和 visit_logs 表新增 site 字段
"""
from base import Migration
from database import db
from sqlalchemy import text


class AddSiteToStatsMigration(Migration):
    """为 site_stats 和 visit_logs 添加 site 字段，支持按站点区分统计数据"""

    def __init__(self):
        super().__init__("010", "add site column to site_stats and visit_logs")

    def up(self):
        with next(db.get_session()) as session:
            # 1. site_stats 添加 site 字段
            session.execute(text("""
                ALTER TABLE site_stats
                ADD COLUMN IF NOT EXISTS site VARCHAR(10) DEFAULT 'zh'
            """))

            # 2. visit_logs 添加 site 字段
            session.execute(text("""
                ALTER TABLE visit_logs
                ADD COLUMN IF NOT EXISTS site VARCHAR(10) DEFAULT 'zh'
            """))

            # 3. 删除旧的 stat_date 唯一约束，改为 (stat_date, site) 联合唯一
            session.execute(text("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.table_constraints
                        WHERE constraint_name = 'site_stats_stat_date_key'
                        AND table_name = 'site_stats'
                    ) THEN
                        ALTER TABLE site_stats DROP CONSTRAINT site_stats_stat_date_key;
                    END IF;
                END;
                $$
            """))

            session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints
                        WHERE constraint_name = 'uq_site_stats_date_site'
                        AND table_name = 'site_stats'
                    ) THEN
                        ALTER TABLE site_stats ADD CONSTRAINT uq_site_stats_date_site UNIQUE (stat_date, site);
                    END IF;
                END;
                $$
            """))

            session.commit()
        print("  ✓ site_stats / visit_logs 添加 site 字段完成")

    def down(self):
        with next(db.get_session()) as session:
            session.execute(text("ALTER TABLE site_stats DROP CONSTRAINT IF EXISTS uq_site_stats_date_site"))
            session.execute(text("ALTER TABLE site_stats DROP COLUMN IF EXISTS site"))
            session.execute(text("ALTER TABLE visit_logs DROP COLUMN IF EXISTS site"))
            session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints
                        WHERE constraint_name = 'site_stats_stat_date_key'
                        AND table_name = 'site_stats'
                    ) THEN
                        ALTER TABLE site_stats ADD CONSTRAINT site_stats_stat_date_key UNIQUE (stat_date);
                    END IF;
                END;
                $$
            """))
            session.commit()
        print("  ✓ 回滚完成")


migration = AddSiteToStatsMigration()
