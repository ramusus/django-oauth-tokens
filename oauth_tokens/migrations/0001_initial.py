# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AccessToken'
        db.create_table('oauth_tokens_accesstoken', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('provider', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('granted', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('access_token', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('expires', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('token_type', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('refresh_token', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('scope', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('oauth_tokens', ['AccessToken'])

    def backwards(self, orm):
        # Deleting model 'AccessToken'
        db.delete_table('oauth_tokens_accesstoken')

    models = {
        'oauth_tokens.accesstoken': {
            'Meta': {'ordering': "('-granted',)", 'object_name': 'AccessToken'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'expires': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'granted': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'refresh_token': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'scope': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'token_type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['oauth_tokens']