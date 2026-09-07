from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.field_option import FieldOption
from app.schemas.field_option import FieldOptionCreate, FieldOptionResponse


router = APIRouter(
    prefix="/field-options",
    tags=["Field Options"]
)


@router.post("/", response_model=FieldOptionResponse)
def create_field_option(
    option: FieldOptionCreate,
    db: Session = Depends(get_db)
):
    new_option = FieldOption(
        field_id=option.field_id,
        option_label=option.option_label,
        option_value=option.option_value,
        display_order=option.display_order
    )

    db.add(new_option)
    db.commit()
    db.refresh(new_option)

    return new_option


@router.get("/", response_model=list[FieldOptionResponse])
def get_field_options(db: Session = Depends(get_db)):
    return db.query(FieldOption).all()