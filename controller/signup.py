# -*- coding: utf-8 -*-
from google.appengine.ext import db

from juno import *
import model

@route('/signup')
def index(web):
    return template('signup/new.html')


@route('/signup/send_confirmation_email')
def send_confirmation_email(web):
    email = web.input('email')
    errors = []
    auth = model.UserAuthentication(email=email)
    if model.UserAuthentication.email_is_registered(email):
        errors.append({'property_name':'email', 'message':'Email is registered'})
        return template('signup/new.html', {'email':email, 'errors':errors})
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
    account = web.input('account')
    fullname = web.input('fullname')
    user = model.User(account=account, fullname=account)
    if not user.is_valid():
        errors.extend(user.errors)
    auth =  model.UserAuthentication(email=email)
    if not auth.is_valid():
        errors.extend(auth.errors)

    # check password and confirmation
    password = web.input('password')
    if password == '' or password == None:
        errors.append({'property_name':'password', 'message':"password is required"})
    elif password != web.input('password_confirmation'):
        errors.append({'property_name':'password', 'message':"password doesn't match password and confirmation"})
    
    if errors:
        return template('signup/signup.html', {'email':email, 'key':key, 'email':email, 'fullname':fullname, 'account':account ,'errors':errors})
    else:
        user = model.User.signup({'email':email, 'account':account, 'password':password, 'fullname':fullname})
        web.session['user'] = user.key()
        web.session.save()
        return template('signup/signedup.html')
