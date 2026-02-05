"""
MongoDB models and database operations
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.collection import Collection
import jdatetime

from .config import MONGO_URI, DB_NAME


# Pydantic models for API
class LogEntry(BaseModel):
    timestamp: str  # ISO format timestamp
    status: str  # "safe" | "nsfw" | "error"
    details: Optional[str] = None


class LogEntryDB(BaseModel):
    timestamp: datetime
    status: str
    details: Optional[str] = None


# Database connection
_client: Optional[MongoClient] = None
_db = None


def get_db():
    """Get database connection"""
    global _client, _db
    if _client is None:
        _client = MongoClient(MONGO_URI)
        _db = _client[DB_NAME]
    return _db


def get_logs_collection() -> Collection:
    """Get logs collection"""
    db = get_db()
    return db["logs"]


def insert_log(log: LogEntry) -> str:
    """Insert a new log entry"""
    collection = get_logs_collection()
    
    # Parse timestamp
    try:
        ts = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
    except:
        ts = datetime.now()
    
    doc = {
        "timestamp": ts,
        "status": log.status,
        "details": log.details,
        "created_at": datetime.now()
    }
    
    result = collection.insert_one(doc)
    return str(result.inserted_id)


def get_last_update() -> Optional[datetime]:
    """Get the timestamp of the last log entry"""
    collection = get_logs_collection()
    last_log = collection.find_one(sort=[("timestamp", -1)])
    if last_log:
        return last_log["timestamp"]
    return None


def get_logs_for_month(jalali_year: int, jalali_month: int) -> dict:
    """
    Get logs for a specific Jalali month.
    Returns a dict with day numbers as keys and status summary as values.
    """
    # Get start and end dates in Gregorian
    start_jalali = jdatetime.date(jalali_year, jalali_month, 1)
    
    # Get last day of Jalali month
    if jalali_month <= 6:
        days_in_month = 31
    elif jalali_month <= 11:
        days_in_month = 30
    else:  # month 12
        if jdatetime.date(jalali_year, 1, 1).isleap():
            days_in_month = 30
        else:
            days_in_month = 29
    
    end_jalali = jdatetime.date(jalali_year, jalali_month, days_in_month)
    
    # Convert to Gregorian
    start_gregorian = start_jalali.togregorian()
    end_gregorian = end_jalali.togregorian()
    
    start_dt = datetime(start_gregorian.year, start_gregorian.month, start_gregorian.day, 0, 0, 0)
    end_dt = datetime(end_gregorian.year, end_gregorian.month, end_gregorian.day, 23, 59, 59)
    
    collection = get_logs_collection()
    logs = collection.find({
        "timestamp": {"$gte": start_dt, "$lte": end_dt}
    })
    
    # Group by Jalali day
    days_data = {}
    for log in logs:
        ts = log["timestamp"]
        jalali_date = jdatetime.date.fromgregorian(date=ts.date())
        day = jalali_date.day
        
        if day not in days_data:
            days_data[day] = {"safe": 0, "nsfw": 0, "error": 0, "has_data": True}
        
        status = log.get("status", "error")
        if status in days_data[day]:
            days_data[day][status] += 1
    
    # Calculate overall status for each day
    result = {}
    for day in range(1, days_in_month + 1):
        if day in days_data:
            data = days_data[day]
            if data["nsfw"] > 0:
                result[day] = "nsfw"
            elif data["safe"] > 0:
                result[day] = "safe"
            else:
                result[day] = "error"
        else:
            result[day] = "no_data"
    
    return {
        "year": jalali_year,
        "month": jalali_month,
        "days_in_month": days_in_month,
        "days": result
    }


def get_logs_for_day(jalali_year: int, jalali_month: int, jalali_day: int) -> dict:
    """
    Get detailed logs for a specific Jalali day grouped by hour.
    """
    # Convert Jalali date to Gregorian
    jalali_date = jdatetime.date(jalali_year, jalali_month, jalali_day)
    gregorian_date = jalali_date.togregorian()
    
    start_dt = datetime(gregorian_date.year, gregorian_date.month, gregorian_date.day, 0, 0, 0)
    end_dt = datetime(gregorian_date.year, gregorian_date.month, gregorian_date.day, 23, 59, 59)
    
    collection = get_logs_collection()
    logs = collection.find({
        "timestamp": {"$gte": start_dt, "$lte": end_dt}
    }).sort("timestamp", 1)
    
    # Group by hour
    hours_data = {hour: {"safe": 0, "nsfw": 0, "error": 0, "logs": []} for hour in range(24)}
    
    for log in logs:
        ts = log["timestamp"]
        hour = ts.hour
        status = log.get("status", "error")
        
        if status in ["safe", "nsfw", "error"]:
            hours_data[hour][status] += 1
        
        hours_data[hour]["logs"].append({
            "time": ts.strftime("%H:%M:%S"),
            "status": status,
            "details": log.get("details")
        })
    
    # Calculate overall status for each hour
    result = {}
    for hour in range(24):
        data = hours_data[hour]
        if data["nsfw"] > 0:
            status = "nsfw"
        elif data["safe"] > 0:
            status = "safe"
        elif data["error"] > 0:
            status = "error"
        else:
            status = "no_data"
        
        result[hour] = {
            "status": status,
            "count": data["safe"] + data["nsfw"] + data["error"],
            "logs": data["logs"]
        }
    
    return {
        "year": jalali_year,
        "month": jalali_month,
        "day": jalali_day,
        "hours": result
    }
