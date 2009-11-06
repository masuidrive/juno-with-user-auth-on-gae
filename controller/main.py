# -*- coding: utf-8 -*-
import juno

@juno.route('/')
@juno.session.require_login
# @juno.session.user_current_user
def index(web):
    return 'Logged in %s<br/><a href="/logoff">Logoff</a>' % (web.current_user.account)
