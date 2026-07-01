"""
OTPInstan Bridge — FastAPI App (Multi-User)
Run: uvicorn main:app --host 0.0.0.0 --port 8032
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from app.database import init_db
from app.routers import api, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="OTPInstan Bridge", lifespan=lifespan)


# ── Root: empty landing page ───────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>OTPInstan Bridge</title>
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    body{
      font-family:'Inter',system-ui,sans-serif;
      background:#08090f; color:#e4e6f2;
      min-height:100vh; display:flex;
      align-items:center; justify-content:center;
    }
    .card{
      background:#13141f; border:1px solid #22243a;
      border-radius:16px; padding:40px 48px;
      text-align:center; max-width:420px; width:100%;
    }
    .logo{
      width:56px; height:56px;
      background:linear-gradient(135deg,#6c63ff,#8b83ff);
      border-radius:16px; display:flex; align-items:center;
      justify-content:center; margin:0 auto 20px;
      font-size:28px; font-weight:800; color:#fff;
    }
    h1{font-size:1.5rem;font-weight:700;color:#fff;margin-bottom:6px;}
    p{font-size:.85rem;color:#6b7280;margin-bottom:24px;line-height:1.6;}
    code{
      color:#8b83ff; background:rgba(108,99,255,.08);
      padding:3px 8px; border-radius:5px; font-size:.75rem;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">O</div>
    <h1>OTPInstan Bridge</h1>
    <p>
      Multi-User OTP Bridge untuk OTPInstan reseller.<br/>
      Akses dashboard Anda di:
    </p>
    <p>
      <code>http://192.168.80.10:8032/username/</code>
    </p>
    <p style="font-size:.72rem;color:#4b5563;margin-top:16px;">
      Ganti <code>username</code> dengan username Anda.<br/>
      Password default: <code>123456</code>
    </p>
  </div>
</body>
</html>"""


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
