# -*- coding: utf-8 -*-
import sys
sys.path.append('./vendor')
sys.path.append('./lib')

import juno
juno.init()

from controller import session, signup, main
#from controller import message, follow
#from controller import test_user

# juno.run_with_profiler()
juno.run()
