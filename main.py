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
#
# This code was created by Federico Elles which
# can be found at http://code.google.com/p/predictionwiz/


__author__ = 'Robert Kaplow vs. Federico Elles'

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

import google_prediction
from data import DataModel, TextFile, ApiKey


def writeTemplate(self, name, template_values):
  path = os.path.join(os.path.dirname(__file__), name)
  self.response.out.write(template.render(path, template_values))

#
# User Frontpage
#
class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      records = DataModel().getmy()
    else:
      records = DataModel().getpublic()
    template_values = {'records':records,
                       'user':user
                       }
    writeTemplate(self, 'main.html', template_values)


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
    data = google_prediction.Predict(getAuth(model), DataModel().getdatafile(model), [post])
    
    addreturn = self.request.get('addreturn','')
    if addreturn:
      try:
        json_content = json.loads(data)['data']
        if 'outputLabel' in json_content:
          self.response.out.write(json_content['outputLabel']) # classification task
        elif 'outputValue' in json_content:
          self.response.out.write(json_content['outputValue'])               
        else:
          self.response.out.write(cgi.escape(data))
      except:
        self.response.out.write(data)      
      self.response.out.write(self.request.get('addreturn',''))
    else:
      self.response.out.write(cgi.escape(data))

  def get(self):
    model = cgi.escape(self.request.get('model'))
    post = cgi.escape(self.request.get('content'))
    # Make the Google Prediction API call
    data = google_prediction.Predict(getAuth(model), DataModel().getdatafile(model), [post])

    try:
      json_content = json.loads(data)['data']

      # classification task
      if 'outputLabel' in json_content:
        self.response.out.write(json_content['outputLabel'])
      elif 'outputValue' in json_content:
        self.response.out.write(json_content['outputValue'])        
      else:
        self.response.out.write(cgi.escape(json))
    except:
      self.response.out.write(data)
    #always print add return reference
    self.response.out.write(self.request.get('addreturn',''))      
    

#
# Get Auth for API call
#
def getAuth(model):
  if users.get_current_user():
    auth = ApiKey().get()
  else:
    auth = ApiKey().getbymodel(model)
  return auth.strip()



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



    
application = webapp.WSGIApplication([
            ('/', MainPage),
            ('/api/predict', Prediction),
            ('/text', Text),
            ('/signin', SignIn)
            ],
            debug=True)


def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
