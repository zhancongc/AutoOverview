"""
积分服务
"""
from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import random
import string

from models.credits import CreditPackage, CreditTransaction, CreditOrder, CREDIT_PACKAGES, CREDIT_COSTS
from authkit.models import User


class CreditService:
    """积分服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_balance(self, user_id: int) -> int:
        """获取用户积分余额"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        return user.credit_balance

    def consume_credits(
        self,
        user_id: int,
        action: str,
        related_id: str = None
    ) -> Tuple[bool, str]:
        """
        消费积分

        Args:
            user_id: 用户ID
            action: 操作类型（如 generate_review）
            related_id: 关联ID（如任务ID）

        Returns:
            (success, message)
        """
        cost = CREDIT_COSTS.get(action, 0)

        if cost == 0:
            return True, "免费操作"

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"

        balance = user.credit_balance
        if balance < cost:
            return False, f"积分不足，需要 {cost} 积分，当前余额 {balance} 积分"

        try:
            # 消费积分
            transaction = user.consume_credits(
                amount=cost,
                description=self._get_consume_description(action),
                related_id=related_id
            )
            self.db.add(transaction)
            self.db.commit()

            return True, f"消费 {cost} 积分成功"

        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def add_credits(
        self,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: str,
        related_id: str = None
    ) -> Tuple[bool, str]:
        """
        增加积分

        Args:
            user_id: 用户ID
            amount: 积分数量
            transaction_type: 交易类型（purchase/reward/refund）
            description: 描述
            related_id: 关联ID

        Returns:
            (success, message)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"

        try:
            transaction = user.add_credits(
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                related_id=related_id
            )
            self.db.add(transaction)
            self.db.commit()

            return True, f"增加 {amount} 积分成功"

        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_packages(self) -> list:
        """获取积分套餐列表"""
        packages = []
        for pkg_data in CREDIT_PACKAGES:
            packages.append({
                "id": len(packages) + 1,
                **pkg_data
            })
        return packages

    def create_order(
        self,
        user_id: int,
        package_id: int
    ) -> Tuple[bool, str, Optional[str]]:
        """
        创建充值订单

        Args:
            user_id: 用户ID
            package_id: 套餐ID

        Returns:
            (success, message, order_no)
        """
        packages = self.get_packages()
        package = next((p for p in packages if p["id"] == package_id), None)

        if not package:
            return False, "套餐不存在", None

        # 生成订单号
        order_no = self._generate_order_no()

        try:
            order = CreditOrder(
                order_no=order_no,
                user_id=user_id,
                package_id=package_id,
                amount=package["credits"],
                amount_paid=package["price"],
                payment_status="pending"
            )
            self.db.add(order)
            self.db.commit()

            return True, "订单创建成功", order_no

        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def complete_order(
        self,
        order_no: str,
        payment_method: str = "wechat"
    ) -> Tuple[bool, str]:
        """
        完成订单支付

        Args:
            order_no: 订单号
            payment_method: 支付方式

        Returns:
            (success, message)
        """
        order = self.db.query(CreditOrder).filter(
            CreditOrder.order_no == order_no
        ).first()

        if not order:
            return False, "订单不存在"

        if order.payment_status == "paid":
            return False, "订单已支付"

        try:
            # 更新订单状态
            order.payment_status = "paid"
            order.paid_at = datetime.utcnow()
            order.payment_method = payment_method

            # 增加用户积分
            user = self.db.query(User).filter(User.id == order.user_id).first()
            transaction = user.add_credits(
                amount=order.amount,
                transaction_type="purchase",
                description=f"购买积分套餐：{order.package.name}",
                related_id=order_no
            )
            self.db.add(transaction)
            self.db.commit()

            return True, f"支付成功，获得 {order.amount} 积分"

        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_transaction_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> list:
        """获取用户交易记录"""
        transactions = self.db.query(CreditTransaction).filter(
            CreditTransaction.user_id == user_id
        ).order_by(CreditTransaction.created_at.desc()).limit(limit).all()

        return [
            {
                "id": t.id,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "type": t.transaction_type,
                "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transactions
        ]

    def _generate_order_no(self) -> str:
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"ORD{timestamp}{random_str}"

    def _get_consume_description(self, action: str) -> str:
        """获取消费描述"""
        descriptions = {
            "generate_review": "生成综述",
            "export_review": "导出综述",
            "save_draft": "保存草稿",
            "analyze_topic": "分析题目",
            "search_papers": "搜索文献",
        }
        return descriptions.get(action, action)
