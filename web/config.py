"""
تنظیمات اپلیکیشن
"""
import os

# تنظیمات لاگین
USERNAME = os.getenv("APP_USERNAME", "admin")
PASSWORD = os.getenv("APP_PASSWORD", "1030")

# تنظیمات MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:stlt1030@87.107.10.230:27017")
DB_NAME = os.getenv("DB_NAME", "accountability")

# تنظیمات OpenRouter (فقط روی سرور)
# نکته امنیتی: کلید را هاردکد نکنید؛ فقط از Environment Variables بخوانید.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv(
    "OPENROUTER_API_URL",
    "https://openrouter.ai/api/v1/chat/completions",
)
# اگر مقداردهی شود، درخواست‌های OpenRouter از طریق SOCKS5 ارسال می‌شوند
# مثال: socks5://user:pass@host:port
OPENROUTER_SOCKS5_PROXY = os.getenv("OPENROUTER_SOCKS5_PROXY", "")
# اگر مقداردهی شود، کلاینت باید هدر X-Proxy-Token را با همین مقدار بفرستد
OPENROUTER_PROXY_TOKEN = os.getenv("OPENROUTER_PROXY_TOKEN", "")

# کلید امنیتی برای session
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")

# تنظیمات session
SESSION_EXPIRE_HOURS = 24
