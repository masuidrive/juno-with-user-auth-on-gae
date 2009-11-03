# -*- coding: utf-8 -*-
from juno import *
import model

@get('/login')
def login_form(web):
    incorrent_login = False
    login = web.input('login')
    return template('session/new.html', {"login":login, "incorrent_login":False})

@post('/login')
def login_form(web):
    login = web.input('login')
    user = model.user.User.authenticate(login, web.input('password'))
    if user:
        web.session['user'] = user.key()
        web.session.save()
        return redirect('/')
    else:
        return template('session/new.html', {"login":login, "incorrent_login":True})

@route('/logoff')
def logoff(web):
    web.session['user'] = None
    web.session.save()
    return redirect('/')
