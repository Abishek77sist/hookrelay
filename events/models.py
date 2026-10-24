from django.conf import settings
from django.db import models
from django.db.models import Q


class Event(models.Model):
    """
    Something that happened in the user's system ("order.created" + JSON data).
    We accept it, store it, and deliver it to all subscribed endpoints.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    # Value of the "Idempotency-Key" header. Optional (null when not sent).
    idempotency_key = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # "idempotency_key unique per user". This creates a UNIQUE INDEX on
            # (user, idempotency_key), which also makes the lookup "did this
            # user already send this key?" fast. The condition means events
            # without a key do not conflict with each other.
            #
            # NOTE for phase 2: keys must only be remembered for 24 hours. When
            # we meet a key older than 24h we will clear it on the old event
            # (set to null) and create the new event. That keeps this DB rule
            # simple and the 24h rule in services.py.
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="uniq_user_idem_key",
            ),
        ]
        indexes = [
            # For "show my newest events" and date-range queries per user.
            models.Index(fields=["user", "-created_at"], name="ev_user_created_idx"),
        ]

    def __str__(self):
        return f"Event {self.pk} ({self.event_type})"