#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.api import namespace_manager
from config import getConfig

import os
import cgi
import string

try:
  import json
except ImportError:
  from django.utils import simplejson as json

#
# Help Functions
#
def helpWrite(self,text):
    self.response.out.write(text)

def helpTemplate(self, name, template_values):
  path = os.path.join(os.path.dirname(__file__), name)
  self.response.out.write(template.render(path, template_values))

def helpStrFilter(str):
    set = 'abcdefghijklmnopqrstuvwxyz0123456789-_'
    return ''.join([c for c in str.lower() if c in set])

def helpClearName(str):
    return helpStrFilter(str.lower().replace(' ','_'))

#
#-------------------------------------------------------------------------------
#





#
# WebData
#
class WebData(db.Model):
  group = db.StringProperty()
  name = db.StringProperty()
  value = db.TextProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)





#
# returns and puts name/value pairs
#
class webstore(webapp.RequestHandler):
    def get(self,project, group, name):
      if getConfig('webstore'):      
        if self.request.get('data'):
          self.post(project, group, name)
        else:
          self.response.headers["Access-Control-Allow-Origin"] = "*"
          namespace_manager.set_namespace(project)
          webdata = WebData.get_by_key_name(group+'/'+name)
          if webdata:
            helpWrite(self,webdata.value)
          else:
            helpWrite(self,'-1 data not found')
      else:
        helpWrite(self,'-1 webstore service not activated')
            

    def post(self,project, group, name):
      self.response.headers["Access-Control-Allow-Origin"] = "*"
      newvalue = self.request.get('data')
      if getConfig('webstore'):
        if newvalue:
          namespace_manager.set_namespace(project)
          webdata = WebData.get_by_key_name(group+'/'+name)
          if webdata:
            webdata.value = newvalue
            webdata.put()
            helpWrite(self,'0 saved')
          else:
            webdata = WebData(key_name=group+'/'+name)
            webdata.group = group
            webdata.name = name
            webdata.value = newvalue
            webdata.put()
            helpWrite(self,'0 saved')
        else:
          helpWrite(self,'-1 data parameter missing')
      else:
        helpWrite(self,'-1 webstore service not activated')
                  

#
# returns all values for group
#
class webstores(webapp.RequestHandler):
    def get(self,project, group):
      self.response.headers["Access-Control-Allow-Origin"] = "*"
      namespace_manager.set_namespace(project)
      
      webdatas = WebData.all()
      webdatas.filter("group =",group)
      if getConfig('webstore'):
        if webdatas:
          values = []
          for data in webdatas:
            values.append({'name':data.name, 'value':data.value})
            
          values = json.dumps({'values':values})
          
          helpWrite(self,values)
        else:
          helpWrite(self,'-1 data not found for group' + group)
      else:
        helpWrite(self,'-1 webstore service not activated')
        

#
#-------------------------------------------------------------------------------
#

#
# Main Handler
#
def main():
    application = webapp.WSGIApplication([
               ('/webstore/(.*)/(.*)/(.*)', webstore),
               ('/webstore/(.*)/(.*)',webstores)               

               
               ],debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
