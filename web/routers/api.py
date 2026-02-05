"""
API endpoints for the accountability dashboard
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import Response
from typing import Optional
import jdatetime
import requests

from ..models import LogEntry, insert_log, get_last_update, get_logs_for_month, get_logs_for_day
from ..auth import require_auth
from ..config import (
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    OPENROUTER_PROXY_TOKEN,
    OPENROUTER_SOCKS5_PROXY,
)

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/log")
async def receive_log(log: LogEntry):
    """
    Receive a log entry from the screenshot application.
    This endpoint does NOT require authentication (called by the client app).
    """
    log_id = insert_log(log)
    return {"status": "ok", "id": log_id}


@router.post("/openrouter")
async def openrouter_proxy(request: Request):
    """
    Proxy endpoint for OpenRouter.
    Client sends the OpenRouter JSON payload (model/messages/...) WITHOUT Authorization header.
    Server adds Authorization and forwards the request to OpenRouter, returning the raw response.
    """
    if OPENROUTER_PROXY_TOKEN:
        provided = request.headers.get("X-Proxy-Token", "")
        if provided != OPENROUTER_PROXY_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid proxy token",
            )

    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENROUTER_API_KEY is not configured on server",
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    proxies = None
    if OPENROUTER_SOCKS5_PROXY:
        proxies = {
            "http": OPENROUTER_SOCKS5_PROXY,
            "https": OPENROUTER_SOCKS5_PROXY,
        }

    try:
        upstream = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=60,
            proxies=proxies,
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream request failed: {e}",
        )

    # Return raw upstream response (status + body)
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type="application/json",
    )


@router.get("/last-update")
async def last_update(request: Request, user: str = Depends(require_auth)):
    """Get the timestamp of the last received log"""
    last_ts = get_last_update()
    if last_ts:
        # Convert to Jalali
        jalali_dt = jdatetime.datetime.fromgregorian(datetime=last_ts)
        return {
            "timestamp": last_ts.isoformat(),
            "jalali": jalali_dt.strftime("%Y/%m/%d %H:%M:%S"),
            "has_data": True
        }
    return {"has_data": False}


@router.get("/month/{year}/{month}")
async def get_month_data(year: int, month: int, request: Request, user: str = Depends(require_auth)):
    """Get logs summary for a specific Jalali month"""
    if month < 1 or month > 12:
        return {"error": "Invalid month"}
    
    data = get_logs_for_month(year, month)
    
    # Add month name in Persian
    month_names = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    data["month_name"] = month_names[month - 1]
    
    return data


@router.get("/day/{year}/{month}/{day}")
async def get_day_data(year: int, month: int, day: int, request: Request, user: str = Depends(require_auth)):
    """Get detailed logs for a specific Jalali day"""
    if month < 1 or month > 12:
        return {"error": "Invalid month"}
    if day < 1 or day > 31:
        return {"error": "Invalid day"}
    
    data = get_logs_for_day(year, month, day)
    
    # Add month name in Persian
    month_names = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    data["month_name"] = month_names[month - 1]
    
    return data


@router.get("/current-date")
async def get_current_date(request: Request, user: str = Depends(require_auth)):
    """Get current Jalali date"""
    now = jdatetime.datetime.now()
    return {
        "year": now.year,
        "month": now.month,
        "day": now.day
    }
