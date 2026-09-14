import re
from datetime import datetime

from app.models.field_option import FieldOption


def validate_field(field, value, db):
    errors = []

    field_type = str(field.field_type).lower()
    config = field.validation_config or {}

    # =====================================================
    # EMPTY VALUE
    # =====================================================

    is_empty = (
        value is None
        or str(value).strip() == ""
    )

    # Required-field checking is handled in submissions.py
    if is_empty:
        return errors

    # =====================================================
    # TEXT / STRING
    # =====================================================

    if field_type in ["text", "string"]:

        text_value = str(value)

        min_length = config.get("min_length")
        max_length = config.get("max_length")

        if min_length is not None:
            if len(text_value) < int(min_length):
                errors.append(
                    f"Minimum {min_length} characters required"
                )

        if max_length is not None:
            if len(text_value) > int(max_length):
                errors.append(
                    f"Maximum {max_length} characters allowed"
                )

    # =====================================================
    # NUMBER
    # =====================================================

    elif field_type == "number":

        try:
            number_value = float(value)

            min_value = config.get("min")
            max_value = config.get("max")

            if min_value is not None:
                if number_value < float(min_value):
                    errors.append(
                        f"Must be greater than or equal to {min_value}"
                    )

            if max_value is not None:
                if number_value > float(max_value):
                    errors.append(
                        f"Must be less than or equal to {max_value}"
                    )

        except (TypeError, ValueError):

            errors.append(
                "Must be a valid number"
            )

    # =====================================================
    # EMAIL
    # =====================================================

    elif field_type == "email":

        email_value = str(value).strip()

        pattern = (
            r"^[A-Za-z0-9._%+-]+@"
            r"[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}$"
        )

        if not re.match(pattern, email_value):

            errors.append(
                "Invalid email format"
            )

    # =====================================================
    # DATE
    # =====================================================

    elif field_type == "date":

        date_value = str(value).strip()

        try:

            datetime.strptime(
                date_value,
                "%Y-%m-%d"
            )

        except ValueError:

            errors.append(
                "Invalid date format. Use YYYY-MM-DD"
            )

    # =====================================================
    # DROPDOWN
    # =====================================================

    elif field_type == "dropdown":

        try:

            options = db.query(FieldOption).filter(
                FieldOption.field_id == field.id
            ).all()

            allowed_values = [
                str(option.option_value)
                for option in options
            ]

            if not allowed_values:

                errors.append(
                    "No options configured for this dropdown"
                )

            elif str(value) not in allowed_values:

                errors.append(
                    "Invalid option. Allowed values: "
                    + ", ".join(allowed_values)
                )

        except Exception as e:

            print(
                "Dropdown validation error:",
                str(e)
            )

            errors.append(
                "Unable to validate dropdown option"
            )

    # =====================================================
    # CHECKBOX
    # =====================================================

    elif field_type == "checkbox":

        if isinstance(value, bool):

            checkbox_value = value

        else:

            checkbox_value = str(value).lower()

            if checkbox_value not in [
                "true",
                "false",
                "1",
                "0"
            ]:

                errors.append(
                    "Checkbox value must be true or false"
                )

        if config.get("must_be_checked") is True:

            if checkbox_value not in [
                True,
                "true",
                "1"
            ]:

                errors.append(
                    "Checkbox must be checked"
                )

    # =====================================================
    # RATING
    # =====================================================

    elif field_type == "rating":

        try:

            rating_value = float(value)

            min_rating = config.get("min", 1)
            max_rating = config.get("max", 5)

            if rating_value < float(min_rating):

                errors.append(
                    f"Rating must be at least {min_rating}"
                )

            if rating_value > float(max_rating):

                errors.append(
                    f"Rating must be at most {max_rating}"
                )

        except (TypeError, ValueError):

            errors.append(
                "Rating must be a valid number"
            )

    # =====================================================
    # FILE UPLOAD
    # =====================================================

    elif field_type in ["file", "file_upload"]:

        file_name = ""

        file_size = None

        # -------------------------------------------------
        # If frontend sends an object
        #
        # Example:
        #
        # {
        #     "name": "resume.pdf",
        #     "size": 100000
        # }
        # -------------------------------------------------

        if isinstance(value, dict):

            file_name = str(
                value.get("name", "")
            ).strip()

            file_size = value.get("size")

        # -------------------------------------------------
        # If frontend sends only filename
        #
        # Example:
        #
        # "resume.pdf"
        # -------------------------------------------------

        else:

            file_name = str(value).strip()

        # -------------------------------------------------
        # FILE NAME CHECK
        # -------------------------------------------------

        if not file_name:

            errors.append(
                "File name is required"
            )

        else:

            # Get extension
            if "." in file_name:

                file_extension = (
                    "."
                    + file_name.rsplit(".", 1)[1].lower()
                )

            else:

                file_extension = ""

            # -------------------------------------------------
            # ALLOWED EXTENSIONS
            # -------------------------------------------------

            allowed_extensions = config.get(
                "allowed_extensions"
            )

            if allowed_extensions:

                normalized_extensions = []

                for extension in allowed_extensions:

                    extension = str(
                        extension
                    ).lower().strip()

                    if not extension.startswith("."):
                        extension = "." + extension

                    normalized_extensions.append(
                        extension
                    )

                if (
                    file_extension
                    not in normalized_extensions
                ):

                    errors.append(
                        "Invalid file type. Allowed types: "
                        + ", ".join(
                            normalized_extensions
                        )
                    )

            # -------------------------------------------------
            # MAX FILE SIZE
            # -------------------------------------------------

            max_size = config.get("max_size")

            if (
                max_size is not None
                and file_size is not None
            ):

                try:

                    if int(file_size) > int(max_size):

                        errors.append(
                            "File size must be less than "
                            f"or equal to {max_size} bytes"
                        )

                except (TypeError, ValueError):

                    errors.append(
                        "Invalid file size"
                    )

    return errors