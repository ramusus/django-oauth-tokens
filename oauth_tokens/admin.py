from django.contrib import admin

from .models import AccessToken, UserCredentials


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('provider', 'access_token', 'user_credentials', 'granted_at', 'expires_at')
    list_display_links = ('access_token',)
    list_filter = ('provider',)


class UserCredentialsAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'username', 'active')
    list_filter = ('provider',)

admin.site.register(AccessToken, AccessTokenAdmin)
admin.site.register(UserCredentials, UserCredentialsAdmin)
