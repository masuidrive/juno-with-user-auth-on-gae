# -*- coding: utf-8 -*-
import juno.session
import model.user


@juno.get('/login')
def login_form(web):
    incorrent_login = False
    login = web.input('login')
    return juno.template('session/new.html', {"web":web or "", "incorrent_login":False})


@juno.post('/login')
def login_form(web):
    user = model.user.User.authenticate(web.input('login'), web.input('password'))
    if user:
        juno.session.set_user(user)
        return juno.redirect('/')
    else:
        return juno.template('session/new.html', {"web":web, "incorrent_login":True})


@juno.route('/logoff')
def logoff(web):
    juno.session.clear()
    return juno.redirect('/')
