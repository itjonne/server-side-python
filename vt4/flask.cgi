#!/home/jovimajo/public_html/cgi-bin/tiea2080/venv/bin/python
# -*- coding: utf-8 -*-

import sys
from wsgiref.handlers import CGIHandler
from werkzeug.debug import DebuggedApplication

try:
  from oma import app as application

  if __name__ == '__main__':
         handler = CGIHandler()
         handler.run(DebuggedApplication(application))

except:
  print "Content-Type: text/plain;charset=UTF-8\n"
  print "Syntaksivirhe:\n"
  for err in sys.exc_info():
        print unicode(err).encode("UTF-8")