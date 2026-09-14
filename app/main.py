from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database.connection import engine

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


# =========================================================
# CREATE FASTAPI APP
# =========================================================

app = FastAPI(
    title="FastAPI Application"
)


# =========================================================
# PROJECT DIRECTORIES
# =========================================================

APP_DIR = Path(__file__).resolve().parent

PROJECT_DIR = APP_DIR.parent

TEMPLATES_DIR = PROJECT_DIR / "templates"

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

# Users
app.include_router(user_router)

# Forms
app.include_router(form_router)

# Form Versions
app.include_router(form_version_router)

# Fields
app.include_router(field_router)

# Field Options
app.include_router(field_option_router)

# Conditional Rules
app.include_router(conditional_rule_router)

# Normal Submissions
app.include_router(submission_router)

# Response Values
app.include_router(response_value_router)

# Authentication
app.include_router(auth_router)

# Public Forms
app.include_router(public_form_router)

# Task 4 - Public Form Submission
app.include_router(public_submissions.router)

# Task 5 - File Upload
app.include_router(upload_router)

# Task 5 - Secure File Access
app.include_router(files_router)

# Task 5 - Admin Uploaded Files
app.include_router(admin_files_router)


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
@app.get("/admin-files")
def admin_files_page():
    return FileResponse(TEMPLATES_DIR / "admin_files.html")
@app.get("/signin")
def signin_page():
    return FileResponse(TEMPLATES_DIR / "signin.html")