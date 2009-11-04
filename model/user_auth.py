# -*- coding: utf-8 -*-
import urllib
import hashlib
import random

from google.appengine.ext import db
from google.appengine.api import mail
import yaml

import gae_util
import model

class UserAuthentication(db.Model):
    user = db.ReferenceProperty(model.User, required=True)
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
    config = {}
    
    @classmethod
    def load_settings(cls, path):
        env = 'production'
        if gae_util.is_development_env():
            env = 'development'
        string = open('user-auth.yaml').read().decode('utf8')
        cls.config = yaml.load(string)[env]['email-confimation']
    
    def __init__(self, to_addr):
        self.to_addr = to_addr
        self.salt = "your-secret-key"
    
    def activate(self, key):
        return self.generate_key()==key

    def generate_key(self):
        return hashlib.sha1(self.to_addr+self.salt).hexdigest()

    def authorize_url(self):
        return "%s/signup/confirm_email?%s" % (self.config['http_prefix'], urllib.urlencode({'email':self.to_addr, 'key':self.generate_key()}))
    
    def send(self):
        mail.send_mail(
            sender = self.config['sender'],
            to = self.to_addr,
            subject = self.config['subject'],
            body = self.config['body'] % (self.authorize_url()))
