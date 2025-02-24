from django.db import models
from django.utils import timezone

class GoldPrice(models.Model):
    title = models.CharField(max_length=255)  # e.g., "هرگرم طلای 18 عیار"
    price = models.CharField(max_length=50)  # Store as a string to handle Persian numbers
    recorded_at = models.DateTimeField(default=timezone.now)  # Timestamp for when price is recorded

    def __str__(self):
        return f"{self.title}: {self.price} ({self.recorded_at.strftime('%Y-%m-%d %H:%M')})"
