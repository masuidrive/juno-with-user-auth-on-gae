# -*- coding: utf-8 -*-
import re
import yaml
from juno_original import *
from jinja2 import environmentfilter, Markup

import gae_util

original_init = init
def init(configuration=None):
    if not configuration:
        configuration = {
            'raise_view_exceptions': gae_util.is_development(),
            'template_root': 'templates',
            'use_db': False,
            }
    original_init(configuration)
    
    """ extend template filter example code
    _re_account = re.compile(r'@([a-zA-Z0-9]{3,})')
    @environmentfilter
    def do_autolink(environment, value):
        escaped_value = unicode(Markup.escape(value))
        return re.sub(_re_account, '@<a href="/u/\\1">\\1</a>', escaped_value)
    config('template_env').filters['autolink'] = do_autolink
    """

_site_config = None
def site_config(key):
    global _site_config
    if not _site_config:
        env = 'production'
        if gae_util.is_development():
            env = 'development'
        string = open('config.yaml').read().decode('utf8')
        _site_config = yaml.load(string)[env]
    if _site_config.has_key(key):
        return _site_config[key]
    else:
        return None

def run_with_profiler():
    # This is the main function for profiling 
    import cProfile, pstats
    prof = cProfile.Profile()
    prof = prof.runctx("run()", globals(), locals())
    print "<pre>"
    stats = pstats.Stats(prof)
    stats.sort_stats("time")  # Or cumulative
    stats.print_stats(80)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    print "</pre>"
