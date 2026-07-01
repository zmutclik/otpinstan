import datetime
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, desc
from app.database import async_session
from app.models import Order, User
from app.services.otpinstan import (
    create_order as otp_create_order,
    check_order as otp_check_order,
)
from app.config import get_or_create_user

router = APIRouter()


async def _get_user_api(username: str) -> str:
    user = await get_or_create_user(username)
    return user.api_key


async def _get_user_server(username: str) -> str:
    user = await get_or_create_user(username)
    return user.server


def parse_error(api_response: dict) -> str:
    if not api_response.get("success"):
        code = api_response.get("error_code", "API_ERROR")
        msg = api_response.get("message", "Unknown error")
        return f"{code}: {msg}"
    return ""


@router.get("/getotp")
async def getotp(
    username: str = Query(...),
    service: str = Query(..., description="Kode service: wa, tg, ig, dll"),
    country: int = Query(..., description="ID negara, contoh: 6 (Indonesia)"),
):
    api_key = await _get_user_api(username)
    server = await _get_user_server(username)

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="API_KEY_NOT_SET: Set API Key OTPInstan di Settings dahulu",
        )

    try:
        resp = await otp_create_order(api_key, service, country, server)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OTPInstan API error: {e}")
    if not resp.get("success"):
        raise HTTPException(status_code=400, detail=parse_error(resp))

    async with async_session() as session:
        order = Order(
            order_id=resp["order_id"],
            phone=resp.get("phone", ""),
            service=service,
            country=country,
            price=resp.get("price", 0),
            status=resp.get("status", "pending"),
            username=username,
        )
        session.add(order)
        await session.commit()

    return {
        "success": True,
        "order_id": order.order_id,
        "phone": order.phone,
        "service": order.service,
        "country": order.country,
        "price": order.price,
        "status": order.status,
    }


@router.get("/chekotp")
async def chekotp(
    username: str = Query(...),
    phone: str = Query(..., description="Nomor HP, contoh: 628123456789"),
):
    async with async_session() as session:
        stmt = (
            select(Order)
            .where(Order.phone == phone, Order.username == username)
            .order_by(desc(Order.created_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="PHONE_NOT_FOUND: Nomor HP tidak ditemukan",
            )

        if order.status in ("pending", "received"):
            api_key = await _get_user_api(username)
            server = await _get_user_server(username)
            try:
                check_resp = await otp_check_order(api_key, order.order_id, server)
                if check_resp.get("success"):
                    new_status = check_resp.get("status", order.status)
                    new_otp = check_resp.get("otp")
                    if new_status != order.status:
                        order.status = new_status
                    if new_otp and new_otp != order.otp_code:
                        order.otp_code = new_otp
                        order.otp_updated_at = datetime.datetime.utcnow()
                    await session.commit()
            except Exception:
                pass

        return {
            "success": True,
            "order_id": order.order_id,
            "phone": order.phone,
            "status": order.status,
            "otp": order.otp_code,
            "otp_updated_at": (
                order.otp_updated_at.isoformat()
                if order.otp_updated_at else None
            ),
        }


@router.get("/status/sukses/{phone}")
async def status_sukses(username: str = Query(...), phone: str = ""):
    async with async_session() as session:
        stmt = (
            select(Order)
            .where(Order.phone == phone, Order.username == username)
            .order_by(desc(Order.created_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(
                status_code=404,
                detail="PHONE_NOT_FOUND: Nomor HP tidak ditemukan",
            )
        order.client_status = "sukses"
        await session.commit()

    return {
        "success": True,
        "phone": phone,
        "client_status": "sukses",
        "order_id": order.order_id,
    }


@router.get("/status/gagal/{phone}")
async def status_gagal(username: str = Query(...), phone: str = ""):
    async with async_session() as session:
        stmt = (
            select(Order)
            .where(Order.phone == phone, Order.username == username)
            .order_by(desc(Order.created_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(
                status_code=404,
                detail="PHONE_NOT_FOUND: Nomor HP tidak ditemukan",
            )
        order.client_status = "gagal"
        await session.commit()

    return {
        "success": True,
        "phone": phone,
        "client_status": "gagal",
        "order_id": order.order_id,
    }
