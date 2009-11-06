# -*- coding: utf-8 -*-
from google.appengine.ext import db

import juno
import model.user
import form


class SignupEmailForm(form.Form):
    validators = (
        form.EmailValidator(property="email",
                            message="Email incorrect format"),
        form.UniqueValidator(property="email",
                             model=model.user.UserAuthentication,
                             model_property="email",
                             message="Email is registered"),
        )
    
    def validate(self, params, entries=None):
        """ custom validator """
        pass


class SignupForm(form.Form):
    validators = (
        form.EmailValidator(property="email",
                            message="Email incorrect format"),
        form.UniqueValidator(property="email",
                             model=model.user.UserAuthentication,
                             model_property="email",
                             message="Email is registered"),
        form.UniqueValidator(property="account",
                             model=model.user.User,
                             model_property="account",
                             message="Account is registered"),
        form.RegexpValidator(property="password",
                             regexp="[a-zA-Z0-9]{3,}",
                             message="Account is only alphabets and numbers"),
        form.RequiredValidator(property="fullname"),
        form.ConfirmedValidator(property="password",
                                confirmation_property="password_confirmation",
                                message="Password isn't match"),
        form.RegexpValidator(property="password",
                             regexp=".{4,}",
                             message="Password is over 4 chars"),
        )
    
    def validate(self, params, entries=None):
        """ custom validator """
        pass


def verify_email_key(web):
    if not model.user.UserConfirmationEmail(web.input('email')).activate(web.input('key')):
        juno.redirect("/signup")
        return False
    return True


@juno.get('/signup')
def index(web):
    return juno.template('signup/new.html', {'web':web})


@juno.post('/signup/send_confirmation_email')
def send_confirmation_email(web):
    f = SignupEmailForm()
    if not f.is_valid(web.input()):
        return juno.template('signup/new.html', {'web':web, 'errors':f.errors})
    uce = model.user.UserConfirmationEmail(web.input('email'))
    uce.send()
    return juno.template('signup/sent_confirmation_email.html', {'web':web})


@juno.get('/signup/confirm_email')
def confirm_email(web):
    if not verify_email_key(web):
        return
    return juno.template('signup/signup.html', {'web':web})


@juno.post('/signup/create')
def create(web):
    if not verify_email_key(web):
        return
    
    f = SignupForm()
    if not f.is_valid(web.input()):
        return juno.template('signup/signup.html', {'web':web, 'errors':f.errors})
    
    user = auth = None
    try:
        user = model.user.User(
            account=web.input('account'),
            fullname=web.input('fullname')
            )
        user.put()
        salt = model.user.UserAuthentication.generate_salt()
        auth = model.user.UserAuthentication(
            user=user,
            email=web.input('email'),
            salt=salt,
            crypted_password=model.user.UserAuthentication.crypt_password(web.input('password'), salt),
            )
        auth.put()
        juno.session.set_user(user)
    except Exception, e:
        user and user.is_saved() and user.delete()
        auth and auth.is_saved() and auth.delete()
        if not isinstance(e, not DuplicatePropertyError):
            raise e
    
    return juno.template('signup/signedup.html', {'web':web})

