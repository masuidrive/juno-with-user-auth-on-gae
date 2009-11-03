# -*- coding: utf-8 -*-
from google.appengine.ext import db
import dbex
import model

class User(dbex.BaseModel):
    account = db.StringProperty(required=True)
    registered_at = db.DateTimeProperty(auto_now_add=True)
    _uniques = set([(account,)])
    
    fullname = db.StringProperty(required=True)
    
    @classmethod
    def authenticate(cls, login, password):
        user_auths = model.UserAuthentication.all().filter("email", login).fetch(1)
        if user_auths:
            if user_auths[0].authorize(password):
                return user_auths[0].parent()
        else:
            users = cls.all().filter("account", login).fetch(1)
            if users:
                user_auths = model.UserAuthentication.all().ancestor(users[0]).fetch(1)
                if user_auths and user_auths[0].authorize(password):
                    return users[0]
        return None
    
    @classmethod
    def get_by_account(cls, account):
        try:
            return cls.all().filter("account", account).fetch(1)[0]
        except:
            return None
    
    @classmethod
    def signup(cls, params):
        user = auth = None
        try:
            user = User(account=params['account'], fullname=params['fullname'])
            if not user.is_valid(): raise Exception, "rollback"
            user.put()
            auth = model.UserAuthentication(parent=user, user=user, email=params['email'])
            auth.update_password(params['password'])
            if not auth.is_valid(): raise Exception, "rollback"
            auth.put()
            return user
        except:
            user.delete()
            auth.delete()
            return None
