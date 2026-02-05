import os
import sys
import time
import threading
import signal
import subprocess
import ctypes
import winreg
import base64
import json
from datetime import datetime

import pyautogui
import requests

# ===== تنظیمات (از Environment Variables ویندوز خوانده می‌شوند) =====

# تنظیمات عمومی
INTERVAL_MINUTES = int(os.getenv("ACC_INTERVAL_MINUTES", "1"))  # هر چند دقیقه اسکرین‌شات بگیره
VISION_MODEL = os.getenv("ACC_VISION_MODEL", "google/gemma-3-4b-it:free")  # مدل AI

# انتخاب حالت اتصال: true = پروکسی سرور | false = مستقیم
USE_SERVER_PROXY_FOR_OPENROUTER = os.getenv("ACC_USE_SERVER_PROXY", "true").lower() in ("true", "1", "yes")

# ===== حالت پروکسی سرور (ACC_USE_SERVER_PROXY=true) =====
SERVER_BASE_URL = os.getenv("ACC_SERVER_URL", "http://localhost:8000")  # آدرس سرور داشبورد
OPENROUTER_PROXY_TOKEN = os.getenv("ACC_PROXY_TOKEN", "")  # توکن امنیتی پروکسی

# ===== حالت مستقیم (ACC_USE_SERVER_PROXY=false) =====
OPENROUTER_API_KEY = os.getenv("ACC_OPENROUTER_API_KEY", "")  # کلید OpenRouter
OPENROUTER_API_URL = os.getenv("ACC_OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
SOCKS5_PROXY = os.getenv("ACC_SOCKS5_PROXY", "")  # پروکسی SOCKS5 (مثال: socks5://host:port)

# آدرس‌های محاسبه‌شده
SERVER_LOG_URL = f"{SERVER_BASE_URL}/api/log"
OPENROUTER_PROXY_URL = f"{SERVER_BASE_URL}/api/openrouter"


def get_proxies():
    """دریافت تنظیمات پروکسی برای requests"""
    if SOCKS5_PROXY and SOCKS5_PROXY.strip():
        return {
            "http": SOCKS5_PROXY,
            "https": SOCKS5_PROXY
        }
    return None

# مسیر پوشه اسکرین‌شات‌ها کنار فایل exe
if getattr(sys, 'frozen', False):
    # اگر به exe تبدیل شده
    APP_DIR = os.path.dirname(sys.executable)
else:
    # اگر اسکریپت پایتون اجرا شده
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

SAVE_DIR = os.path.join(APP_DIR, "Screenshots")
APP_NAME = "AccountabilityScreenshot"

# اگر پوشه وجود نداشت، بساز
os.makedirs(SAVE_DIR, exist_ok=True)


def hide_console():
    """مخفی کردن پنجره کنسول"""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
    except:
        pass


def add_to_startup():
    """اضافه کردن برنامه به استارتاپ ویندوز"""
    try:
        # مسیر فایل اجرایی
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(__file__)
        
        # اضافه به رجیستری
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        log_message("Added to Windows startup")
    except Exception as e:
        log_message(f"Failed to add to startup: {e}")


def block_signals():
    """غیرفعال کردن سیگنال‌های خاتمه"""
    def ignore_signal(sig, frame):
        log_message(f"Blocked termination attempt (signal {sig})")
        return  # چیزی انجام نده
    
    # بلاک کردن همه سیگنال‌های خاتمه
    signal.signal(signal.SIGINT, ignore_signal)   # Ctrl+C
    signal.signal(signal.SIGTERM, ignore_signal)  # Terminate
    signal.signal(signal.SIGBREAK, ignore_signal) # Ctrl+Break on Windows


def log_message(msg):
    """ثبت پیام با زمان"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{now}] {msg}"
    print(log_line)
    
    # ذخیره لاگ در فایل
    try:
        log_file = os.path.join(SAVE_DIR, "activity_log.txt")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except:
        pass


def image_to_base64(image_path):
    """تبدیل تصویر به base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def check_image_for_nsfw(image_path):
    """بررسی تصویر برای محتوای نامناسب با مدل هوش مصنوعی"""
    try:
        base64_image = image_to_base64(image_path)

        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this screenshot. Is there any pornographic, nude, or sexually explicit content visible? Reply with ONLY 'YES' if there is ANY inappropriate content, or 'NO' if the content is safe. Do not explain, just answer YES or NO."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 10
        }

        # انتخاب مسیر ارسال درخواست: مستقیم یا پروکسی سرور
        if USE_SERVER_PROXY_FOR_OPENROUTER:
            headers = {"Content-Type": "application/json"}
            if OPENROUTER_PROXY_TOKEN:
                headers["X-Proxy-Token"] = OPENROUTER_PROXY_TOKEN

            response = requests.post(
                OPENROUTER_PROXY_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )
        else:
            if not OPENROUTER_API_KEY or not OPENROUTER_API_KEY.strip():
                log_message("⚠️ API key not configured, skipping NSFW check (direct mode)")
                return None, "API key not set (set ACC_OPENROUTER_API_KEY)"

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=30,
                proxies=get_proxies(),
            )
        
        if response.status_code == 200:
            result = response.json()
            message = result["choices"][0]["message"]
            answer = message.get("content", "") or ""
            
            log_message(f"AI Response: '{answer}'")
            
            answer_upper = answer.strip().upper()
            is_nsfw = answer_upper.startswith("YES") or "YES" in answer_upper[:20]
            return is_nsfw, answer
        else:
            log_message(f"API error: {response.status_code} - {response.text}")
            return None, f"API error: {response.status_code}"
            
    except Exception as e:
        log_message(f"NSFW check failed: {e}")
        return None, str(e)


def log_nsfw_alert(image_path, detection_result):
    """ثبت هشدار محتوای نامناسب"""
    alert_file = os.path.join(SAVE_DIR, "nsfw_alerts.txt")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_line = f"[{now}] 🚨 NSFW DETECTED: {image_path} | Result: {detection_result}\n"
    
    try:
        with open(alert_file, "a", encoding="utf-8") as f:
            f.write(alert_line)
    except:
        pass
    
    log_message(f"🚨 NSFW ALERT: {os.path.basename(image_path)}")


def send_log_to_server(status, details=None):
    """ارسال لاگ به سرور داشبورد"""
    try:
        payload = {
            "timestamp": datetime.now().isoformat(),
            "status": status,  # "safe", "nsfw", "error"
            "details": details
        }
        response = requests.post(SERVER_LOG_URL, json=payload, timeout=5)
        if response.status_code == 200:
            log_message(f"📤 Log sent to server: {status}")
        else:
            log_message(f"⚠️ Server response: {response.status_code}")
    except Exception as e:
        log_message(f"⚠️ Failed to send log to server: {e}")


def take_screenshot():
    """گرفتن اسکرین‌شات و ذخیره روی دیسک"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(SAVE_DIR, f"screenshot_{now}.png")
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        log_message(f"Saved screenshot: {filename}")
        
        # بررسی محتوای نامناسب
        is_nsfw, result = check_image_for_nsfw(filename)
        if is_nsfw is True:
            log_nsfw_alert(filename, result)
            # ارسال لاگ به سرور
            send_log_to_server("nsfw", result)
            # انتقال به پوشه flagged
            flagged_dir = os.path.join(SAVE_DIR, "flagged")
            os.makedirs(flagged_dir, exist_ok=True)
            flagged_path = os.path.join(flagged_dir, os.path.basename(filename))
            os.rename(filename, flagged_path)
            log_message(f"Moved to flagged: {flagged_path}")
        elif is_nsfw is False:
            log_message(f"✅ Content check: SAFE")
            # ارسال لاگ به سرور
            send_log_to_server("safe", "Content is safe")
        else:
            log_message(f"⚠️ Content check: {result}")
            # ارسال لاگ به سرور با وضعیت خطا
            send_log_to_server("error", result)
            
    except Exception as e:
        log_message(f"Screenshot failed: {e}")
        # ارسال لاگ خطا به سرور
        send_log_to_server("error", str(e))


def screenshot_loop():
    """لوپ بی‌نهایت که هر X دقیقه اسکرین‌شات می‌گیره"""
    while True:
        try:
            take_screenshot()
        except:
            pass
        time.sleep(INTERVAL_MINUTES * 60)


def watchdog():
    """نگهبان - اگر برنامه بسته شد دوباره اجرا کن"""
    while True:
        time.sleep(30)
        # چک کن که هنوز در حال اجراست
        try:
            # یک فایل بنویس که نشون بده زنده‌ایم
            heartbeat_file = os.path.join(SAVE_DIR, "heartbeat.txt")
            with open(heartbeat_file, "w") as f:
                f.write(str(time.time()))
        except:
            pass


def respawn_on_exit():
    """اگر برنامه بسته شد، دوباره اجرا شو"""
    import atexit
    
    def respawn():
        try:
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(
                    [sys.executable, os.path.abspath(__file__)],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
        except:
            pass
    
    atexit.register(respawn)


def prevent_multiple_instances():
    """جلوگیری از اجرای چند نسخه همزمان"""
    import socket
    try:
        # استفاده از سوکت به عنوان mutex
        global _instance_socket
        _instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _instance_socket.bind(('127.0.0.1', 59123))
        return True
    except socket.error:
        return False


def main():
    # چک کن که فقط یک نسخه اجرا باشه
    if not prevent_multiple_instances():
        log_message("Already running, exiting duplicate instance")
        sys.exit(0)
    
    log_message("=== Accountability app started ===")
    log_message(f"Config: INTERVAL={INTERVAL_MINUTES}min, USE_PROXY={USE_SERVER_PROXY_FOR_OPENROUTER}, SERVER={SERVER_BASE_URL}")
    
    # # مخفی کردن کنسول
    # hide_console()
    
    # # بلاک کردن سیگنال‌های خاتمه
    # block_signals()
    
    # # اضافه به استارتاپ
    # add_to_startup()
    
    # # تنظیم respawn
    # respawn_on_exit()
    
    # شروع ترد نگهبان
    watchdog_thread = threading.Thread(target=watchdog, daemon=True)
    watchdog_thread.start()
    
    # یک اسکرین‌شات فوری بگیر
    take_screenshot()
    
    log_message("Running in background. Taking screenshots every {} minutes.".format(INTERVAL_MINUTES))
    
    # لوپ اصلی - هرگز متوقف نمی‌شود
    screenshot_loop()


if __name__ == "__main__":
    main()
