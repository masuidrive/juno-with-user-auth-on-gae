Juno with user authentication on Google App Engine
====
* Homepage: [http://github.com/masuidrive/juno-with-user-auth-on-gae][homepage]
* Repository: [http://github.com/masuidrive/juno-with-user-auth-on-gae][repo]


Features
--------
* User authentication without Google Account.


Included
--------
* [Juno-GAE][juno-gae]
* [Jinja2][jinja2]
* [Beaker][beaker]


Example
--------

Require login:

    from junoex import *
    
    @route('/')
    @require_login
    def index(web):
        return 'Logged in %s<br/>' % (web.current_user.account)
    
    run()


License
--------
MIT License

[homepage]:   http://github.com/masuidrive/juno-with-user-auth-on-gae
[repo]:       http://github.com/masuidrive/juno-with-user-auth-on-gae
[juno-gae]:   http://github.com/justinjas/juno-gae
[jinja2]:     http://jinja.pocoo.org/2/
[beaker]:     http://wiki.pylonshq.com/display/beaker/Home
