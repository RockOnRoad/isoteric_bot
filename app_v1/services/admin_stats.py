from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import datetime, timedelta
from db.models import User, GenerationHistory, Payment


async def get_admin_stats(db_session: AsyncSession) -> dict:

    total_users = await db_session.scalar(select(func.count(User.id)))
    active_users = await db_session.scalar(
        select(func.count(User.id)).where(
            User.last_updated >= datetime.now() - timedelta(days=1)
        )
    )
    new_users_today = await db_session.scalar(
        select(func.count(User.id)).where(
            func.date(User.created_at) == func.current_date()
        )
    )
    new_users_yesterday = await db_session.scalar(
        select(func.count(User.id)).where(
            func.date(User.created_at) == func.current_date() - 1
        )
    )
    total_generations = await db_session.scalar(
        select(func.count(GenerationHistory.id))
    )
    total_payments = await db_session.scalar(
        select(func.count(Payment.id)).where(Payment.status == "completed")
    )
    payments_today = await db_session.scalar(
        select(func.count(Payment.id)).where(
            func.date(Payment.created_at) == func.current_date(),
            Payment.status == "completed",
        )
    )
    payments_yesterday = await db_session.scalar(
        select(func.count(Payment.id)).where(
            func.date(Payment.created_at) == func.current_date() - 1,
            Payment.status == "completed",
        )
    )

    leads = await db_session.scalar(
        select(func.count(User.id)).where(User.segment == "lead")
    )
    quals = await db_session.scalar(
        select(func.count(User.id)).where(User.segment == "qual")
    )
    clients = await db_session.scalar(
        select(func.count(User.id)).where(User.segment == "client")
    )
    banned = await db_session.scalar(
        select(func.count(User.id)).where(User.segment == "banned")
    )

    leads_percentage = (leads / total_users) * 100
    quals_percentage = (quals / total_users) * 100
    clients_percentage = (clients / total_users) * 100
    banned_percentage = (banned / total_users) * 100

    text = f"""
<b>✨ MatrikaSoulBot ✨</b> статистика

👥 Всего пользователей: {total_users}
🔥 Активных сегодня: {active_users}
🆕 Новых пользователей сегодня: {new_users_today}
🆕 Новых пользователей вчера: {new_users_yesterday}
🎨 Всего генераций: {total_generations}
💰 Всего платежей: {total_payments}
💳 Платежей сегодня: {payments_today}
💳 Платежей вчера: {payments_yesterday}

📈 Сегменты пользователей:
🆕 Лиды: {leads} ({leads_percentage:.2f}%)
✨ Квалы: {quals} ({quals_percentage:.2f}%)
💎 Клиенты: {clients} ({clients_percentage:.2f}%)
🚫 Забаненные: {banned} ({banned_percentage:.2f}%)
"""

    return text
