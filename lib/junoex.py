from juno import *
import model

def require_login(func):
    def innerFunc(web):
        if web.session and web.session.has_key('user') and web.session['user']:
            web.current_user = model.User.get(web.session['user'])
        if web.current_user:
            return func(web)
        else:
            return redirect("/login")
    return innerFunc
