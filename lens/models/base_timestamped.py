from django.db import models
from django.utils import timezone

class TimeStampedModel(models.Model):
    """
    Abstract base model that provides commonly used date and time fields.
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True
