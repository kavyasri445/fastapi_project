from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database.connection import engine

from app.models.public_link import PublicLink

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
from app.routers import submission

# =========================================================
# CREATE FASTAPI APP
# =========================================================

app = FastAPI(
    title="FastAPI Application"
)


# =========================================================
# PROJECT DIRECTORIES
# =========================================================

# Location of app/main.py
APP_DIR = Path(__file__).resolve().parent

# Location of fastapi_project/
PROJECT_DIR = APP_DIR.parent

# Location of fastapi_project/templates/
TEMPLATES_DIR = PROJECT_DIR / "templates"

# Location of fastapi_project/app/static/
STATIC_DIR = APP_DIR / "static"


# =========================================================
# STATIC FILES
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# =========================================================
# INCLUDE API ROUTERS
# =========================================================

app.include_router(user_router)
app.include_router(form_router)
app.include_router(form_version_router)
app.include_router(field_router)
app.include_router(field_option_router)

# Conditional Rules
app.include_router(conditional_rule_router)

app.include_router(submission_router)
app.include_router(response_value_router)
app.include_router(auth_router)
app.include_router(public_form_router)
app.include_router(submission.router)

# =========================================================
# HOME / API ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "FastAPI application is running"
    }


# =========================================================
# DATABASE CHECK
# =========================================================

@app.get("/database-check")
def database_check():

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

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
# SIGNUP PAGE
# =========================================================

@app.get("/signup")
def signup_page():

    return FileResponse(
        TEMPLATES_DIR / "signup.html"
    )


# =========================================================
# FORMS LIST PAGE
# =========================================================

@app.get("/forms-page")
def forms_page():

    return FileResponse(
        TEMPLATES_DIR / "forms.html"
    )


# =========================================================
# CREATE FORM PAGE
# =========================================================

@app.get("/create-form")
def create_form_page():

    return FileResponse(
        TEMPLATES_DIR / "create_form.html"
    )


# =========================================================
# FORM BUILDER PAGE
# =========================================================

@app.get("/form-builder")
def form_builder_page():

    return FileResponse(
        TEMPLATES_DIR / "form_builder.html"
    )


# =========================================================
# EDIT FORM PAGE
# =========================================================

@app.get("/edit-form/{form_id}")
def edit_form_page(form_id: str):

    return FileResponse(
        TEMPLATES_DIR / "edit_form.html"
    )


# =========================================================
# VERSION HISTORY PAGE
# =========================================================

@app.get("/version-history")
def version_history_page():

    return FileResponse(
        STATIC_DIR / "version_history.html"
    )


# =========================================================
# PUBLIC FORM PAGE
# =========================================================

@app.get("/public/forms/{slug}/page")
def public_form_page(slug: str):

    return FileResponse(
        TEMPLATES_DIR / "public_form.html"
    )


# =========================================================
# SHARE FORM PAGE
# =========================================================

@app.get("/share-form/{form_id}")
def share_form_page(form_id: str):

    return FileResponse(
        TEMPLATES_DIR / "share_form.html"
    )