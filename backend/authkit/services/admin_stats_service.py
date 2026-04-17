"""
管理员统计服务 - 汇总所有用户数据
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


class AdminStatsService:
    """管理员统计服务"""

    def __init__(self, db: Session, redis_client=None):
        self.db = db
        self.redis_client = redis_client

    def get_overview_stats(self) -> dict:
        """获取统计概览（总数据）"""
        from ..models.stats import SiteStats
        from models import ReviewRecord, ReviewTask
        from authkit.models.payment import Subscription
        from authkit.models import User

        # 1. 总访问量（从 Redis 或数据库）
        total_visits = self._get_total_visits()

        # 2. 总注册量
        total_registers = self.db.query(func.count(User.id)).scalar() or 0

        # 3. 总生成数（含免费）
        total_generations = self.db.query(func.count(ReviewRecord.id)).filter(
            ReviewRecord.status == "success"
        ).scalar() or 0

        # 免费生成数
        free_generations = self.db.query(func.count(ReviewRecord.id)).filter(
            and_(
                ReviewRecord.status == "success",
                ReviewRecord.is_paid == False
            )
        ).scalar() or 0

        # 付费生成数
        paid_generations = total_generations - free_generations

        # 4. 付费统计（按套餐类型）
        payment_stats = self._get_payment_stats()

        # 5. 今日数据
        today_stats = self._get_today_stats()

        # 6. 北极星指标
        funnel_stats = self._get_funnel_stats()

        return {
            "visits": {
                "total": total_visits,
                "today": today_stats.get("today_visits", 0)
            },
            "registers": {
                "total": total_registers,
                "today": today_stats.get("today_registers", 0)
            },
            "generations": {
                "total": total_generations,
                "free": free_generations,
                "paid": paid_generations
            },
            "payments": payment_stats,
            "today": today_stats,
            "funnel": funnel_stats
        }

    def get_daily_stats(self, days: int = 30) -> list:
        """获取每日统计数据（最近 N 天）"""
        from ..models.stats import SiteStats
        from models import ReviewRecord
        from authkit.models import User
        from authkit.models.payment import Subscription

        result = []
        today = date.today()

        for i in range(days):
            stat_date = (today - timedelta(days=days - 1 - i)).isoformat()
            date_obj = date.fromisoformat(stat_date)

            # 访问量（从 Redis 或数据库）
            visits = self._get_visits_by_date(stat_date)

            # 注册量
            registers = self.db.query(func.count(User.id)).filter(
                func.date(User.created_at) == date_obj
            ).scalar() or 0

            # 生成数
            generations = self.db.query(func.count(ReviewRecord.id)).filter(
                and_(
                    ReviewRecord.status == "success",
                    func.date(ReviewRecord.created_at) == date_obj
                )
            ).scalar() or 0

            # 按货币统计付费数和收入
            daily_payment_stats = self.db.query(
                Subscription.currency,
                func.count(Subscription.id).label('count'),
                func.sum(Subscription.amount).label('revenue')
            ).filter(
                and_(
                    Subscription.status == "paid",
                    func.date(Subscription.payment_time) == date_obj
                )
            ).group_by(Subscription.currency).all()

            payments_by_currency = {}
            total_payments = 0
            for currency, count, revenue in daily_payment_stats:
                curr = currency or "CNY"
                payments_by_currency[curr] = {
                    "count": count,
                    "revenue": float(revenue) if revenue else 0.0
                }
                total_payments += count

            # 确保 CNY 和 USD 都存在
            for curr in ["CNY", "USD"]:
                if curr not in payments_by_currency:
                    payments_by_currency[curr] = {
                        "count": 0,
                        "revenue": 0.0
                    }

            result.append({
                "date": stat_date,
                "visits": visits,
                "registers": registers,
                "generations": generations,
                "payments": total_payments,
                "payments_by_currency": payments_by_currency
            })

        return result

    def _get_total_visits(self) -> int:
        """获取总访问量"""
        if self.redis_client:
            # 从 Redis 获取最近 7 天的访问量
            total = 0
            for i in range(7):
                date_str = (date.today() - timedelta(days=i)).isoformat()
                visit_key = f"stats:visits:{date_str}"
                visits = self.redis_client.get(visit_key)
                if visits:
                    total += int(visits)

            # 加上数据库中的历史数据
            from ..models.stats import SiteStats
            db_visits = self.db.query(func.sum(SiteStats.visit_count)).scalar() or 0
            total += db_visits
            return total
        else:
            # 从数据库获取
            from ..models.stats import SiteStats
            return self.db.query(func.sum(SiteStats.visit_count)).scalar() or 0

    def _get_visits_by_date(self, stat_date: str) -> int:
        """获取指定日期的访问量"""
        if self.redis_client:
            visit_key = f"stats:visits:{stat_date}"
            visits = self.redis_client.get(visit_key)
            if visits:
                return int(visits)

        # 降级到数据库
        from ..models.stats import SiteStats
        stats = self.db.query(SiteStats).filter_by(stat_date=stat_date).first()
        return stats.visit_count if stats else 0

    def _get_payment_stats(self) -> dict:
        """获取付费统计（按套餐类型和货币）"""
        from authkit.models.payment import Subscription

        # 按货币统计
        currency_stats = self.db.query(
            Subscription.currency,
            func.count(Subscription.id).label('count'),
            func.sum(Subscription.amount).label('revenue')
        ).filter(
            Subscription.status == "paid"
        ).group_by(Subscription.currency).all()

        by_currency = {}
        total_orders = 0
        for currency, count, revenue in currency_stats:
            curr = currency or "CNY"
            by_currency[curr] = {
                "total_orders": count,
                "total_revenue": float(revenue) if revenue else 0.0
            }
            total_orders += count

        # 确保 CNY 和 USD 都存在
        for curr in ["CNY", "USD"]:
            if curr not in by_currency:
                by_currency[curr] = {
                    "total_orders": 0,
                    "total_revenue": 0.0
                }

        # 按套餐类型+货币统计
        plan_currency_stats = self.db.query(
            Subscription.plan_type,
            Subscription.currency,
            func.count(Subscription.id).label('count'),
            func.sum(Subscription.amount).label('revenue')
        ).filter(
            Subscription.status == "paid"
        ).group_by(Subscription.plan_type, Subscription.currency).all()

        # 初始化按套餐统计
        plans = {}
        plan_names = {
            "single": {"CNY": "体验包", "USD": "Starter"},
            "semester": {"CNY": "标准包", "USD": "Semester Pro"},
            "yearly": {"CNY": "进阶包", "USD": "Annual Premium"},
            "unlock": {"CNY": "单次解锁", "USD": "Single Unlock"}
        }

        for plan_type in plan_names.keys():
            plans[plan_type] = {}
            for curr in ["CNY", "USD"]:
                plans[plan_type][curr] = {
                    "count": 0,
                    "revenue": 0.0,
                    "name": plan_names[plan_type][curr]
                }

        # 填充实际数据
        for plan_type, currency, count, revenue in plan_currency_stats:
            curr = currency or "CNY"
            if plan_type in plans and curr in plans[plan_type]:
                plans[plan_type][curr]["count"] = count
                plans[plan_type][curr]["revenue"] = float(revenue) if revenue else 0.0

        return {
            "total_orders": total_orders,
            "by_currency": by_currency,
            "by_plan": plans
        }

    def _get_today_stats(self) -> dict:
        """获取今日统计"""
        from ..models.stats import SiteStats
        from models import ReviewRecord
        from authkit.models import User
        from authkit.models.payment import Subscription

        today = date.today()

        # 今日访问量
        today_visits = self._get_visits_by_date(today.isoformat())

        # 今日注册量
        today_registers = self.db.query(func.count(User.id)).filter(
            func.date(User.created_at) == today
        ).scalar() or 0

        # 今日生成数
        today_generations = self.db.query(func.count(ReviewRecord.id)).filter(
            and_(
                ReviewRecord.status == "success",
                func.date(ReviewRecord.created_at) == today
            )
        ).scalar() or 0

        # 今日按货币统计付费数和收入
        today_payment_stats = self.db.query(
            Subscription.currency,
            func.count(Subscription.id).label('count'),
            func.sum(Subscription.amount).label('revenue')
        ).filter(
            and_(
                Subscription.status == "paid",
                func.date(Subscription.payment_time) == today
            )
        ).group_by(Subscription.currency).all()

        today_payments_by_currency = {}
        total_today_payments = 0
        for currency, count, revenue in today_payment_stats:
            curr = currency or "CNY"
            today_payments_by_currency[curr] = {
                "count": count,
                "revenue": float(revenue) if revenue else 0.0
            }
            total_today_payments += count

        # 确保 CNY 和 USD 都存在
        for curr in ["CNY", "USD"]:
            if curr not in today_payments_by_currency:
                today_payments_by_currency[curr] = {
                    "count": 0,
                    "revenue": 0.0
                }

        return {
            "today_visits": today_visits,
            "today_registers": today_registers,
            "today_generations": today_generations,
            "today_payments": total_today_payments,
            "today_payments_by_currency": today_payments_by_currency
        }

    def _get_funnel_stats(self) -> dict:
        """获取北极星指标（漏斗统计）"""
        from models import ReviewTask, ReviewRecord
        from datetime import timedelta

        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # 1. 搜索 UV - 最近 30 天的总访问量
        search_uv = 0
        for i in range(30):
            date_str = (today - timedelta(days=i)).isoformat()
            search_uv += self._get_visits_by_date(date_str)

        # 2. 计算预览 -> 矩阵转化率
        # 预览任务：type == "search_only"
        preview_tasks = self.db.query(func.count(ReviewTask.id)).filter(
            and_(
                ReviewTask.created_at >= thirty_days_ago,
                ReviewTask.params.op('->>')('type') == 'search_only'
            )
        ).scalar() or 0

        # 矩阵任务：type == "comparison_matrix_only"
        matrix_tasks = self.db.query(func.count(ReviewTask.id)).filter(
            and_(
                ReviewTask.created_at >= thirty_days_ago,
                ReviewTask.params.op('->>')('type') == 'comparison_matrix_only'
            )
        ).scalar() or 0

        preview_to_matrix_rate = 0.0
        if preview_tasks > 0:
            preview_to_matrix_rate = matrix_tasks / preview_tasks

        # 3. 计算矩阵 -> 综述转化率
        # 综述任务（有 review_record_id 的任务，且不是 comparison_matrix_only）
        review_tasks = self.db.query(func.count(ReviewTask.id)).filter(
            and_(
                ReviewTask.created_at >= thirty_days_ago,
                ReviewTask.review_record_id.isnot(None),
                ReviewTask.params.op('->>')('type') != 'comparison_matrix_only'
            )
        ).scalar() or 0

        matrix_to_review_rate = 0.0
        if matrix_tasks > 0:
            matrix_to_review_rate = review_tasks / max(matrix_tasks, 1)

        # 4. Credits 消耗速率 - 最近 30 天的总消耗
        # 计算所有任务的 credit_cost 总和
        all_tasks_30d = self.db.query(ReviewTask).filter(
            ReviewTask.created_at >= thirty_days_ago
        ).all()

        total_credits_consumed = 0
        for task in all_tasks_30d:
            params = task.params or {}
            credit_cost = params.get("credit_cost", 0)
            total_credits_consumed += credit_cost

        # 计算日均消耗
        daily_credit_rate = total_credits_consumed / 30.0

        return {
            "search_uv": search_uv,
            "preview_to_matrix_rate": round(preview_to_matrix_rate * 100, 2),
            "matrix_to_review_rate": round(matrix_to_review_rate * 100, 2),
            "total_credits_consumed": total_credits_consumed,
            "daily_credit_rate": round(daily_credit_rate, 2),
            "preview_tasks": preview_tasks,
            "matrix_tasks": matrix_tasks,
            "review_tasks": review_tasks
        }
