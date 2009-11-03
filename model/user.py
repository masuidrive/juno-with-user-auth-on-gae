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
        user_auths = model.UserAuthentication.all().filter("email =", login).fetch(1)
        if len(user_auths)>0:
            if user_auths[0].authorize(password):
                return user_auths[0].parent()
        else:
            users = cls.all().filter("account =", login).fetch(1)
            if len(users)>0:
                user_auths = model.UserAuthentication.all().ancestor(users[0]).fetch(1)
                if len(user_auths)>0 and user_auths[0].authorize(password):
                    return users[0]
        return None
    
    @classmethod
    def get_by_account(cls, account):
        try:
            return cls.all().filter("account =", account).fetch(1)[0]
        except:
            return None
