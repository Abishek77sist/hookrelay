from django.db import models


class Delivery(models.Model):
    """
    "Deliver THIS event to THAT endpoint." One row per (event, endpoint).
    It tracks the overall state; each individual HTTP try is a DeliveryAttempt.

    Status flow:
        PENDING --success--> SUCCESS
        PENDING --fail-----> RETRYING --success--> SUCCESS
                             RETRYING --5th failure--> DEAD  (dead-letter)
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"      # created, not tried yet
        RETRYING = "RETRYING", "Retrying"   # failed at least once, will try again
        SUCCESS = "SUCCESS", "Success"      # receiver answered with 2xx
        DEAD = "DEAD", "Dead"               # gave up after max attempts

    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="deliveries"
    )
    endpoint = models.ForeignKey(
        "endpoints.Endpoint", on_delete=models.CASCADE, related_name="deliveries"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    attempt_count = models.PositiveIntegerField(default=0)
    # When the next retry is due (null when nothing is scheduled).
    next_retry_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # One delivery per event+endpoint. Also protects us from creating
            # duplicates if the fan-out task runs twice. The unique index also
            # speeds up "all deliveries of this event".
            models.UniqueConstraint(
                fields=["event", "endpoint"], name="uniq_event_endpoint"
            ),
        ]
        indexes = [
            # The retry scheduler asks: "RETRYING deliveries whose
            # next_retry_at is in the past". This index makes that cheap.
            models.Index(fields=["status", "next_retry_at"], name="dl_status_retry_idx"),
            # "Deliveries of this endpoint, newest first" (list filter by
            # endpoint + date, and stats per endpoint).
            models.Index(fields=["endpoint", "-created_at"], name="dl_endpoint_created_idx"),
            # List filter by status + date range.
            models.Index(fields=["status", "created_at"], name="dl_status_created_idx"),
        ]

    def __str__(self):
        return f"Delivery {self.pk} [{self.status}]"


class DeliveryAttempt(models.Model):
    """
    One single HTTP try. We keep ALL attempts forever (an audit trail):
    this is how you debug "why did my webhook not arrive?".
    """

    delivery = models.ForeignKey(
        Delivery, on_delete=models.CASCADE, related_name="attempts"
    )
    attempt_number = models.PositiveIntegerField()  # 1, 2, 3...
    success = models.BooleanField(default=False)
    # Null when we never got an HTTP response (timeout, connection refused...)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    # Only the first N characters (see HOOKRELAY_RESPONSE_BODY_MAX_CHARS)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Attempt numbers are unique inside a delivery. The index also
            # serves "show attempts of delivery X in order".
            models.UniqueConstraint(
                fields=["delivery", "attempt_number"], name="uniq_delivery_attempt_no"
            ),
        ]
        indexes = [
            # The stats endpoint reads "all attempts in the last 24 hours".
            # This index lets the database jump straight to recent rows.
            models.Index(fields=["created_at"], name="att_created_idx"),
        ]

    def __str__(self):
        return f"Attempt {self.attempt_number} of delivery {self.delivery_id}"