from pydantic import BaseModel


class LoginData(BaseModel):
    email: str
    password: str


class RegisterData(BaseModel):
    tour_agency_id: str
    email: str
    password: str
