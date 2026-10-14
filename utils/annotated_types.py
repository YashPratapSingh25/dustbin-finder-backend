import re
from typing import Annotated
from fastapi import Query
from pydantic import AfterValidator

def validate_password(value : str):
    if len(value) < 8 and len(value) > 20:
        raise ValueError("Password should be between 8 and 20 characters")

    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one number")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character")

    return value

# Custom Type which contains a custom validation on String type data
PasswordStr = Annotated[str, AfterValidator(func=validate_password)]

PageNumberQuery = Annotated[int, Query(gt=0)]

PageSizeQuery = Annotated[int, Query(gt=0)]