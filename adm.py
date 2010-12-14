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
# This code was modified by Federico Elles which
# can be found at http://code.google.com/p/predictionwiz/


__author__ = 'Robert Kaplow vs. Federico Elles'

import cgi
import os
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import google_prediction
from data import DataModel, ApiKey

def writeTemplate(self, name, template_values):
  path = os.path.join(os.path.dirname(__file__), name)
  self.response.out.write(template.render(path, template_values))

#
# Adm Frontpage
#
class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      template_values = {'records':DataModel().getmy()}
      writeTemplate(self, 'adm.html', template_values)
    else:
      self.redirect(users.create_login_url(self.request.uri))    

class Logout(webapp.RequestHandler):
  def get(self):
    self.redirect(users.create_logout_url("/"))



# You need to create a file auth-token which has the token returned from a
# google_prediction.get_auth() call
def getAuth():
    #auth_file = open('auth-token', 'r')
    #auth = auth_file.read()
    #auth_file.close()
    auth = ApiKey().get()
    return auth.strip()

class AdmGetToken(webapp.RequestHandler):
  def post(self):
    user = cgi.escape(self.request.get('user'))
    userpass = cgi.escape(self.request.get('pass'))
    self.response.out.write (google_prediction.GetAuthentication(user,userpass))

#
# Create new model
#
class AdmNewModel(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      datafile = cgi.escape(self.request.get('datafile','')).strip()
      bucket = cgi.escape(self.request.get('bucket','')).strip()  
      caption = cgi.escape(self.request.get('caption','')).strip()
      public = cgi.escape(self.request.get('public','')).strip()
      if caption == '':
        caption = datafile
      if public == 'on':
        public = True
      else:
        public = False

      
      if datafile != '' and caption != '' and bucket != '':
        newmodelkey = DataModel().save(bucket,datafile,caption,public)
      self.redirect("/adm/")
    else:
      self.redirect(users.create_login_url(self.request.uri))    

#
# Deete model
#
class AdmDeleteModel(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:    
      key = cgi.escape(self.request.get('key',''))
      DataModel().drop(key)
      self.redirect("/adm/")      

#
# Train new model
#
class AdmTrain(webapp.RequestHandler):
  def post(self):
    datafile = cgi.escape(self.request.get('datafile'))
    self.response.out.write (google_prediction.Train(getAuth(),datafile))

#
# Ask for status of training
#
class AdmTrainStatus(webapp.RequestHandler):
  def post(self):
    datafile = cgi.escape(self.request.get('datafile'))
    self.response.out.write (google_prediction.TrainStatus(getAuth(),datafile))

#
# Save key for user
#
class KeySaver(webapp.RequestHandler):
  def post(self):
    try:
      key = cgi.escape(self.request.get('key'))
      ApiKey().save(key)
      self.response.out.write ('Saved!')
    except:
      self.response.out.write ('Error')
  def get(self):
    try:
      self.response.out.write (ApiKey().get())
    except:
      self.response.out.write ('Loading key failed')





application = webapp.WSGIApplication([
            ('/adm/', MainPage),
            ('/adm/key', KeySaver),            
            ('/adm/exit', Logout),            
            ('/adm/new', AdmNewModel),
            ('/adm/delete', AdmDeleteModel),            
            ('/adm/api/gettoken', AdmGetToken),
            ('/adm/api/train', AdmTrain),
            ('/adm/api/trainstatus', AdmTrainStatus)
            ],
            debug=True)


def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
