from django.contrib import admin
from models import AccessToken

class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('provider','access_token','granted','expires')
    list_display_links = ('access_token',)

admin.site.register(AccessToken, AccessTokenAdmin)