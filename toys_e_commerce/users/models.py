from django.db import models

class User(models.Model):
    user_id = models.CharField(max_length=255, unique=True, db_index=True)
    full_name = models.CharField(max_length=255, db_index=True)
    phone_number = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name
