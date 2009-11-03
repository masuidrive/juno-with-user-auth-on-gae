# -*- coding: utf-8 -*-
# base is http://d.hatena.ne.jp/hipuri/20091022/1256217975

from google.appengine.ext import db
from vendor import burns

# disable default validation on db.Property
setattr(db.Property, '__set__', 
        lambda self, model_instance, value: 
            setattr(model_instance, self._attr_name(), value))


class BaseModel(burns.UniqueModel):
    errors = None

    def __init__(self, *args, **kwds):
        super(BaseModel, self).__init__(*args, **kwds)
        self.errors = Errors()
    
    def validate(self):
        pass
    
    def is_valid(self):
        self.validate()
        self._check_uniqueness()
        for prop in self.properties().values():
            value = getattr(self, prop._attr_name(), None)
            try:
                value = prop.validate(value)
                setattr(self, prop._attr_name(), value)
            except db.BadValueError, e:
                self.errors.append(prop, e.message)
        return not bool(self.errors)
    
    def _check_uniqueness(self):
        for ut in self.__class__._uniques:
            for property in ut:
                count = self.__class__.all().filter(property.name, str(getattr(self, property.name))).fetch(1)
                if count and (not self.is_saved() or self.key()!=count[0].key()):
                    self.errors.append(property, '%s is not uniqueness' % property.name)
                    return False
        return True


    # add 'before_put' hook
    def put(self):
        if self.before_put():
            super(BaseModel, self).put()
    save = put

    # Hook: call before put function.
    def before_put(self):
        return True


# Container of validation error
class Error(object):
    def __init__(self, prop, message=None):
        self.prop = prop
        self.message = message

    def __str__(self):
        return self.tostr()
    
    property_name = property(lambda self: self.prop.name)    
    
    def tostr(self, format=u"[%s] %s"):
        if isinstance(self.prop, db.Property) and format:
            return format % (self.prop.verbose_name
                        or self.prop.name, self.message)
        else:
            return self.message

# Container of errors
class Errors(list):
    def __init__(self):
        self.map = dict()

    def append(self, prop, msg=None, error=True):
        if error:
            if isinstance(prop, db.Property):
                super(Errors, self).append(Error(prop, msg))
                self.map[prop.name] = len(self) - 1
            elif isinstance(prop, (str, unicode)):
                super(Errors, self).append(Error(prop, msg))
                self.map[prop] = len(self) - 1
            else:
                super(Errors, self).append(Error(None, prop))

    def clear(self):
        del self[:]
    
    def get(self, name, default=None):
        return self[index] if name in self else default

    def tostr(self, sep=u"\n", **ops):
        msgs=list()
        for error in self:
            msgs.append(error.tostr(**ops))
        return sep.join(msgs)

    def __str__(self):
        return self.tostr()

    def __contains__(self, name):
        return name in self.map
    
    def __getitem__(self, index):
        if isinstance(index, (str, unicode)):
            if index not in self.map:
                raise IndexError(u"'%s' property has not error." % name)
            index = self.map[index]
        return super(Errors, self).__getitem__(index)
