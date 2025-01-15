from django.contrib import admin
from users.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'full_name', 'phone_number', 'created_at', 'updated_at')
    search_fields = ('user_id', 'full_name', 'phone_number')
