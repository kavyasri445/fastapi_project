from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.response_value import ResponseValue
from app.schemas.response_value import (
    ResponseValueCreate,
    ResponseValueResponse
)

router = APIRouter(
    prefix="/response-values",
    tags=["Response Values"]
)


@router.post("/", response_model=ResponseValueResponse)
def create_response_value(
    response: ResponseValueCreate,
    db: Session = Depends(get_db)
):
    new_response = ResponseValue(
        submission_id=response.submission_id,
        field_id=response.field_id,
        value=response.value
    )

    db.add(new_response)
    db.commit()
    db.refresh(new_response)

    return new_response


@router.get("/", response_model=list[ResponseValueResponse])
def get_response_values(db: Session = Depends(get_db)):
    return db.query(ResponseValue).all()