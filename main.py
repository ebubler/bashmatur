import asyncio
import shutil

from database import Database
from fastapi import status
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from uvicorn import Server, Config
from difflib import SequenceMatcher
from jwt_utils import decode_jwt, generate_jwt
from models import LoginData, RegisterData
from slowapi import Limiter
from slowapi.util import get_remote_address



def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


class Agency:
    def __init__(self, id, title, url, contacts, about_us, photo):
        self.id = id
        self.title = title
        self.url = url
        self.contacts = contacts
        self.about_us = about_us
        self.photo = photo


class Tour:
    def __init__(self, id, title, start_time, duration, route, tags, tour_agency, photo=None, agency_id=0):
        self.id = id
        self.title = title
        self.start_time = start_time
        self.duration = duration
        self.route = route
        self.tags = tags
        self.tour_agency = tour_agency
        self.photo = photo
        self.agency_id = agency_id


class TourDescription:
    def __init__(self, id, tour_id, description, include, photo2):
        self.id = id
        self.tour_id = tour_id
        self.description = description
        self.include = include
        self.photo2 = photo2


class BookingRequest(BaseModel):
    tour_id: int
    full_name: str
    phone: str
    email: str

    @classmethod
    def as_form(
            cls,
            tour_id: int = Form(...),
            full_name: str = Form(...),
            phone: str = Form(...),
            email: str = Form(...),
    ) -> "BookingRequest":
        return cls(tour_id=tour_id, full_name=full_name, phone=phone, email=email)


templates = Jinja2Templates(directory="templates")
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), "static")
db = Database()
limiter = Limiter(key_func=get_remote_address)


@app.get("/add/{tour_agency_id}/{email}/{password}")
@limiter.limit("120/minute")
async def temp_add(request: Request, tour_agency_id: str, email: str, password: str):
    db.register_user(tour_agency_id, email, password)


@app.get("/", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def redirect(request: Request):
    return templates.TemplateResponse(request, "redirect.html")


@app.get("/login", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def login_html(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.post("/login", response_class=RedirectResponse)
@limiter.limit("120/minute")
async def login(request: Request, login_data: LoginData):
    is_auth = db.login_user(login_data.email, login_data.password)
    if is_auth:
        jwt = generate_jwt(is_auth, login_data.email, login_data.password)
        response = RedirectResponse("/tours", status_code=status.HTTP_200_OK)
        response.set_cookie("Authorization", jwt)
        return response
    return False


@app.get("/logout")
@limiter.limit("120/minute")
async def logout(request: Request):
    response = templates.TemplateResponse(request=request, name="logout.html")
    response.delete_cookie("Authorization")
    return response


@app.get("/tour/{tour_id}", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def tour_page(request: Request, tour_id: int):
    args = db.get_tour_by_id(tour_id)
    tour = Tour(*args)
    args = db.get_description_tour(tour_id)
    description = TourDescription(*args)
    return templates.TemplateResponse(request=request, name="tour.html", context={
        "tour": tour, "description": description
    })


@app.post("/add_tour")
@limiter.limit("120/minute")
async def add_tour_request(
        request: Request,
        photos: list[UploadFile] = File(...),
        title: str = Form(...),
        start_time: str = Form(...),
        duration: str = Form(...),
        route: str = Form(...),
        tags: str = Form(...),
        description: str = Form(...)
):
    data = decode_jwt(request.cookies.get("Authorization"))
    tour_agency = db.get_agency_by_id(data.get("tour_agency_id"))
    if db.login_user(data.get("email"), data.get("password")):
        print(data.get("tour_agency_id"))
        tour_id = db.add_tour(title, start_time, duration, route, tags, tour_agency, None, data.get("tour_agency_id"))
        db.add_description(tour_id, description, "")

        filenames = []

        for i in range(len(photos)):
            with open(f'static/photo/tour_{tour_id}_{i}.png', 'wb') as buffer:
                shutil.copyfileobj(photos[i].file, buffer)
            filenames.append(f'tour_{tour_id}_{i}.png')

        db.photos_update(tour_id, filenames)

        return templates.TemplateResponse(request=request, name="tour_added.html")
    return "NO PERMISSION"


@app.get("/tours", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def tours(request: Request, search: str = None):
    data = decode_jwt(request.cookies.get("Authorization"))
    if data:
        is_auth = db.login_user(data["email"], data["password"])
    else:
        is_auth = False
    all_tours = db.get_all_tours()
    all_tours = [Tour(*args) for args in all_tours]
    if search is not None:
        search_lower = search.lower()
        tour_list = [
            tour for tour in all_tours
            if search_lower in tour.tags.lower()
               or max((similar(search_lower, word) for word in tour.title.lower().split())) >= 0.5
               or max((similar(search_lower, word) for word in tour.route.lower().split())) >= 0.5
               or max((similar(search_lower, word) for word in tour.tour_agency.lower().split())) >= 0.5
        ]
    else:
        tour_list = all_tours
    return templates.TemplateResponse(request=request, name="tours.html", context={"tours": tour_list, "is_auth": is_auth})


@app.get("/add_tour", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def add_tour(request: Request):
    return templates.TemplateResponse(request=request, name="add_tour.html")


@app.get("/agency/{tour_agency_id}", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def agency(request: Request, tour_agency_id: int):
    args = db.get_all_tours_agency(tour_agency_id)
    tour_list = [Tour(*args) for args in args]
    args = db.get_tour_agency(tour_agency_id)
    ag = Agency(*args)
    return templates.TemplateResponse(request=request, name="agency.html", context={'agency': ag, "tours": tour_list})


@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/edit_tour/{tour_id}", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def admin_edit_tour(request: Request, tour_id: int = None):
    tour_agency_id = decode_jwt(request.cookies.get("Authorization")).get("tour_agency_id")
    if not tour_agency_id:
        return "NO PERMISSION"
    args = db.get_all_tours_agency(tour_agency_id)
    tour_list = [Tour(*args) for args in args]
    current_tour = db.get_tour_by_id(tour_id)
    current_tour_descriptions = db.get_description_tour(tour_id)
    if tour_id is not None:
        return templates.TemplateResponse(request=request, name="edit_tour.html", context={
            "tours": tour_list,
            "descriptions": TourDescription(*current_tour_descriptions),
            "is_edit": True,
            "current_tour": Tour(*current_tour)
        })
    return templates.TemplateResponse(request=request, name="edit_tour.html", context={
        "tours": tour_list,
        "is_edit": False
    })


@app.post("/update-agency")
@limiter.limit("120/minute")
async def edit_agency_request(
        request: Request,
        photos: list[UploadFile] = File(...),
        title: str = Form(...),
        url: str = Form(...),
        contacts: str = Form(...),
        about_us: str = Form(...)
):
    data = decode_jwt(request.cookies.get("Authorization"))
    if db.login_user(data.get("email"), data.get("password")):
        print(data.get("tour_agency_id"))
        db.edit_agency(title, url, contacts, about_us, data.get("tour_agency_id"))

        filenames = []

        for i in range(len(photos)):
            with open(f'static/photo/tour_{data.get("tour_agency_id")}_{i}.png', 'wb') as buffer:
                shutil.copyfileobj(photos[i].file, buffer)
            filenames.append(f'tour_{data.get("tour_agency_id")}_{i}.png')

        db.photos_update_agency(data.get("tour_agency_id"), filenames)

        return templates.TemplateResponse(request=request, name="tour_added.html")
    return "NO PERMISSION"


@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/edit_prof", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def admin_edit_tour(request: Request, tour_id: int = None):
    tour_agency_id = decode_jwt(request.cookies.get("Authorization")).get("tour_agency_id")
    if not tour_agency_id:
        return "NO PERMISSION"
    args = db.get_tour_agency(tour_agency_id)
    agenc = Agency(*args)
    return templates.TemplateResponse(request=request, name="edit_agency.html", context={
            "agenc": agenc
        })


@app.post("/update-tour", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def admin_edit_tour_submit(
    request: Request,
    tour_id: int = Form(...),
    title: str = Form(...),
    start_time: str = Form(...),
    duration: str = Form(...),
    route: str = Form(...),
    tags: str = Form(...),
    description: str = Form(...)
    ):
    db.edit_tour(tour_id, title, start_time, duration, route, tags, description)
    return templates.TemplateResponse(request=request, name="tour_added.html")


@app.get("/booking/tour/{tour_id}", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def tour_booking(request: Request, tour_id: int):
    args = db.get_tour_by_id(tour_id)
    tour = Tour(*args)

    return templates.TemplateResponse(request=request, name="booking.html", context={"tour": tour})


@app.post("/booking/tour/submit", response_class=HTMLResponse)
@limiter.limit("120/minute")
async def submit_form(
    request: Request,
    tour_id: int = Form(...),
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    ):
    db.add_request(tour_id, full_name, phone, email)
    return templates.TemplateResponse(request=request, name="submit.html")


async def main():
    server = Server(Config(app, port=80))
    await server.serve()


if __name__ == "__main__":
    db.create_tables()
    asyncio.run(main())
