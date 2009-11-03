# -*- coding: utf-8 -*-
from google.appengine.ext import db

class BaseModel(db.Model):
    def put(self):
        if self.before_put():
            super(BaseModel, self).put()

    save = put

    def before_put(self):
        pass
