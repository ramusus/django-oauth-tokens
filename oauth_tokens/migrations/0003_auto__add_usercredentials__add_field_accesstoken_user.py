# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserCredentials'
        db.create_table('oauth_tokens_usercredentials', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('additional', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('provider', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('oauth_tokens', ['UserCredentials'])

        # Adding field 'AccessToken.user'
        db.add_column('oauth_tokens_accesstoken', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['oauth_tokens.UserCredentials'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'UserCredentials'
        db.delete_table('oauth_tokens_usercredentials')

        # Deleting field 'AccessToken.user'
        db.delete_column('oauth_tokens_accesstoken', 'user_id')


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
            'additional': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['oauth_tokens']