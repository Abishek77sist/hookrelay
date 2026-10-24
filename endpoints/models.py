import secrets

from django.conf import settings
from django.db import models


def generate_secret() -> str:
    """Random secret used to sign webhooks (64 hex characters)."""
    return secrets.token_hex(32)


class Endpoint(models.Model):
    """
    A URL (owned by a user) where we send webhooks.
    The receiver uses `secret` to verify that a webhook really came from us.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="endpoints"
    )
    target_url = models.URLField(max_length=2000)
    secret = models.CharField(max_length=64, default=generate_secret, editable=False)
    # List of event type strings, e.g. ["order.created", "order.paid"]
    event_types = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    # --- Circuit breaker fields (used in phase 3) ---
    # How many deliveries failed in a row. Reset to 0 on any success.
    consecutive_failures = models.PositiveIntegerField(default=0)
    # Why and when the circuit breaker disabled this endpoint.
    disabled_reason = models.CharField(max_length=255, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # When an event arrives we ask: "which ACTIVE endpoints does THIS
            # user have?" (then check event_types). This index answers that
            # without scanning other users' endpoints.
            models.Index(fields=["user", "is_active"], name="ep_user_active_idx"),
        ]

    def __str__(self):
        return f"Endpoint {self.pk} -> {self.target_url}"