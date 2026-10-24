"""Small shared views. The rate limiter and security helpers arrive in later phases."""
import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health(request):
    """
    Health check: confirms the web container can reach Postgres and Redis.
    Returns 200 if both work, 503 otherwise.
    """
    result = {"database": "ok", "redis": "ok"}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as exc:  # broad on purpose: any failure means "not healthy"
        result["database"] = f"error: {exc}"

    try:
        redis.from_url(settings.REDIS_URL).ping()
    except Exception as exc:
        result["redis"] = f"error: {exc}"

    healthy = all(value == "ok" for value in result.values())
    result["status"] = "ok" if healthy else "unhealthy"
    return JsonResponse(result, status=200 if healthy else 503)