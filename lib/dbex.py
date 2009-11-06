from google.appengine.ext import db
import burns

class BaseModel(burns.UniqueModel):
    def __eq__(self, other):
        return self.key()==other.key()
    
    def __hash__(self):
        return self.key().__hash__()

    def get_key(self, prop_name):
        return getattr(self.__class__, prop_name).get_value_for_datastore(self)
