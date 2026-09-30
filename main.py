import json
from pathlib import Path

from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from database import (
    init_db,
    create_user,
    get_user_by_email,
    save_recommendation,
    get_history,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from models import HomeRequest, PartyRequest, JewelryRequest
from gemini_utils import generate_recommendation

load_dotenv()

# --------------------------------------------------
# APP SETUP
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="PocketSmart AI",
    version="1.0.0"
)

# Static files
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# HTML templates
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


# --------------------------------------------------
# DATABASE STARTUP
# --------------------------------------------------

@app.on_event("startup")
def startup():
    init_db()


# --------------------------------------------------
# COMMON PAGE CONTEXT
# --------------------------------------------------

def page_context(request: Request, **kwargs):
    return {
        "request": request,
        "user": get_current_user(request),
        **kwargs
    }


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=page_context(request)
    )


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=page_context(request)
    )
    @app.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...)
):
    user = get_user_by_email(email)

    if not user:
        return RedirectResponse(
            "/login?error=Invalid%20email%20or%20password",
            status_code=303
        )

    if not verify_password(
        password,
        user["password_hash"]
    ):
        return RedirectResponse(
            "/login?error=Invalid%20email%20or%20password",
            status_code=303
        )

    token = create_access_token(user["id"])

    response = RedirectResponse(
        "/dashboard",
        status_code=303
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )

    return response


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        page_context(request)
    )


@app.post("/register")
def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    existing_user = get_user_by_email(email)

    if existing_user:
        return RedirectResponse(
            "/register?error=Email%20already%20registered",
            status_code=303
        )

    user_id = create_user(
        name.strip(),
        email.strip(),
        hash_password(password)
    )

    token = create_access_token(user_id)

    response = RedirectResponse(
        "/dashboard",
        status_code=303
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )

    return response


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.get("/logout")
def logout():
    response = RedirectResponse(
        "/",
        status_code=303
    )

    response.delete_cookie("access_token")

    return response


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    user = get_current_user(request)

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    history = get_history(user["id"])

    return templates.TemplateResponse(
        "dashboard.html",
        page_context(
            request,
            history=history[:5]
        )
    )


# --------------------------------------------------
# HOME INTERIOR PLANNER
# --------------------------------------------------

@app.get("/home-planner", response_class=HTMLResponse)
def home_planner(request: Request):
    return templates.TemplateResponse(
        "home_planner.html",
        page_context(request)
    )


# --------------------------------------------------
# PARTY PLANNER
# --------------------------------------------------

@app.get("/party-planner", response_class=HTMLResponse)
def party_planner(request: Request):
    return templates.TemplateResponse(
        "party_planner.html",
        page_context(request)
    )


# --------------------------------------------------
# JEWELRY PLANNER
# --------------------------------------------------

@app.get("/jewelry-planner", response_class=HTMLResponse)
def jewelry_planner(request: Request):
    return templates.TemplateResponse(
        "jewelry_planner.html",
        page_context(request)
    )


# --------------------------------------------------
# RECOMMENDATION HISTORY
# --------------------------------------------------

@app.get("/history", response_class=HTMLResponse)
def history(request: Request):

    user = get_current_user(request)

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    user_history = get_history(user["id"])

    return templates.TemplateResponse(
        "history.html",
        page_context(
            request,
            history=user_history
        )
    )


# --------------------------------------------------
# HOME INTERIOR AI RECOMMENDATION
# --------------------------------------------------

@app.post("/generate-home")
async def generate_home(request: Request):

    user = get_current_user(request)

    if not user:
        return JSONResponse(
            {
                "error": "Please login first."
            },
            status_code=401
        )

    body = await request.json()

    data = HomeRequest(**body)

    payload = data.model_dump()

    result = generate_recommendation(
        "home",
        payload
    )

    save_recommendation(
        user["id"],
        "Home",
        payload,
        result
    )

    return {
        "category": "Home",
        "recommendation": result
    }


# --------------------------------------------------
# PARTY AI RECOMMENDATION
# --------------------------------------------------

@app.post("/generate-party")
async def generate_party(request: Request):

    user = get_current_user(request)

    if not user:
        return JSONResponse(
            {
                "error": "Please login first."
            },
            status_code=401
        )

    body = await request.json()

    data = PartyRequest(**body)

    payload = data.model_dump()

    result = generate_recommendation(
        "party",
        payload
    )

    save_recommendation(
        user["id"],
        "Party",
        payload,
        result
    )

    return {
        "category": "Party",
        "recommendation": result
    }


# --------------------------------------------------
# JEWELRY AI RECOMMENDATION
# --------------------------------------------------

@app.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    image: UploadFile | None = File(default=None)
):

    user = get_current_user(request)

    if not user:
        return JSONResponse(
            {
                "error": "Please login first."
            },
            status_code=401
        )

    form = await request.form()

    data = JewelryRequest(
        budget=float(form.get("budget")),
        occasion=str(form.get("occasion")),
        style=str(
            form.get(
                "style",
                "Elegant"
            )
        ),
        outfit_color=str(
            form.get(
                "outfit_color",
                ""
            )
        ),
        extra=str(
            form.get(
                "extra",
                ""
            )
        )
    )

    image_bytes = None

    if image and image.filename:

        image_bytes = await image.read()

        # Maximum image size = 5 MB
        if len(image_bytes) > 5 * 1024 * 1024:

            return JSONResponse(
                {
                    "error": "Image must be smaller than 5 MB."
                },
                status_code=400
            )

    payload = data.model_dump()

    result = generate_recommendation(
        "jewelry",
        payload,
        image_bytes
    )

    save_recommendation(
        user["id"],
        "Jewelry",
        payload,
        result
    )

    return {
        "category": "Jewelry",
        "recommendation": result
    }


# --------------------------------------------------
# SESSION INFORMATION
# --------------------------------------------------

@app.get("/session-info")
def session_info(request: Request):

    user = get_current_user(request)

    if not user:
        return {
            "logged_in": False
        }

    return {
        "logged_in": True,
        "user_id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }


# --------------------------------------------------
# SESSION DATA
# --------------------------------------------------

@app.get("/session-data")
def session_data(request: Request):

    user = get_current_user(request)

    if not user:
        return JSONResponse(
            {
                "error": "Not authenticated"
            },
            status_code=401
        )

    history = get_history(user["id"])

    return {
        "user": dict(user),
        "history_count": len(history)
    }


# --------------------------------------------------
# RECOMMENDATION DETAILS
# --------------------------------------------------

@app.get("/recommendations-details")
def recommendation_details(
    request: Request,
    recommendation_id: int
):

    user = get_current_user(request)

    if not user:
        return JSONResponse(
            {
                "error": "Not authenticated"
            },
            status_code=401
        )

    rows = [
        row
        for row in get_history(user["id"])
        if row["id"] == recommendation_id
    ]

    if not rows:
        return JSONResponse(
            {
                "error": "Recommendation not found"
            },
            status_code=404
        )

    row = rows[0]

    return {
        "id": row["id"],
        "category": row["category"],
        "request": json.loads(
            row["request_json"]
        ),
        "response": row["response_text"],
        "created_at": row["created_at"]
    }


# --------------------------------------------------
# STARTUP STATUS
# --------------------------------------------------

@app.get("/startup")
def startup_status():

    return {
        "status": "PocketSmart AI is running"
    }


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )