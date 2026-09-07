import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.conditional_rule import ConditionalRule
from app.models.field import Field
from app.models.form import Form
from app.models.form_version import FormVersion
from app.schemas.conditional_rule import (
    ConditionalRuleCreate,
    ConditionalRuleResponse,
    ConditionalRuleUpdate,
)

router = APIRouter(
    prefix="/conditional-rules",
    tags=["Conditional Rules"]
)


# ============================================================
# ALLOWED VALUES
# ============================================================

ALLOWED_OPERATORS = {
    "equals",
    "not_equals",
    "contains",
    "greater_than",
    "is_empty"
}

ALLOWED_ACTIONS = {
    "show",
    "hide",
    "require"
}


# ============================================================
# CREATE RULE
# POST /conditional-rules/forms/{form_id}/rules
# ============================================================

@router.post(
    "/forms/{form_id}/rules",
    response_model=ConditionalRuleResponse,
    status_code=201
)
def create_conditional_rule(
    form_id: uuid.UUID,
    rule: ConditionalRuleCreate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Check form
    # --------------------------------------------------------

    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # --------------------------------------------------------
    # 2. Validate operator
    # --------------------------------------------------------

    if rule.operator not in ALLOWED_OPERATORS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid operator. "
                f"Allowed operators: {list(ALLOWED_OPERATORS)}"
            )
        )

    # --------------------------------------------------------
    # 3. Validate action
    # --------------------------------------------------------

    if rule.action not in ALLOWED_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid action. "
                "Allowed actions: show, hide, require"
            )
        )

    # --------------------------------------------------------
    # 4. Trigger and target cannot be same
    # --------------------------------------------------------

    if rule.trigger_field_id == rule.target_field_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Trigger field and target field "
                "cannot be the same"
            )
        )

    # --------------------------------------------------------
    # 5. Check trigger field
    # --------------------------------------------------------

    trigger_field = (
        db.query(Field)
        .join(
            FormVersion,
            Field.form_version_id == FormVersion.id
        )
        .filter(
            Field.id == rule.trigger_field_id,
            FormVersion.form_id == form_id
        )
        .first()
    )

    if not trigger_field:
        raise HTTPException(
            status_code=404,
            detail="Trigger field not found in this form"
        )

    # --------------------------------------------------------
    # 6. Check target field
    # --------------------------------------------------------

    target_field = (
        db.query(Field)
        .join(
            FormVersion,
            Field.form_version_id == FormVersion.id
        )
        .filter(
            Field.id == rule.target_field_id,
            FormVersion.form_id == form_id
        )
        .first()
    )

    if not target_field:
        raise HTTPException(
            status_code=404,
            detail="Target field not found in this form"
        )

    # --------------------------------------------------------
    # 7. Create rule
    # --------------------------------------------------------

    new_rule = ConditionalRule(
        form_id=form_id,
        trigger_field_id=rule.trigger_field_id,
        operator=rule.operator,
        comparison_value=rule.comparison_value,
        target_field_id=rule.target_field_id,
        action=rule.action
    )

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return new_rule


# ============================================================
# GET RULES
# GET /conditional-rules/forms/{form_id}/rules
# ============================================================

@router.get(
    "/forms/{form_id}/rules",
    response_model=list[ConditionalRuleResponse]
)
def get_conditional_rules(
    form_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    # Check form

    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # Get rules

    rules = (
        db.query(ConditionalRule)
        .filter(
            ConditionalRule.form_id == form_id
        )
        .all()
    )

    return rules


# ============================================================
# UPDATE RULE
# PUT /conditional-rules/{rule_id}
# ============================================================

@router.put(
    "/{rule_id}",
    response_model=ConditionalRuleResponse
)
def update_conditional_rule(
    rule_id: uuid.UUID,
    rule: ConditionalRuleUpdate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find rule
    # --------------------------------------------------------

    existing_rule = (
        db.query(ConditionalRule)
        .filter(
            ConditionalRule.id == rule_id
        )
        .first()
    )

    if not existing_rule:
        raise HTTPException(
            status_code=404,
            detail="Conditional rule not found"
        )

    form_id = existing_rule.form_id

    # --------------------------------------------------------
    # 2. Validate operator
    # --------------------------------------------------------

    if rule.operator is not None:

        if rule.operator not in ALLOWED_OPERATORS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid operator. "
                    f"Allowed operators: {list(ALLOWED_OPERATORS)}"
                )
            )

        existing_rule.operator = rule.operator

    # --------------------------------------------------------
    # 3. Validate action
    # --------------------------------------------------------

    if rule.action is not None:

        if rule.action not in ALLOWED_ACTIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid action. "
                    "Allowed actions: show, hide, require"
                )
            )

        existing_rule.action = rule.action

    # --------------------------------------------------------
    # 4. Update trigger field
    # --------------------------------------------------------

    if rule.trigger_field_id is not None:

        trigger_field = (
            db.query(Field)
            .join(
                FormVersion,
                Field.form_version_id == FormVersion.id
            )
            .filter(
                Field.id == rule.trigger_field_id,
                FormVersion.form_id == form_id
            )
            .first()
        )

        if not trigger_field:
            raise HTTPException(
                status_code=404,
                detail="Trigger field not found in this form"
            )

        existing_rule.trigger_field_id = (
            rule.trigger_field_id
        )

    # --------------------------------------------------------
    # 5. Update target field
    # --------------------------------------------------------

    if rule.target_field_id is not None:

        target_field = (
            db.query(Field)
            .join(
                FormVersion,
                Field.form_version_id == FormVersion.id
            )
            .filter(
                Field.id == rule.target_field_id,
                FormVersion.form_id == form_id
            )
            .first()
        )

        if not target_field:
            raise HTTPException(
                status_code=404,
                detail="Target field not found in this form"
            )

        existing_rule.target_field_id = (
            rule.target_field_id
        )

    # --------------------------------------------------------
    # 6. Trigger and target cannot be same
    # --------------------------------------------------------

    if (
        existing_rule.trigger_field_id
        == existing_rule.target_field_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Trigger field and target field "
                "cannot be the same"
            )
        )

    # --------------------------------------------------------
    # 7. Update comparison value
    # --------------------------------------------------------

    if rule.comparison_value is not None:

        existing_rule.comparison_value = (
            rule.comparison_value
        )

    # --------------------------------------------------------
    # 8. Save
    # --------------------------------------------------------

    db.commit()
    db.refresh(existing_rule)

    return existing_rule


# ============================================================
# DELETE RULE
# DELETE /conditional-rules/{rule_id}
# ============================================================

@router.delete("/{rule_id}")
def delete_conditional_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    # Find rule

    existing_rule = (
        db.query(ConditionalRule)
        .filter(
            ConditionalRule.id == rule_id
        )
        .first()
    )

    if not existing_rule:
        raise HTTPException(
            status_code=404,
            detail="Conditional rule not found"
        )

    # Delete

    db.delete(existing_rule)
    db.commit()

    return {
        "message": "Conditional rule deleted successfully"
    }