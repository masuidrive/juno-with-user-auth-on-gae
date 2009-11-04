# -*- coding: utf-8 -*-
from datetime import datetime
from google.appengine.ext import db
import model

class User(db.Model):
    account = db.StringProperty(required=True)
    fullname = db.StringProperty(required=True)
    registered_at = db.DateTimeProperty(auto_now_add=True)
    posted_at = db.DateTimeProperty()
    _uniques = set([(account,)])
    
    @classmethod
    def authenticate(cls, login, password):
        user_auths = model.UserAuthentication.all().filter("email", login).fetch(1)
        if user_auths:
            if user_auths[0].authorize(password):
                return user_auths[0].parent()
        else:
            users = cls.all().filter("account", login).fetch(1)
            if users:
                user_auths = model.UserAuthentication.all().filter("user", users[0]).fetch(1)
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
        model.Follower.update_posted_at(self, posted_at)
