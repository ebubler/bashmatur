import jwt
import os

from dotenv import load_dotenv


load_dotenv()

JWT_SECRET: str = "JWT_SECRET_KEY"


def generate_jwt(tour_agency_id, email, password):
    return jwt.encode({
        "tour_agency_id": str(tour_agency_id),
        "email": email,
        "password": password
    }, key=JWT_SECRET, algorithm="HS256")


def decode_jwt(jwt_token):
    try:
        is_auth = jwt.decode(jwt_token, JWT_SECRET, algorithms=["HS256"])
    except Exception as e:
        return False
    return is_auth
