# -*- coding: utf-8 -*-
from google.appengine.ext import db

from juno import *
import model
import form


class SignupEmailForm(form.Form):
    validators = (
        form.EmailValidator(property="email",
                            message="Email incorrect format"),
        form.UniqueValidator(property="email",
                             model=model.UserAuthentication,
                             model_property="email",
                             message="Email is registered"),
        )
    
    def validate(self, web, entries=None):
        """ custom validator """
        pass


class SignupForm(form.Form):
    validators = (
        form.EmailValidator(property="email",
                            message="Email incorrect format"),
        form.UniqueValidator(property="email",
                             model=model.UserAuthentication,
                             model_property="email",
                             message="Email is registered"),
        form.UniqueValidator(property="account",
                             model=model.User,
                             model_property="account",
                             message="Account is registered"),
        form.RequiredValidator(property="fullname"),
        form.ConfirmedValidator(property="password",
                                confirmation_property="password_confirmation",
                                message="Password isn't match"),
        form.RegexpValidator(property="password",
                             regexp=".{4,}",
                             message="Password is over 4 chars"),
        )
    
    def validate(self, web, entries=None):
        """ custom validator """
        pass


def verify_email_key(web):
    if not model.UserConfirmationEmail(web.input('email')).activate(web.input('key')):
        redirect("/signup")
        return False
    return True


@get('/signup')
def index(web):
    return template('signup/new.html', {'web':web})


@post('/signup/send_confirmation_email')
def send_confirmation_email(web):
    f = SignupEmailForm()
    if not f.is_valid(web):
        return template('signup/new.html', {'web':web, 'errors':f.errors})
    uce = model.UserConfirmationEmail(web.input('email'))
    uce.send()
    return template('signup/sent_confirmation_email.html', {'web':web})


@get('/signup/confirm_email')
def confirm_email(web):
    if not verify_email_key(web):
        return
    return template('signup/signup.html', {'web':web})


@post('/signup/create')
def create(web):
    if not verify_email_key(web):
        return
    
    f = SignupForm()
    if not f.is_valid(web):
        return template('signup/signup.html', {'web':web, 'errors':f.errors})
    
    user = auth = None
    try:
        user = model.User(
            account=web.input('account'),
            fullname=web.input('fullname')
            )
        user.put()
        salt = model.UserAuthentication.generate_salt()
        auth = model.UserAuthentication(
            user=user,
            email=web.input('email'),
            salt=salt,
            crypted_password=model.UserAuthentication.crypt_password(web.input('password'), salt),
            )
        auth.put()
    except Exception, e:
        user and user.delete()
        auth and auth.delete()
        raise e
    
    return template('signup/signedup.html', {'web':web})

