# -*- coding: utf-8 -*-
import urllib
import hashlib
import random
import yaml
from datetime import datetime

from google.appengine.api import mail
from google.appengine.ext import db

import juno
import gae_util
import dbex
import model

class User(dbex.BaseModel):
    account = db.StringProperty(required=True)
    fullname = db.StringProperty(required=True)
    registered_at = db.DateTimeProperty(auto_now_add=True)
    posted_at = db.DateTimeProperty()
    _uniques = set([(account,)])
    
    @classmethod
    def authenticate(cls, login, password):
        user_auths = UserAuthentication.all().filter("email", login).fetch(1)
        if user_auths:
            if user_auths[0].authorize(password):
                return user_auths[0].parent()
        else:
            users = cls.all().filter("account", login).fetch(1)
            if users:
                user_auths = UserAuthentication.all().filter("user", users[0]).fetch(1)
                if user_auths and user_auths[0].authorize(password):
                    return users[0]
        return None
    
    @classmethod
    def get_by_account(cls, account):
        try:
            return cls.all().filter("account", account).fetch(1)[0]
        except:
            return None
    
    def update_posted_at(self, posted_at=datetime.now()):
        self.posted_at = posted_at
        self.put()
        model.follow.Follower.update_posted_at(self, posted_at)


class UserAuthentication(dbex.BaseModel):
    user = db.ReferenceProperty(User, required=True)
    email = db.EmailProperty(required=True)
    salt = db.StringProperty(required=True)
    crypted_password = db.StringProperty(required=True)
    accept_login = db.BooleanProperty(default=True, required=True)
    _uniques = set([(email,)])

    @classmethod
    def email_is_registered(cls, email):
        return not not cls.all().filter('email', email).fetch(1)
    
    @classmethod
    def crypt_password(cls, password, salt):
        return hashlib.sha1(password+salt).hexdigest()
    
    @classmethod
    def generate_salt(cls):
        return hashlib.sha1("%f!!%f" % (random.random(), random.random())).hexdigest()
    
    def authorize(self, password):
        return self.accept_login and self.crypt_password(password, self.salt)==self.crypted_password
    

class UserConfirmationEmail:
    config = None
    
    def __init__(self, to_addr):
        if not self.config:
            self.config = juno.site_config('email-confirmation')
        self.to_addr = to_addr
    
    def activate(self, key):
        return self.generate_key()==key
    
    def generate_key(self):
        return hashlib.sha1(self.to_addr+self.config['salt']).hexdigest()

    def authorize_url(self):
        return "%s/signup/confirm_email?%s" % (self.config['http_prefix'], urllib.urlencode({'email':self.to_addr, 'key':self.generate_key()}))
    
    def send(self):
        mail.send_mail(
            sender = self.config['sender'],
            to = self.to_addr,
            subject = self.config['subject'],
            body = self.config['body'] % (self.authorize_url()))
