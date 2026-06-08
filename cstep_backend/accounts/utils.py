import random
import string
from django.core.cache import cache
from django.conf import settings


def generate_otp(length=6):
    return "".join(random.choices(string.digits, k=length))


def set_otp(key: str, otp: str):
    cache.set(key, otp, timeout=settings.OTP_EXPIRE_SECONDS)


def get_otp(key: str):
    return cache.get(key)


def delete_otp(key: str):
    cache.delete(key)


def phone_otp_key(phone: str) -> str:
    return f"otp:phone:{phone}"


def email_otp_key(email: str) -> str:
    return f"otp:email:{email}"
