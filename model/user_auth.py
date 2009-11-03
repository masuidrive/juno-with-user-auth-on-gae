# -*- coding: utf-8 -*-
import urllib
import hashlib
import random

from google.appengine.ext import db
from google.appengine.api import mail
import yaml

import gae_util
import dbex

import model

class UserAuthentication(dbex.BaseModel):
    user = db.ReferenceProperty(model.User)
    email = db.EmailProperty()
    salt = db.StringProperty()
    crypted_password = db.StringProperty()
    accept_login = db.BooleanProperty(default=True, required=True)
    _uniques = set([(email,)])

    @classmethod
    def email_is_registered(cls, email):
        return not not cls.all().filter('email', email).fetch(1)

    def authorize(self, password):
        return self.accept_login and self.crypt_password(password)==self.crypted_password
    
    def crypt_password(self, password):
        return hashlib.sha1(password+self.salt).hexdigest()
    
    def update_password(self, password):
        self.salt = hashlib.sha1("%f!!%f" % (random.random(), random.random())).hexdigest()
        self.crypted_password = self.crypt_password(password)


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
    
    def activation(self, key):
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
