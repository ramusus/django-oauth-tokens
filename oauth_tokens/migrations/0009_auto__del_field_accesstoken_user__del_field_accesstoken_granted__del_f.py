# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'AccessToken.user'
        db.delete_column(u'oauth_tokens_accesstoken', 'user_id')

        # Deleting field 'AccessToken.granted'
        db.delete_column(u'oauth_tokens_accesstoken', 'granted')

        # Deleting field 'AccessToken.expires'
        db.delete_column(u'oauth_tokens_accesstoken', 'expires')

        # Adding field 'AccessToken.granted_at'
        db.add_column(u'oauth_tokens_accesstoken', 'granted_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.datetime(2014, 12, 22, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'AccessToken.expires_in'
        db.add_column(u'oauth_tokens_accesstoken', 'expires_in',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'AccessToken.expires_at'
        db.add_column(u'oauth_tokens_accesstoken', 'expires_at',
                      self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'AccessToken.user_id'
        db.add_column(u'oauth_tokens_accesstoken', 'user_id',
                      self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'AccessToken.user_credentials'
        db.add_column(u'oauth_tokens_accesstoken', 'user_credentials',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['oauth_tokens.UserCredentials'], null=True, blank=True),
                      keep_default=False)


        # Changing field 'AccessToken.scope'
        db.alter_column(u'oauth_tokens_accesstoken', 'scope', self.gf('annoying.fields.JSONField')(max_length=200, null=True))
        # Adding field 'UserCredentials.exception'
        db.add_column(u'oauth_tokens_usercredentials', 'exception',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'AccessToken.user'
        db.add_column(u'oauth_tokens_accesstoken', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['oauth_tokens.UserCredentials'], null=True, blank=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'AccessToken.granted'
        raise RuntimeError("Cannot reverse this migration. 'AccessToken.granted' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'AccessToken.granted'
        db.add_column(u'oauth_tokens_accesstoken', 'granted',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True),
                      keep_default=False)

        # Adding field 'AccessToken.expires'
        db.add_column(u'oauth_tokens_accesstoken', 'expires',
                      self.gf('django.db.models.fields.DateTimeField')(blank=True, null=True, db_index=True),
                      keep_default=False)

        # Deleting field 'AccessToken.granted_at'
        db.delete_column(u'oauth_tokens_accesstoken', 'granted_at')

        # Deleting field 'AccessToken.expires_in'
        db.delete_column(u'oauth_tokens_accesstoken', 'expires_in')

        # Deleting field 'AccessToken.expires_at'
        db.delete_column(u'oauth_tokens_accesstoken', 'expires_at')

        # Deleting field 'AccessToken.user_id'
        db.delete_column(u'oauth_tokens_accesstoken', 'user_id')

        # Deleting field 'AccessToken.user_credentials'
        db.delete_column(u'oauth_tokens_accesstoken', 'user_credentials_id')


        # Changing field 'AccessToken.scope'
        db.alter_column(u'oauth_tokens_accesstoken', 'scope', self.gf('django.db.models.fields.CharField')(max_length=200, null=True))
        # Deleting field 'UserCredentials.exception'
        db.delete_column(u'oauth_tokens_usercredentials', 'exception')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'oauth_tokens.accesstoken': {
            'Meta': {'ordering': "('-granted_at',)", 'object_name': 'AccessToken'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'expires_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'expires_in': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'granted_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'refresh_token': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'scope': ('annoying.fields.JSONField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'token_type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user_credentials': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['oauth_tokens.UserCredentials']", 'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'oauth_tokens.usercredentials': {
            'Meta': {'object_name': 'UserCredentials'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'additional': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'exception': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        }
    }

    complete_apps = ['oauth_tokens']