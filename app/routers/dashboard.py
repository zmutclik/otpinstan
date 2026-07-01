import datetime
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc, func
from itsdangerous import URLSafeSerializer
from pathlib import Path
from app.database import async_session
from app.models import Order, User
from app.services.otpinstan import get_balance as otp_get_balance, cancel_order as otp_cancel
from app.config import get_or_create_user, update_user, DEFAULT_PASSWORD

router = APIRouter()

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_signer() -> URLSafeSerializer:
    return URLSafeSerializer("otpinstan-bridge-secret-key-2026")


async def _check_session(request: Request, username: str) -> bool:
    cookie = request.cookies.get("session")
    if not cookie:
        return False
    signer = get_signer()
    try:
        val = signer.loads(cookie)
        return val == username
    except Exception:
        return False


async def _get_user_or_redirect(request: Request, username: str):
    user = await get_or_create_user(username)
    if not await _check_session(request, username):
        return None, RedirectResponse(url=f"/{username}/login", status_code=302)
    return user, None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, username: str = ""):
    await get_or_create_user(username)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "username": username,
        "error": None,
    })


@router.post("/login")
async def login(request: Request, username: str = ""):
    form = await request.form()
    input_user = form.get("username", "")
    input_pass = form.get("password", "")
    user = await get_or_create_user(username)

    if input_user != username or input_pass != user.password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "username": username,
            "error": "Username atau password salah",
        })

    resp = RedirectResponse(url=f"/{username}/", status_code=302)
    signer = get_signer()
    resp.set_cookie("session", signer.dumps(username), httponly=True, max_age=86400)
    return resp


@router.get("/logout")
async def logout(request: Request, username: str = ""):
    resp = RedirectResponse(url=f"/{username}/login", status_code=302)
    resp.delete_cookie("session")
    return resp


@router.get("/")
async def dashboard(request: Request, username: str = ""):
    user, redirect = await _get_user_or_redirect(request, username)
    if redirect:
        return redirect

    async with async_session() as session_db:
        sukses_count = await session_db.scalar(
            select(func.count(Order.id)).where(
                Order.username == username, Order.client_status == "sukses"
            )
        )
        gagal_count = await session_db.scalar(
            select(func.count(Order.id)).where(
                Order.username == username, Order.client_status == "gagal"
            )
        )
        pending_count = await session_db.scalar(
            select(func.count(Order.id)).where(
                Order.username == username, Order.status == "pending"
            )
        )

    balance = 0
    try:
        bal_resp = await otp_get_balance(user.api_key)
        if bal_resp.get("success"):
            balance = bal_resp.get("balance", 0)
    except Exception:
        pass

    async with async_session() as session_db:
        stmt = (
            select(Order)
            .where(Order.username == username)
            .order_by(desc(Order.created_at))
            .limit(5)
        )
        result = await session_db.execute(stmt)
        recent = result.scalars().all()

    server = user.server or "s5"
    server_label = {"s5": "Server 5", "s1": "Server 1", "s6": "Server 6"}.get(server, server.upper())

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username,
        "user": user,
        "current_page": "dashboard",
        "page_title": "Dashboard",
        "balance": balance,
        "sukses": sukses_count,
        "gagal": gagal_count,
        "pending": pending_count,
        "recent": recent,
        "server_label": server_label,
    })


@router.get("/orders")
async def orders_page(request: Request, username: str = ""):
    user, redirect = await _get_user_or_redirect(request, username)
    if redirect:
        return redirect

    async with async_session() as session_db:
        stmt = (
            select(Order)
            .where(Order.username == username)
            .order_by(desc(Order.created_at))
            .limit(100)
        )
        result = await session_db.execute(stmt)
        orders = result.scalars().all()

    return templates.TemplateResponse("orders.html", {
        "request": request,
        "username": username,
        "user": user,
        "current_page": "orders",
        "page_title": "Daftar OTP",
        "orders": orders,
    })


@router.get("/settings")
async def settings_page(request: Request, username: str = ""):
    user, redirect = await _get_user_or_redirect(request, username)
    if redirect:
        return redirect
    return _settings_response(request, username, user, msg=None, error=None)


@router.post("/settings")
async def settings_save(request: Request, username: str = ""):
    user, redirect = await _get_user_or_redirect(request, username)
    if redirect:
        return redirect

    form = await request.form()
    api_key = form.get("api_key", "").strip()
    new_password = form.get("password", "").strip()
    server = form.get("server", "s5").strip()

    if api_key:
        await update_user(username, api_key=api_key)
    if new_password:
        await update_user(username, password=new_password)
    if server:
        await update_user(username, server=server)

    user = await get_or_create_user(username)
    return _settings_response(request, username, user,
                              msg="Settings berhasil disimpan", error=None)


def _settings_response(request, username, user, msg, error):
    api_key_display = user.api_key or ""
    api_key_masked = ""
    if api_key_display:
        if len(api_key_display) > 12:
            api_key_masked = api_key_display[:6] + "•" * 8 + api_key_display[-4:]
        else:
            api_key_masked = api_key_display[:4] + "•" * 6

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "username": username,
        "user": user,
        "current_page": "settings",
        "page_title": "Settings",
        "msg": msg,
        "error": error,
        "api_key_display": api_key_display,
        "api_key_masked": api_key_masked,
    })


@router.get("/cancel/{order_id}")
async def cancel_order_route(order_id: str, request: Request, username: str = ""):
    if not await _check_session(request, username):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)

    user = await get_or_create_user(username)
    try:
        await otp_cancel(user.api_key, order_id, user.server)
    except Exception:
        pass

    async with async_session() as session_db:
        stmt = select(Order).where(
            Order.order_id == order_id, Order.username == username
        )
        result = await session_db.execute(stmt)
        order = result.scalar_one_or_none()
        if order:
            order.status = "cancelled"
            await session_db.commit()

    return RedirectResponse(url=f"/{username}/orders", status_code=302)


@router.get("/api-docs")
async def api_docs_page(request: Request, username: str = ""):
    user, redirect = await _get_user_or_redirect(request, username)
    if redirect:
        return redirect

    base_url = f"{request.base_url.scheme}://{request.base_url.netloc}/{username}"

    return templates.TemplateResponse("api_docs.html", {
        "request": request,
        "username": username,
        "user": user,
        "current_page": "api-docs",
        "page_title": "API Documentation",
        "base_url": base_url,
    })
