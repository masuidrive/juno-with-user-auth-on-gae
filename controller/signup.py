# -*- coding: utf-8 -*-
from juno import *
from vendor import burns
import model

@route('/signup')
def index(web):
    return template('signup/new.html')


@route('/signup/send_confirmation_email')
def send_confirmation_email(web):
    email = web.input('email')
    errors = []
    auth = model.UserAuthentication(email = email)
    if auth.check_uniqueness():
        errors.append(webappex.ErrorMessage('email', '%s is registered' % (auth.email)))
        return template('signup/new.html')
    uce = model.UserConfirmationEmail(email)
    uce.send()
    return template('signup/sent_confirmation_email.html')


@route('/signup/confirm_email')
def confirm_email(web):
    email = web.input('email')
    key = web.input('key')
    if not model.UserConfirmationEmail(email).activation(key):
        return redirect("/signup")
    return template('signup/signup.html', {'email': web.input('email'), 'key': web.input('key')})


@route('/signup/create')
def create(web):
    email = web.input('email')
    key = web.input('key')
    if not model.UserConfirmationEmail(email).activation(key):
        return redirect("/signup")
    
    errors = []
    user = model.User(account = web.input('account'), fullname = web.input('fullname'))
    try:
        user.put()
    except burns.UniqueConstraintViolatedError, e:
        errors.append({'field':'account', 'message':'Account is registered'})
    
    if user.is_saved():
        user_authentication = model.UserAuthentication(parent = user, user = user, email = web.input('email'))
        if user_authentication.check_uniqueness():
            errors.append({'field':'Email', 'message':'%s is registered'})
        else:
            user_authentication.put()
        
        password = web.input('password')
        if password == '' or password == None:
            errors.append({'field':'password', 'message':"Required password"})
        elif password != web.input('password_confirmation'):
            errors.append({'field':'password', 'message':"Don't match password and confirmation"})
        else:
            user_authentication.update_password(password)
            user_authentication.put()
    else:
        pass
    
    """
    user_detail = model.UserDetail(parent = user, user = user)
    user_detail.put()
    """
        
    if len(errors)==0:
        template('signup/signedup.html', {'my': ''})
    else:
        template('signup/signup.html', {'email':email, 'key':key, 'errors':errors})
