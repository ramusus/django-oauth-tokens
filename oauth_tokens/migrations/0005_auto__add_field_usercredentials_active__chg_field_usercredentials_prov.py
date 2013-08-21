# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserCredentials.active'
        db.add_column('oauth_tokens_usercredentials', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


        # Changing field 'UserCredentials.provider'
        db.alter_column('oauth_tokens_usercredentials', 'provider', self.gf('django.db.models.fields.CharField')(max_length=20))

    def backwards(self, orm):
        # Deleting field 'UserCredentials.active'
        db.delete_column('oauth_tokens_usercredentials', 'active')


        # Changing field 'UserCredentials.provider'
        db.alter_column('oauth_tokens_usercredentials', 'provider', self.gf('django.db.models.fields.CharField')(max_length=100))

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
            'token_type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['oauth_tokens.UserCredentials']", 'null': 'True', 'blank': 'True'})
        },
        'oauth_tokens.usercredentials': {
            'Meta': {'object_name': 'UserCredentials'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'additional': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['oauth_tokens']