"""A set of classes to add robust support for uniqueness constraints to google.appengine.ext.db.Model

Author:
  Benjamin Burns, Ocean Research & Conservation Association <http://www.teamorca.com>

Comments:
  UniqueMetaAttributer written with much help from habnabit from #python on freenode.  Thanks!!
"""

#===============================================================================
# The MIT License
# 
# Copyright (c) 2008 Benjamin Burns
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#===============================================================================

from google.appengine.ext import db
import hashlib
import sys
import exceptions

class UniqueMetaAttributer(db.PropertiedClass):
    """Metaclass to grab unique property tuples from base classes
    
    Special thanks to habnabit from #python on freenode for this.
    """
    def __init__(cls, name, bases, dict):
        """Build class w/ its own class attribute '_uniques' that joins base classes' instances of _uniques"""
        if '_uniques' in dict:
            unique = set(dict.pop('_uniques'))
            for base in bases:
                unique.update(getattr(base, '_uniques', []))
            cls._uniques = frozenset(unique)
        super(UniqueMetaAttributer,cls).__init__(name,bases,dict)

class UniqueConstraintViolatedError(exceptions.Exception):
    """Raised on put() if a uniqueness constraint defined by a tuple of properties is violated"""
    pass

class ExplicitKeyNameError(exceptions.Exception):
    """Raised if a key_name is explicitly defined in __init__ for classes in this module that disallow this."""
    pass

class UniquePropertyInstanceParent(db.Model):
    """Entities of this kind are roots for entity groups of unique property tuples
    
    Attributes:
      kind_to_check: the name of the class that extends UniqueModel to be represented by this entity
    """
    kind_to_check = db.StringProperty(required = True)
    
    def __init__(self, parent = None, key_name = None, _app = None, **kwds):
        if key_name is not None:
            raise ExplicitKeyNameError, 'key_name must be set implicitly.'
        key_name = kwds['kind_to_check']
        
        super(UniquePropertyInstanceParent, self).__init__(parent, key_name, _app, **kwds)

class UniquePropertyInstance(db.Model):    
    """Kind that represents a tuple of unique properties
    
    Attributes:
      unique_tuple: the tuple of properties represented as a string
      hash: the hash of the properties in the tuple, concatenated
      uniquable_model: instance of UniqueModel on which this tuple of properties is unique
    """
    unique_tuple = db.StringProperty(required = True)
    hash = db.StringProperty(required = True)
    unique_model = db.ReferenceProperty(collection_name='unique_property_instances', required=True)
    
    @classmethod
    def _build_key_name(cls,unique_tuple,hash):
        """Helper method to build the key name from the properties of this class"""
        return '%s:%s,%s'%(cls.__name__,unique_tuple,hash)
    
    def __init__(self, parent = None, key_name = None, _app = None, **kwds):
        if key_name is not None:
            raise ExplicitKeyNameError, 'key_name must be set implicitly.'
        key_name = self._build_key_name(kwds['unique_tuple'],kwds['hash'])
        super(UniquePropertyInstance, self).__init__(parent, key_name, _app, **kwds)
    

class UniqueModel(db.Model):
    """
    Model implementation that allows a Kind to specify tuples of unique properties.
    
    UniqueConstraintViolatedError is raised on put() in the event that a put() on this entity would violate uniqueness for this kind.
    For uniqueness to be violated for a particular tuple ALL properties of the entity being put that are contained in the tuple must
    match identically to those respective properties of an existing entity.  This is similar to a search in which the terms are ANDed
    together.  In the event that the search returns a result, UniqueConstraintViolatedError is raised.  Of course, if the search returns
    more than one result, we've really got some problems on our hands!
    
    Attributes:
      _uniques: A set of tuples that define a collection of properties to be unique. 
    """
    __metaclass__ = UniqueMetaAttributer
    _uniques = set()
    
    @classmethod
    def _constraint_tuple_as_string(cls, tuple):
        """Helper method to convert a tuple of db.Property objects to a string""" 
        s = ['(']
        for prop in tuple:
            s.append(prop.name)
            s.append(',')
        s.append(')')
        return ''.join(s)
    
    def _store_uniqueness(self, uniques_to_store):
        """Method used to store UniquePropertyInstances transactionally."""
        for unique in uniques_to_store:
            upi = UniquePropertyInstance.get_by_key_name(
                                                             key_names=UniquePropertyInstance._build_key_name(unique[0].unique_tuple,unique[0].hash),
                                                             parent=unique[0].parent()
                                                         )
            if upi == None:
                unique[0].put()
            else:
                raise UniqueConstraintViolatedError,'Unique constraint %s violated on kind %s!' % unique[1]
    
    def check_uniqueness(self):
        for ut in self.__class__._uniques:
            for property in ut:
                count = self.__class__.all().filter(('%s=' % property.name), str(getattr(self, property.name))).fetch(1)
                if count > 0:
                    return False

        return True

    def put(self):
        """Method used to store instances of UniqueModel to the datastore"""
        
        if self.is_saved(): #remove hashes in case we're updating
            instances_to_delete = []
            for upi in self.unique_property_instances:
                instances_to_delete.append(upi)
            if len(instances_to_delete)>0:
                db.run_in_transaction(self._delete_unique_instances,instances_to_delete)
        
        uniques_to_store = []
        upip = UniquePropertyInstanceParent.get_by_key_name(self.__class__.__name__)
        if upip == None:
            upip = UniquePropertyInstanceParent(
                                                kind_to_check = self.__class__.__name__
                                                )
            upip.put()
        
        key = super(UniqueModel, self).put()
        for ut in self.__class__._uniques:
            strings = []
            
            #concatenate str(property_value)
            for property in ut:
                strings.append(str(getattr(self, property.name)))
            
            #build hash from composite properties
            md5sum = hashlib.md5(''.join(strings)).hexdigest()
            uniques_to_store.append(
                                    (
                                     UniquePropertyInstance(hash=md5sum,unique_tuple=self._constraint_tuple_as_string(ut),unique_model=self,parent=upip),
                                     (self._constraint_tuple_as_string(ut),self.__class__.__name__)
                                     )
                                    )
        
        try:
            db.run_in_transaction(self._store_uniqueness, uniques_to_store)
        except UniqueConstraintViolatedError, e:
            super(UniqueModel, self).delete() #do not call UniquableModel.delete
            raise e
        
        return key
    
    def _delete_unique_instances(self, instances_to_delete):
        """Method used to delete UniquePropertyInstances from the datastore transactionally"""
        for upi in instances_to_delete:
            upi.delete()
    
    def delete(self):
        """Method used to delete instance of UniqueModel from the datastore"""
        instances_to_delete = []
        for upi in self.unique_property_instances:
            instances_to_delete.append(upi)
        db.run_in_transaction(self._delete_unique_instances,instances_to_delete)
        super(UniqueModel, self).delete()
    
