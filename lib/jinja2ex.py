import re
from jinja2 import environmentfilter, Markup

_re_account = re.compile(r'@([a-zA-Z0-9]{3,})')

def addfilters(juno):
    @environmentfilter
    def do_autolink(environment, value):
        escaped_value = unicode(Markup.escape(value))
        return re.sub(_re_account, '@<a href="/u/\\1">\\1</a>', escaped_value)
    juno.config['template_env'].filters['autolink'] = do_autolink
