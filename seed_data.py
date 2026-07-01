#!/usr/bin/env python3
"""
Seed script: membuat user dan data dummy.
Jalankan: python seed_data.py
"""
import asyncio
import datetime
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, async_session
from app.models import Order, User
from sqlalchemy import select

USERS = [
    {"username": "john",   "password": "admin123", "api_key": os.getenv("OTPK_instanAPI_KEY", ""), "server": "s5"},
    {"username": "semut",  "password": "123456",   "api_key": "", "server": "s5"},
    {"username": "nanang", "password": "123456",   "api_key": "", "server": "s5"},
]

DUMMY_ORDERS = [
    ("S5-987654321", "628123456789", "wa", 6, 3200, "received", "957418", "sukses", 3),
    ("S5-987654322", "628234567890", "tg", 6, 2800, "received", "123456", "gagal", 8),
    ("S5-987654323", "628345678901", "ig", 6, 4500, "pending", None, None, 12),
    ("S5-987654324", "628456789012", "wa", 6, 3200, "received", "789012", "sukses", 18),
    ("S5-987654325", "628567890123", "wa", 6, 3200, "cancelled", None, None, 22),
    ("S5-987654326", "628678901234", "tg", 6, 2800, "received", "345678", "sukses", 28),
    ("S5-987654327", "628789012345", "sh", 6, 1800, "pending", None, None, 35),
    ("S5-987654328", "628890123456", "wa", 6, 3200, "received", "654321", "gagal", 42),
]


async def seed():
    await init_db()

    async with async_session() as session:
        # Cek apakah sudah ada data
        existing = await session.scalar(select(User).limit(1))
        if existing:
            print("Database sudah berisi data. Lewati seed.")
            return

        # Buat user
        for u in USERS:
            session.add(User(
                username=u["username"],
                password=u["password"],
                api_key=u["api_key"],
                server=u["server"],
            ))

        # Buat dummy orders untuk john (sebagai demo)
        now = datetime.datetime.utcnow()
        for (order_id, phone, service, country, price,
             status, otp_code, client_status, minutes_ago) in DUMMY_ORDERS:
            created_at = now - datetime.timedelta(minutes=minutes_ago)
            otp_updated = None
            if otp_code:
                otp_updated = created_at + datetime.timedelta(
                    minutes=random.randint(1, 3)
                )

            order = Order(
                order_id=order_id,
                phone=phone,
                service=service,
                country=country,
                price=price,
                status=status,
                otp_code=otp_code,
                otp_updated_at=otp_updated,
                client_status=client_status,
                created_at=created_at,
                updated_at=created_at,
                username="john",
            )
            session.add(order)

        await session.commit()
        print(f"Seed: {len(USERS)} user + {len(DUMMY_ORDERS)} order dummy.")


if __name__ == "__main__":
    asyncio.run(seed())
