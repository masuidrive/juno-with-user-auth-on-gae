#from juno import *
from junoex import *

@route('/')
@require_login
def index(web):
    return 'Logged in %s<br/><a href="/logoff">Logoff</a>' % (web.current_user.account)

