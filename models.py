from pydantic import BaseModel, Field
from typing import Optional


# --------------------------------------------------
# REGISTER MODEL
# --------------------------------------------------

class RegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=80
    )

    email: str

    password: str = Field(
        min_length=6,
        max_length=100
    )


# --------------------------------------------------
# LOGIN MODEL
# --------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


# --------------------------------------------------
# HOME INTERIOR MODEL
# --------------------------------------------------

class HomeRequest(BaseModel):
    budget: float = Field(
        gt=0
    )

    room: str

    style: str = "Modern"

    lights: int = Field(
        default=1,
        ge=0
    )

    fans: int = Field(
        default=1,
        ge=0
    )

    tables: int = Field(
        default=0,
        ge=0
    )

    extra: Optional[str] = ""


# --------------------------------------------------
# PARTY PLANNING MODEL
# --------------------------------------------------

class PartyRequest(BaseModel):
    budget: float = Field(
        gt=0
    )

    guests: int = Field(
        gt=0
    )

    event_type: str

    venue: str = "Any"

    food_preference: str = "Mixed"

    extra: Optional[str] = ""


# --------------------------------------------------
# JEWELRY RECOMMENDATION MODEL
# --------------------------------------------------

class JewelryRequest(BaseModel):
    budget: float = Field(
        gt=0
    )

    occasion: str

    style: str = "Elegant"

    outfit_color: Optional[str] = ""

    extra: Optional[str] = ""