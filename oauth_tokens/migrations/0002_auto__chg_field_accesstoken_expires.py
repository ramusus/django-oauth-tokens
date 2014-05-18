# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'AccessToken.expires'
        db.alter_column('oauth_tokens_accesstoken', 'expires', self.gf('django.db.models.fields.DateTimeField')(null=True))
    def backwards(self, orm):

        # Changing field 'AccessToken.expires'
        db.alter_column('oauth_tokens_accesstoken', 'expires', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 3, 16, 0, 0)))
    models = {
        'oauth_tokens.accesstoken': {
            'Meta': {'ordering': "('-granted',)", 'object_name': 'AccessToken'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'granted': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'refresh_token': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'scope': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'token_type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['oauth_tokens']