#!/usr/bin/env python
#
# Copyright 2010 Google Inc. All Rights Reserved.
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

"""A simple blog application written on Google App Engine. This renders both the
MainPage as well as the Moderation page, which will show the classification
results.
"""

__author__ = 'Robert Kaplow'

import cgi
import os
import random
import string
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
try:
  import json
except ImportError:
  from django.utils import simplejson as json

from data import DataModel, TextFile, ApiKey, getUserHash
from adm import Predict, Learn
from config import getConfig

def writeTemplate(self, name, template_values):
  path = os.path.join(os.path.dirname(__file__), name)
  self.response.out.write(template.render(path, template_values))

def onlyAdmins():
  try:
    return getConfig('admin_only')
  except:
    return False

#
# User Frontpage
#
class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if onlyAdmins():
      if users.is_current_user_admin():
        if user:
          records = DataModel().getmy()
          template_values = {'records':records,
                           'user':user
                           }
          writeTemplate(self, 'main.html', template_values)
      else:
        self.redirect(users.create_login_url('/'))  

    else:
      if user:
        records = DataModel().getmy()
      else:
        records = DataModel().getpublic()
      template_values = {'records':records,
                         'user':user
                         }
      writeTemplate(self, 'main.html', template_values)



    #  self.response.out.write('Hello World')


#
# Sign in
#
class SignIn(webapp.RequestHandler):
  def get(self):
    self.redirect(users.create_login_url('/'))    

#
# Prediction API for POST and GET
#
class Prediction(webapp.RequestHandler):
  def post(self):
    model = cgi.escape(self.request.get('model')) #key
    post = cgi.escape(self.request.get('content'))

    
   
    # Make the Google Prediction API call
    user = users.get_current_user()
    if user:
      userid, apikey = ApiKey().getbyuser()
    else:
      userid, apikey = ApiKey().getbymodel(model)

    datafile = False
    mydatamodel = DataModel().get(model)
    if mydatamodel:
      if mydatamodel.public or mydatamodel.userhash == getUserHash():
        datafile = mydatamodel.datafile
    
    addreturn = self.request.get('addreturn','')
    addjson = self.request.get('addjson','')

    if datafile and userid and post:
      #try:
      data = Predict(userid, datafile, post)
      #except:
      #  data = {'outputValue':'error'}

      
     
      if addreturn:
        try:
          if 'outputLabel' in data:
            self.response.out.write(data['outputLabel'])
          elif 'outputValue' in data:
            self.response.out.write(data['outputValue'])        
          else:
            self.response.out.write(json.dumps(data))
        except:
          self.response.out.write(json.dumps(data))   
        self.response.out.write(self.request.get('addreturn',''))
      else:
        self.response.out.write(json.dumps(data))

      if addjson:
        self.response.out.write(addjson)
    else:
      if addreturn:
        self.response.out.write( 'error'+addreturn)
      else:
        self.response.out.write( '{"error":"user, model or post were empty"}')
        

  def get(self):
    model = cgi.escape(self.request.get('model')) #key
    post = cgi.escape(self.request.get('content'))
   
    # Make the Google Prediction API call
    user = users.get_current_user()
    if user:
      userid, apikey = ApiKey().getbyuser()
    if not user or not userid:
      userid, apikey = ApiKey().getbymodel(model)

    datafile = False
    mydatamodel = DataModel().get(model)
    if mydatamodel:
      #if mydatamodel.public or mydatamodel.userhash == getUserHash(): #not required since you don't want to make a model public to access it.
      datafile = mydatamodel.datafile

    if datafile and userid and post:
      data = Predict(userid, datafile, post)          

      if 'outputLabel' in data:
        self.response.out.write(data['outputLabel'])
      elif 'outputValue' in data:
        self.response.out.write(data['outputValue'])        
      else:
        self.response.out.write(json.dumps(data))
     
    else:
      self.response.out.write('ERROR: model or content missing')

    #always print add return reference
    self.response.out.write(self.request.get('addreturn',''))      
    


#
# Learning API for GET
#
class Learning(webapp.RequestHandler):
  def get(self):
    model = cgi.escape(self.request.get('model')) #key
    post = cgi.escape(self.request.get('content'))
    answer = cgi.escape(self.request.get('answer'))
   
    # Make the Google Prediction API call
    user = users.get_current_user()
    if user:
      userid, apikey = ApiKey().getbyuser()
    if not user or not userid:
      userid, apikey = ApiKey().getbymodel(model)

    datafile = False
    mydatamodel = DataModel().get(model)
    if mydatamodel:
      #if mydatamodel.public or mydatamodel.userhash == getUserHash(): #not required since you don't want to make a model public to access it.
      datafile = mydatamodel.datafile

    if datafile and userid and post:
      model = Learn(userid, datafile, post,answer)          

      if 'trainingStatus' in model:
        self.response.out.write(model['trainingStatus'])
      elif 'kind' in model:
        self.response.out.write(model['kind'])
      else:
        self.response.out.write('ERROR: trainingStatus not found in returned model. Dump: '+json.dumps(model))
     
    else:
      self.response.out.write('ERROR: model or content missing')

    #always print add return reference
    self.response.out.write(self.request.get('addreturn',''))      

#
# upload textfile, return id
#
class Text(webapp.RequestHandler):
  def post(self):
    text = cgi.escape(self.request.get('text',''))
    if text:
      key =''
      for i in range(20): key = key + random.choice(string.letters + string.digits)
      #create file
      textfile = TextFile(key_name=key)
      textfile.id = key      
      textfile.text = ''+text
      try:
        textfile.put()
        domain = self.request.uri
        self.response.out.write(domain+'?key='+key)
      except:
         self.response.out.write('Error'+text+','+key)
    else:
      self.response.out.write('')

  def get(self):
    key = cgi.escape(self.request.get('key',''))
    if key:
      textfile = TextFile().get_by_key_name(key)
      self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
      #self.response.headers['Content-Length'] = len(textfile.text)
      self.response.out.write(textfile.text)


class Demo(webapp.RequestHandler):
  def get(self,model,title):
    template_values = {'model':model,
                       'title':title
                      }
    writeTemplate(self, 'demo.html', template_values)    


    
application = webapp.WSGIApplication([
            ('/', MainPage),
            ('/api/predict', Prediction),
            ('/api/learn', Learning),
            ('/demo/(.*)/(.*)', Demo),
            ('/text', Text),
            ('/signin', SignIn)
            ],
            debug=True)


def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
