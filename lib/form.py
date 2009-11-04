import re
from google.appengine.ext import db
from juno import *
import model

class Validator(object):
    def validate(self):
        return False


class RegexpValidator(Validator):
    def __init__(self, property=None, regexp=None, message="%s is incorrect format"):
        self.property = property
        self.message = message
        self.regexp = regexp

    def validate(self, params, entries=None):
        if not re.match(self.regexp, params[self.property]):
            return Error(self.property, self.message)
        return None


class RequiredValidator(Validator):
    def __init__(self, property=None, message="%s is required"):
        self.property = property
        self.message = message

    def validate(self, params, entries=None):
        if not params[self.property]:
            return Error(self.property, self.message)
        return None


class ConfirmedValidator(Validator):
    def __init__(self, property=None, confirmation_property=None, message="%s is required"):
        self.property = property
        self.message = message
        self.confirmation_property = confirmation_property
    
    def validate(self, params, entries=None):
        if params[self.property]!=params[self.confirmation_property]:
            return Error(self.property, self.message)
        return None


class EmailValidator(Validator):
    def __init__(self, property=None, message="%s is incorrect format"):
        self.property = property
        self.message = message

    def validate(self, params, entries=None):
        if not re.match("[-_.a-zA-Z0-9]+@[a-zA-Z0-9.]+\.[a-z]{2,}", params[self.property]):
            return Error(self.property, self.message)
        return None


class UniqueValidator(Validator):
    def __init__(self, property=None, model=None, model_property=None, message="%s is registered"):
        self.property = property
        self.message = message
        self.model = model
        self.model_property = model_property

    def validate(self, params, entries=None):
        key = None
        if entries:
            for entry in entries:
                if isinstance(entry, self.model):
                    key = entry.key()
                    break
        existing_entry = self.model.all().filter(self.model_property, params[self.property]).fetch(1)
        if existing_entry and (not key or (key and existing_entry.key()!=key)):
            return Error(self.property, self.message)
        return None


class Error(object):
    def __init__(self, property, message):
        self.property = property
        self.message = message
    
    def __str__(self):
        "%s %s" % (self.property. self.message)


class Form(object):
    validators = ()
    errors = None
    
    def __init__(self):
        pass
    
    def validate(self, params, entries=None):
        pass
    
    def is_valid(self, params, entries=None):
        self.errors = []
        self.validate(params)
        for validator in self.validators:
            error = validator.validate(params, entries)
            if error:
                self.errors.append(error)
        return not self.errors
