"""
HTML views for the accountability dashboard
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import jdatetime
import os

from ..auth import verify_credentials, create_session_token, get_current_user, login_required

router = APIRouter(tags=["views"])

# Setup templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Redirect to calendar or login"""
    redirect = login_required(request)
    if redirect:
        return redirect
    return RedirectResponse(url="/calendar", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/calendar", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission"""
    if verify_credentials(username, password):
        token = create_session_token(username)
        response = RedirectResponse(url="/calendar", status_code=302)
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            max_age=86400  # 24 hours
        )
        return response
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "نام کاربری یا رمز عبور اشتباه است"
    })


@router.get("/logout")
async def logout(request: Request):
    """Logout and clear session"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="session_token")
    return response


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request):
    """Show calendar page"""
    redirect = login_required(request)
    if redirect:
        return redirect
    
    # Get current Jalali date
    now = jdatetime.datetime.now()
    
    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "current_year": now.year,
        "current_month": now.month,
        "current_day": now.day
    })


@router.get("/day/{year}/{month}/{day}", response_class=HTMLResponse)
async def day_detail_page(request: Request, year: int, month: int, day: int):
    """Show day detail page"""
    redirect = login_required(request)
    if redirect:
        return redirect
    
    month_names = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    
    return templates.TemplateResponse("day_detail.html", {
        "request": request,
        "year": year,
        "month": month,
        "day": day,
        "month_name": month_names[month - 1] if 1 <= month <= 12 else ""
    })
