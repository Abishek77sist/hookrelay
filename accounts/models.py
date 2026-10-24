from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Our own User model. It is identical to Django's, except that the
    email must be unique (we use it as the account identity).
    Always create a custom user model at the start of a project:
    changing it later is painful.
    """

    email = models.EmailField(unique=True)


class ApiKey(models.Model):
    """
    An API key used in the header:  Authorization: Api-Key <key>

    SECURITY: we NEVER store the real key. We store only its SHA-256 hash.
    The real key is shown to the user exactly once, when it is created.
    (Like a password: if our database leaks, the attacker cannot use the hashes.)
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=100, blank=True)
    # First 8 characters of the key, so the user can recognise which key is which.
    prefix = models.CharField(max_length=12)
    # SHA-256 hex digest = always 64 characters.
    key_hash = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # INDEX NOTE: `unique=True` on key_hash already creates an index.
        # That index is used on EVERY API request (we look the key up by its
        # hash), so it must be fast.
        indexes = [
            # Used to list "all active keys of this user" in the dashboard/API.
            models.Index(fields=["user", "is_active"], name="apikey_user_active_idx"),
        ]

    def __str__(self):
        return f"{self.prefix}... ({self.user_id})"