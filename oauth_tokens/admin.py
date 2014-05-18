from django.contrib import admin
from models import AccessToken, UserCredentials

class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('provider','access_token','user','granted','expires')
    list_display_links = ('access_token',)

class UserCredentialsAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'active')

admin.site.register(AccessToken, AccessTokenAdmin)
admin.site.register(UserCredentials, UserCredentialsAdmin)