from django.contrib import admin

from .models import User, Subscribe


class UserAdmin(admin.ModelAdmin):
    list_filter = ('username', 'email')
    exclude = ('password',)


admin.site.register(User, UserAdmin)
admin.site.register(Subscribe)
