# http://github.com/justinjas/juno-gae

# Built in library imports
import mimetypes
import re
import os
import sys
# Server imports
import urlparse
import cgi
import logging

class Juno(object):
    def __init__(self, configuration=None):
        """Takes an optional configuration dictionary. """
        global _hub
        if _hub is not None:
            logging.error('Warning: there is already a Juno object created you might get some weird behavior.')
        else: _hub = self
        self.routes = []
        # Set options and merge in user-set options
        self.config = {
                # General settings / meta information
                'log':    True,
                'routes': self.routes,
                'self':   self,
                # Types and encodings
                'charset':      'utf-8',
                'content_type': 'text/html',
                # Server options
                'mode':     'appengine',
                'scgi_port': 8000,
                'fcgi_port': 8000,
                'dev_port':  8000,
                # Template options
                'use_templates':           True,
                'template_lib':            'jinja2',
                'get_template_handler':    _get_template_handler,
                'render_template_handler': _render_template_handler,
                'auto_reload_templates':   True,
                'translations':            [], 
                'template_kwargs':         {},
                'template_root':           os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates/'),
                '404_template':            '404.html',
                '500_template':            '500.html',
                # Database options
                'use_db':      True,
                # Session options
                'use_sessions': False,
                'session_lib':  'beaker',
                # Debugger
                'use_debugger': False,
                'raise_view_exceptions': False,
                # Custom middleware
                'middleware': []
        }
        if configuration is not None: self.config.update(configuration)
        # Set up templating
        if self.config['use_templates']: 
            self.setup_templates()
        # Set up the database 
        if self.config['use_db']:
            self.setup_database()

    def setup_templates(self):
        if self.config['template_lib'] == 'jinja2':
            import jinja2
            # If the user specified translation objects, load i18n extension
            if len(self.config['translations']) != 0:
                extensions = ['jinja2.ext.i18n']
            else:
                extensions = ()
            self.config['template_env'] = jinja2.Environment(
                loader      = jinja2.FileSystemLoader(
                                searchpath = self.config['template_root'],
                                encoding   = self.config['charset'],
                              ),
                auto_reload = self.config['auto_reload_templates'],
                extensions = extensions,
                **self.config['template_kwargs']
            )
            for translation in self.config['translations']:
                self.config['template_env'].install_gettext_translations(translation)
        if self.config['template_lib'] == 'mako':
            import mako.lookup
            self.config['template_env'] = mako.lookup.TemplateLookup(
                directories       = [self.config['template_root']],
                input_encoding    = self.config['charset'],
                output_encoding   = self.config['charset'],
                filesystem_checks = self.config['auto_reload_templates'],
                **self.config['template_kwargs']
            )

    def setup_database(self):
        # DB library imports
        from google.appengine.ext import db

    def run(self):
        run_appengine(self.request)

    def request(self, request, method='*', **kwargs):
        """Called when a request is received.  Routes a url to its view.
        Returns a 3-tuple (status_string, headers, body) from 
        JunoResponse.render()."""
        if config('log'): logging.info('%s request for %s...' %(method, request))
        req_obj = JunoRequest(kwargs)
        # Set the global response object in case the view wants to use it
        global _response
        _response = JunoResponse()
        # Add a slash if there isn't one - avoids frustrating matching bugs
        if request[-1] != '/': request += '/'
        for route in self.routes:
            if not route.match(request, method): continue
            if config('log'): logging.info('%s matches, calling %s()...\n' %(
                route.old_url, route.func.__name__))
            # Get the return from the view    
            if config('raise_view_exceptions') or config('use_debugger'):
                response = route.dispatch(req_obj)
            else:
                try:
                    response = route.dispatch(req_obj)
                except:
                    return servererror(error=cgi.escape(str(sys.exc_info()))).render()
            # If nothing returned, use the global object
            if response is None: response = _response
            # If we don't have a string, render the Response to one
            if isinstance(response, JunoResponse):
                return response.render()
            return JunoResponse(body=response).render()
        # No matches - 404
        return notfound(error='No matching routes registered').render()

    def route(self, url, func, method):
        """Attaches a view to a url or list of urls, for a given function. """
        # An implicit route - the url is just the function name
        if url is None: url = '/' + func.__name__ + '/'
        # If we just have one url, add it
        if type(url) == str: self.routes.append(JunoRoute(url, func, method))
        # Otherwise add each url in the list
        else:
            for u in url: self.routes.append(JunoRoute(u, func, method)) 

    def __getattr__(self, attr):
        if attr in self.config.keys():
            return self.config[attr]
        return None

    def __repr__(self): return '<Juno>'

class JunoRoute(object):
    """Uses a simplified regex to grab url parts:
    i.e., '/hello/*:name/' compiles to '^/hello/(?P<name>\w+)/' """
    def __init__(self, url, func, method):
        # Make sure the url begins and ends in a '/'
        if url[0] != '/': url = '/' + url
        if url[-1] != '/': url += '/'
        # Store the old one before we modify it (we use it for __repr__)
        self.old_url = url
        # RE to match the splat format
        splat_re = re.compile('^\*?:(?P<var>\w+)$')
        # Start building our modified url
        buffer = '^'
        for part in url.split('/'):
            # Beginning and end entries are empty, so skip them
            if not part: continue
            match_obj = splat_re.match(part)
            # If it doesn't match, just add it without modification
            if match_obj is None: buffer += '/' + part
            # Otherwise replace it with python's regex format
            else: buffer += '/(?P<' + match_obj.group('var') + '>.*)'
        # If we don't end with a wildcard, add a end of line modifier    
        if buffer[-1] != ')': buffer += '/$'
        else: buffer += '/'
        self.url = re.compile(buffer)
        self.func = func
        self.method = method.upper()
        self.params = {}

    def match(self, request, method):
        """Matches a request uri to this url object. """
        match_obj = self.url.match(request)
        if match_obj is None: return False
        # Make sure the request method matches
        if self.method != '*' and self.method != method: return False
        # Store the parts that matched
        self.params.update(match_obj.groupdict())
        return True

    def dispatch(self, req):
        """Calls the route's view with any named parameters."""
        return self.func(req, **self.params)

    def __repr__(self):
        return '<JunoRoute: %s %s - %s()>' %(self.method, self.old_url, 
                                             self.func.__name__)

class JunoRequest(object):
    """Offers following members:
        raw           => the header dict used to construct the JunoRequest
        location      => uri being requested, without query string ('/' from '/?a=6')
        full_location => uri with query string ('/?a=6' from '/?a=6')
        user_agent    => the user agent string of requester
    """
    def __init__(self, request):
        # Make sure we have a request uri, and it ends in '/'
        if request['PATH_INFO'][-1] != '/': request['PATH_INFO'] += '/'
        # Set some instance variables
        self.raw = request
        self.raw['input'] = {}
        self.location = request['PATH_INFO']
        # If we get a REQUEST_URI, store it.  Otherwise copy PATH_INFO
        if 'REQUEST_URI' in request:
            self.full_location = request['REQUEST_URI']
        else: self.full_location = self.location
        # Find the right user agent header
        if 'HTTP_USER_AGENT' in request: 
            self.user_agent = request['HTTP_USER_AGENT']
        elif 'User-Agent' in request: 
            self.user_agent = request['User-Agent']
        else: self.user_agent = ''
        self.combine_request_dicts()
        # Check for sessions
        if config('use_sessions') and config('session_lib') == 'beaker':
            self.session = request['beaker.session']

    def combine_request_dicts(self):
        input_dict = self.raw['QUERY_DICT'].copy()
        for k, v in self.raw['POST_DICT'].items():
            # Combine repeated keys
            if k in input_dict.keys(): input_dict[k].extend(v)
            # Otherwise just add this key
            else: input_dict[k] = v
        # Reduce the dict - change one item lists ([a] to a)
        for k, v in input_dict.items(): 
            if len(v) == 1: input_dict[k] = v[0]
        self.raw['input'] = input_dict

    def __getattr__(self, attr):
        # Try returning values from self.raw
        if attr in self.keys(): return self.raw[attr]
        if attr == 'session' and config('log'):
             logging.error("Error: To use sessions, enable 'use_sessions' when calling juno.init()")
        return None

    def input(self, arg=None):
        # No args: return the whole dictionary
        if arg is None: return self.raw['input']
        # Otherwise try to return the value for that key
        if self.raw['input'].has_key(arg): 
            return self.raw['input'][arg]
        return None

    # Make JunoRequest act as a dictionary for self.raw
    def __getitem__(self, key): return self.raw[key]
    def __setitem__(self, key, val): self.raw[key] = val
    def keys(self): return self.raw.keys()
    def items(self): return self.raw.items()
    def values(self): return self.raw.values()
    def __len__(self): return len(self.raw)
    def __contains__(self, key): return key in self.raw

    def __repr__(self):
        return '<JunoRequest: %s>' %self.location

class JunoResponse(object):
    status_codes = {
        200: 'OK',
        301: 'Moved Permanently',
        302: 'Found',
        303: 'See Other',
        304: 'Not Modified',
        400: 'Bad Request',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        410: 'Gone',
        500: 'Internal Server Error',
    }
    def __init__(self, configuration=None, **kwargs):
        # Set options and merge in user-set options
        self.config = {
            'body': '',
            'status': 200,
            'headers': { 'Content-Type': config('content_type'), },
        }
        if configuration is None: configuration = {}
        self.config.update(configuration)
        self.config.update(kwargs)
        self.config['headers']['Content-Length'] = len(self.config['body'])
    
    # Add text and adjust content-length
    def append(self, text):
        self.config['body'] += str(text)
        self.config['headers']['Content-Length'] = len(self.config['body'])
        return self
 
    # Implement +=
    def __iadd__(self, text):
        return self.append(text)

    def render(self):
        """Returns a 3-tuple (status_string, headers, body)."""
        status_string = '%s %s' %(self.config['status'],
                                  self.status_codes[self.config['status']])
        headers = [(k, str(v)) for k, v in self.config['headers'].items()]
        body = '%s' %self.config['body']
        return (status_string, headers, body)

    # Set a header value
    def header(self, header, value):
        self.config['headers'][header] = value
        return self
 
    # Modify the headers dictionary when the response is treated like a dict
    def __setitem__(self, header, value): self.header(header, value)
    def __getitem__(self, header): return self.config['headers'][header]

    def __getattr__(self, attr):
        return self.config[attr]

    def __repr__(self):
        return '<JunoResponse: %s %s>' %(self.status, self.status_codes[self.status])

#
#   Functions to deal with the global Juno object (_hub)
#

_hub = None

def init(configuration=None):
    """Set up Juno with an optional configuration."""
    # Only set it up if we haven't already. (Avoids multiple Juno objects)
    global _hub # Use global keyword here to avoid SyntaxWarning
    if _hub is None:
        _hub = Juno(configuration)
    return _hub

def config(key, value=None):
    """Get or set configuration options."""
    if _hub is None: init()
    if value is None:
        # Either pass a configuration dictionary
        if type(key) == dict: _hub.config.update(key)
        # Or retrieve a value
        else: 
            if key in _hub.config.keys(): 
                return _hub.config[key]
            return None
    # Or set a specific value
    else: _hub.config[key] = value

def run():
    """Start Juno"""
    if _hub is None: init()
    return _hub.run()

#
#   Decorators to add routes based on request methods
#

def route(url=None, method='*'):
    if _hub is None: init()
    def wrap(f): _hub.route(url, f, method)
    return wrap

def post(url=None):   return route(url, 'post')
def get(url=None):    return route(url, 'get')
def head(url=None):   return route(url, 'head')
def put(url=None):    return route(url, 'put')
def delete(url=None): return route(url, 'delete')

#
#   Functions to deal with the global response object (_response)
#

_response = None

def append(body):
    """Add text to response body. """
    global _response
    return _response.append(body)

def header(key, value):
    """Set a response header. """
    global _response
    return _response.header(key, value)

def content_type(type):
    """Set the content type header. """
    header('Content-Type', type)

def status(code):
    _response.config['status'] = code

#
#   Convenience functions for 404s and redirects
#

def redirect(url, code=302):
    status(code)
    # clear the response headers and add the location header
    _response.config['headers'] = { 'Location': url }
    return _response

def assign(from_, to):
    if type(from_) not in (list, tuple): from_ = [from_]
    for url in from_:
        @route(url)
        def temp(web): redirect(to)

def notfound(error='Unspecified error', file=None):
    """Sets the response to a 404, sets the body to 404_template."""
    if config('log'):  logging.error('Not Found: %s' % error);
    status(404)
    if file is None: file = config('404_template')
    return template(file, error=error)

def servererror(error='Unspecified error', file=None):
    """Sets the response to a 500, sets the body to 500_template."""
    if config('log'): logging.error('Error: (%s, %s, %s)' % sys.exc_info())
    status(500)
    if file is None: file = config('500_template')
    # Resets the response, in case the error occurred as we added data to it
    _response.config['body'] = ''
    return template(file, error=error)

#
#   Serve static files.
#

def static_serve(web, file):
    """The default static file serve function. Maps arguments to dir structure."""
    file = os.path.join(config('static_root'), file)
    realfile = os.path.realpath(file)
    if not realfile.startswith(os.path.realpath(config('static_root'))):
        notfound("that file could not be found/served")
    elif yield_file(file) != 7:
        notfound("that file could not be found/served")

def yield_file(filename, type=None):
    """Append the content of a file to the response. Guesses file type if not
    included.  Returns 1 if requested file can't be accessed (often means doesn't 
    exist).  Returns 2 if requested file is a directory.  Returns 7 on success. """
    if not os.access(filename, os.F_OK): return 1
    if os.path.isdir(filename): return 2
    if type is None:
        guess = mimetypes.guess_type(filename)[0]
        if guess is None: content_type('text/plain')
        else: content_type(guess)
    else: content_type(type)
    append(open(filename, 'r').read())
    return 7

#
#   Templating
#

def template(template_path, template_dict=None, **kwargs):
    """Append a rendered template to response.  If template_dict is provided,
    it is passed to the render function.  If not, kwargs is."""
    # Retreive a template object.
    t = get_template(template_path)
    # Render it without arguments.
    if not kwargs and not template_dict: 
        return append(render_template(t))
    # Render the template with a provided template dictionary
    if template_dict: 
        return append(render_template(t, **template_dict))
    # Render the template with **kwargs
    return append(render_template(t, **kwargs))

def get_template(template_path):
    """Returns a template object by calling the default value of
    'get_template_handler'.  Allows getting a template to be the same
    regardless of template library."""
    return config('get_template_handler')(template_path)

# The default value of config('get_template_handler')
def _get_template_handler(template_path):
    """Return a template object.  This is defined for the Jinja2 and
    Mako libraries, otherwise you have to override it.  Takes one 
    parameter: a string containing the desired template path.  Needs
    to return an object that will be passed to your rendering function."""
    return config('template_env').get_template(template_path)

def render_template(template_obj, **kwargs):
    """Renders a template object by using the default value of
    'render_template_handler'.  Allows rendering a template to be consistent
    regardless of template library."""
    return config('render_template_handler')(template_obj, **kwargs)

# The default value of config('render_template_handler')
def _render_template_handler(template_obj, **kwargs):
    """Renders template object with an optional dictionary of values.
    Defined for Jinja2 and Mako - override it if you use another
    library.  Takes a template object as the first parameter, with an
    optional **kwargs parameter.  Needs to return a string."""
    if config('template_lib') == 'mako': return template_obj.render(**kwargs)
    if config('template_lib') == 'jinja2':
        # Jinja needs its output encoded here
        return template_obj.render(**kwargs).encode(config('charset'))

def autotemplate(urls, template_path):
    """Automatically renders a template for a given path.  Currently can't
    use any arguments in the url."""
    if type(urls) not in (list, tuple): urls = urls[urls]
    for url in urls:
        @route(url)
        def temp(web): template(template_path)

####
#   Juno's Servers - Development (using WSGI), and SCGI (using Flup)
####

def get_application(process_func):
    def application(environ, start_response):
        # This may be temporary - I was getting weird errors where
        # the `environ` was None.  Seems to have stopped, but I don't
        # know why.  This message was to clarify what happened.
        if environ is None:
            logging.error('Error: environ is None for some reason. Error: environ=%s' %environ)
            sys.exit()
        # Ensure some variable exist (WSGI doesn't guarantee them)
        if 'PATH_INFO' not in environ.keys() or not environ['PATH_INFO']: 
            environ['PATH_INFO'] = '/'
        if 'QUERY_STRING' not in environ.keys():
            environ['QUERY_STRING'] = ''
        if 'CONTENT_LENGTH' not in environ.keys() or not environ['CONTENT_LENGTH']:
            environ['CONTENT_LENGTH'] = '0'
        # Standardize some header names
        environ['DOCUMENT_URI'] = environ['PATH_INFO']
        if environ['QUERY_STRING']:
            environ['REQUEST_URI'] = environ['PATH_INFO']+'?'+environ['QUERY_STRING']
        else:
            environ['REQUEST_URI'] = environ['DOCUMENT_URI']
        # Parse query string arguments
        environ['QUERY_DICT'] = cgi.parse_qs(environ['QUERY_STRING'],
                                             keep_blank_values=1)
        if environ['REQUEST_METHOD'] in ('POST', 'PUT'):
            fs = cgi.FieldStorage(fp=environ['wsgi.input'],
                                  environ=environ,
                                  keep_blank_values=True)
            
            post_dict = {}
            if fs.list:
                for field in fs.list:
                    if field.filename:
                        value = field
                    else:
                        value = field.value
                    
                    # Each element of post_dict will be a list, even if it contains only
                    # one item. This is in line with QUERY_DICT which also works like this.
                    if not field.name in post_dict:
                        post_dict[field.name] = [value]
                    else:
                        post_dict[field.name].append(value)
            
            environ['POST_DICT'] = post_dict
        else: environ['POST_DICT'] = {}
        # Done parsing inputs, now ready to send to Juno
        status_str, headers, body = process_func(environ['PATH_INFO'],
                                                 environ['REQUEST_METHOD'],
                                                 **environ)
        start_response(status_str, headers)
        return [body]

    middleware_list = []
    if config('use_debugger'):
        middleware_list.append(('werkzeug.DebuggedApplication', {'evalex': True}))
    if config('use_sessions') and config('session_lib') == 'beaker':
        middleware_list.append(('beaker.middleware.SessionMiddleware', {}))
    middleware_list.extend(config('middleware'))
    application = _load_middleware(application, middleware_list)

    return application

def _load_middleware(application, middleware_list):
    for middleware, args in middleware_list:
        parts = middleware.split('.')
        module = '.'.join(parts[:-1])
        name = parts[-1]
        try:
            obj = getattr(__import__(module, None, None, [name]), name)
            application = obj(application, **args)
        except (ImportError, AttributeError):
            logging.warning('failed to load middleware %s' % name)
    return application

def run_appengine(process_func):
    #sys.stdout = sys.stderr
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(get_application(process_func))
