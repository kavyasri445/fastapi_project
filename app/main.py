from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database.connection import engine

# =========================================================
# MODELS
# =========================================================

from app.models.audit_log import AuditLog


# =========================================================
# ROUTERS
# =========================================================

from app.routers.user import router as user_router
from app.routers.form import router as form_router
from app.routers.form_version import router as form_version_router
from app.routers.field import router as field_router
from app.routers.field_option import router as field_option_router
from app.routers.conditional_rule import router as conditional_rule_router
from app.routers.submission import router as submission_router
from app.routers.response_value import router as response_value_router
from app.routers.auth import router as auth_router
from app.routers.public_form import router as public_form_router
from app.routers import public_submissions
from app.routers.upload import router as upload_router
from app.routers.files import router as files_router
from app.routers.admin_files import router as admin_files_router
from app.routers.analytics import router as analytics_router
from app.routers.responses import router as responses_router
from app.routers.response_detail import router as response_detail_router
from app.routers.response_management import router as response_management_router

router_list = [
    user_router,
    form_router,
    form_version_router,
    field_router,
    field_option_router,
    conditional_rule_router,
    submission_router,
    response_value_router,
    auth_router,
    public_form_router,
    public_submissions.router,
    upload_router,
    files_router,
    admin_files_router,
    analytics_router,
    responses_router,
    response_detail_router,
    response_management_router,
]

app = FastAPI(title="FastAPI Application")

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
TEMPLATES_DIR = PROJECT_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =========================================================
# INCLUDE ROUTERS
# =========================================================

for router in router_list:
    app.include_router(router)


# =========================================================
# BASIC ROUTES
# =========================================================

@app.get("/")
def root():
    return {"message": "FastAPI application is running"}


@app.get("/database-check")
def database_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "success",
            "message": "Database connection successful"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# =========================================================
# PWA ROUTES
# =========================================================

@app.get("/manifest.json")
def pwa_manifest():
    return FileResponse(
        STATIC_DIR / "manifest.json",
        media_type="application/manifest+json"
    )


@app.get("/sw.js")
def service_worker():
    return FileResponse(
        STATIC_DIR / "sw.js",
        media_type="application/javascript"
    )


# =========================================================
# HTML PAGES
# =========================================================

@app.get("/signup")
def signup_page():
    return FileResponse(TEMPLATES_DIR / "signup.html")


@app.get("/forms-page")
def forms_page():
    return FileResponse(TEMPLATES_DIR / "forms.html")


@app.get("/create-form")
def create_form_page():
    return FileResponse(TEMPLATES_DIR / "create_form.html")


@app.get("/form-builder")
def form_builder_page():
    return FileResponse(TEMPLATES_DIR / "form_builder.html")


@app.get("/edit-form/{form_id}")
def edit_form_page(form_id: str):
    return FileResponse(TEMPLATES_DIR / "edit_form.html")


@app.get("/version-history")
def version_history_page():
    return FileResponse(STATIC_DIR / "version_history.html")


@app.get("/public/forms/{slug}/page")
def public_form_page(slug: str):
    return FileResponse(TEMPLATES_DIR / "public_form.html")


@app.get("/share-form/{form_id}")
def share_form_page(form_id: str):
    return FileResponse(TEMPLATES_DIR / "share_form.html")


@app.get("/admin-files")
def admin_files_page():
    return FileResponse(TEMPLATES_DIR / "admin_files.html")


@app.get("/signin")
def signin_page():
    return FileResponse(TEMPLATES_DIR / "signin.html")


@app.get("/analytics/{form_id}")
def analytics_page(form_id: str):
    return FileResponse(TEMPLATES_DIR / "analytics.html")


@app.get("/responses/{form_id}")
def responses_page(form_id: str):
    return FileResponse(TEMPLATES_DIR / "responses.html")


@app.get("/response-management/{form_id}")
def response_management_page(form_id: str):
    return FileResponse(TEMPLATES_DIR / "responses.html")