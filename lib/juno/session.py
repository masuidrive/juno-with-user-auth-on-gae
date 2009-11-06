# -*- coding: utf-8 -*-
import re
import Cookie
import hashlib
import juno
import model.user


def _get_current_user(web):
    web.current_user = None
    try:
        cookie = Cookie.SimpleCookie(web.raw['HTTP_COOKIE'])
        config = juno.site_config('session')
        if cookie.has_key(config['cookie']) and config['cookie']:
            (hash, key) = cookie[config['cookie']].value.split(':',2)
            if hashlib.sha1(key+config['salt']).hexdigest()==hash:
                web.current_user = model.user.User.get(key)
            else:
                clear()
    except:
        clear()

def require_login(func):
    def innerFunc(web, **kw):
        _get_current_user(web)
        if web.current_user:
            return func(web, **kw)
        else:
            return juno.redirect("/login")
    return innerFunc

def use_current_user(func):
    def innerFunc(web, **kw):
        _get_current_user(web)
        return func(web, **kw)
    return innerFunc

def set_user(user):
    cookie = Cookie.SimpleCookie()
    key = str(user.key())
    hash = hashlib.sha1(key+juno.site_config('session')['salt']).hexdigest()
    cookie[juno.site_config('session')['cookie']] = '%s:%s' % (hash, key)
    juno.header('Set-Cookie', cookie.output(header=''))

def clear():
    cookie = Cookie.SimpleCookie()
    cookie[juno.site_config('session')['cookie']] = ""
    juno.header('Set-Cookie', cookie.output(header=''))
