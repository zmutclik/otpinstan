"""
OTPInstan Bridge — FastAPI App (Multi-User)
Run: uvicorn main:app --host 0.0.0.0 --port 8032
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from app.database import init_db
from app.routers import api, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("/app/data", exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="OTPInstan Bridge", lifespan=lifespan)


# ── Root: empty landing page ───────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root():
    return """"""


# ── Catch-all: parse {username} from path, route accordingly ────────────
@app.api_route("/{username}/{path:path}", methods=["GET", "POST"])
async def catch_all(username: str, path: str, request: Request):
    """Dynamic routing based on username prefix and sub-path."""

    if path == "" or path == "/":
        return await dashboard.dashboard(request, username=username)

    elif path == "login":
        if request.method == "POST":
            return await dashboard.login(request, username=username)
        return await dashboard.login_page(request, username=username)

    elif path == "logout":
        return await dashboard.logout(request, username=username)

    elif path == "orders":
        return await dashboard.orders_page(request, username=username)

    elif path == "settings":
        if request.method == "POST":
            return await dashboard.settings_save(request, username=username)
        return await dashboard.settings_page(request, username=username)

    elif path == "api-docs":
        return await dashboard.api_docs_page(request, username=username)

    # ── API endpoints ──────────────────────────────────────────────────
    elif path == "getotp":
        return await api.getotp(
            username=username,
            service=request.query_params.get("service", ""),
            country=int(request.query_params.get("country", 0)),
        )

    elif path == "chekotp":
        return await api.chekotp(
            username=username,
            phone=request.query_params.get("phone", ""),
        )

    elif path.startswith("status/sukses/"):
        phone = path.split("/")[-1]
        return await api.status_sukses(username=username, phone=phone)

    elif path.startswith("status/gagal/"):
        phone = path.split("/")[-1]
        return await api.status_gagal(username=username, phone=phone)

    elif path.startswith("cancel/"):
        order_id = path.split("/", 1)[1]
        return await dashboard.cancel_order_route(
            order_id, request, username=username
        )

    return JSONResponse(
        {"success": False, "message": "Not found"}, status_code=404
    )
