
from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: str
    full_name: str | None = None
    age: int | None = None
    gender: str | None = None
    weight_kg: float | None = None
    height_cm: float | None = None
    resting_hr: int | None = None
    max_hr: int | None = None
