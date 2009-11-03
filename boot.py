# -*- coding: utf-8 -*-
import sys
sys.path.append('./vendor')
sys.path.append('./lib')

import gae_util
from junoex import *
init({'raise_view_exceptions': gae_util.is_development_env(),
      'template_root': 'templates',
      'use_sessions': True,
      'use_db': False,
      })

import model
model.UserConfirmationEmail.load_settings('user-auth.yaml')

from controller import session, signup, main

run()
