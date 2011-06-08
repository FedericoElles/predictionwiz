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

"""A simple blog application written on Google App Engine. This renders both the
MainPage as well as the Moderation page, which will show the classification
results.
"""

__author__ = 'Robert Kaplow, Federico Elles'



from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import urlfetch
try:
  import json
except ImportError:
  from django.utils import simplejson as json

import sys
import cgi
import httplib2
import logging
import os
import pickle
import time, datetime
import random
import urllib
import urlparse
import urllib2

from apiclient.discovery import build
from oauth2client.appengine import CredentialsProperty
from oauth2client.appengine import StorageByKeyName
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import AccessTokenRefreshError
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from apiclient.errors import HttpError as HTTPError

class Credentials(db.Model):
  credentials = CredentialsProperty()

from data import DataModel, ApiKey, getUserHash


#time interpretation
#import texttime
#texttime.LANG = "en"

#_sidChars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
#_defaultTimeout=60*60*24*30 # 30 days
#_defaultCookieName='sid'



#prediction wiz


def writeTemplate(self, name, template_values):
  path = os.path.join(os.path.dirname(__file__), name)
  self.response.out.write(template.render(path, template_values))


#
# Logout
#
class Logout(webapp.RequestHandler):
  def get(self):
    self.redirect(users.create_logout_url("/"))



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
    user = users.get_current_user()
    if user:      
      datafile = cgi.escape(self.request.get('datafile'))
      html = json.dumps(Training(user.user_id(),'insert',datafile))
      self.response.out.write (html)

#
# Ask for status of training
#
class AdmTrainStatus(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:      
      datafile = cgi.escape(self.request.get('datafile'))
      html = json.dumps(Training(user.user_id(),'get',datafile))
      self.response.out.write (html)



# ----------
# oAuth2Test
# ----------

class MainPage(webapp.RequestHandler):

  def get(self):
    user = users.get_current_user()
    if user:      
      
      credentials = StorageByKeyName(
          Credentials, user.user_id(), 'credentials').get()

      if credentials is None or credentials.invalid == True:
        flow = OAuth2WebServerFlow(
            # Visit https://code.google.com/apis/console to
            # generate your client_id, client_secret and to
            # register your redirect_uri.
            client_id = '171963544562.apps.googleusercontent.com',
            client_secret = '7bQAlIeYBOGpSve3nttukuOE',

            scope='https://www.googleapis.com/auth/prediction',
            user_agent='predictionwiz/1.2',
            domain='anonymous',
            xoauth_displayname='Prediction Wizard')

        callback = self.request.relative_url('/adm/auth')
        authorize_url = flow.step1_get_authorize_url(callback)
        memcache.set(user.user_id(), pickle.dumps(flow))
        self.redirect(authorize_url)
      else:
        template_values = {'records':DataModel().getmy()}
        writeTemplate(self, 'adm.html', template_values)

    else:
      self.redirect(users.create_login_url(self.request.uri))  

class OAuthHandler(webapp.RequestHandler):

  def get(self):
    user = users.get_current_user()
    if user:      
      
      flow = pickle.loads(memcache.get(user.user_id()))
      if flow:
        credentials = flow.step2_exchange(self.request.params)
        StorageByKeyName(
            Credentials, user.user_id(), 'credentials').put(credentials)
        ApiKey().save(user.user_id())
        self.redirect("/adm/debug_oauth_check")
      else:
        pass
    else:
      self.redirect(users.create_login_url(self.request.uri))  



#
# Verifying oAuth Token
# Documentation
# 1: http://api-python-client-doc.appspot.com/prediction/v1.1/training
# 2: http://code.google.com/p/google-api-python-client/source/browse/samples/prediction/prediction.py
#

class oAuthCheck2(webapp.RequestHandler):
  def get(self):

    user = users.get_current_user()
    if user:
      #userid = user.user_id()
      userid, apikey = ApiKey().getbyuser()
      check = self.request.get('check','0').encode('ascii')

      testfile = 'predictionoracle/qualityconf.55.txt'

      if check == '0':
        html = json.dumps(Training(userid,'get',testfile))
      if check == '1':
        html = json.dumps(Training(userid,'insert',testfile))
      if check == '3':
        html = Predict(userid, testfile, 'this is a test')                

   

      self.response.out.write(html)
    else:
      self.redirect(users.create_login_url(self.request.uri))  






#
# Ask for training status
#
def Training(userid, action, model):
  try:  
    credentials = StorageByKeyName(
      Credentials, userid, 'credentials').get()
    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build("prediction", "v1.2", http=http)
    train = service.training()
    body = {'id' : model}
    if (action == 'get'):
      start = train.get(data=model).execute()
    if (action == 'insert'):
      start = train.insert(body=body).execute()
    return start
  except AccessTokenRefreshError:
    return {"error":{"message":"The credentials have been revoked or expired, please re-run the application to re-authorize"}}
  except HTTPError,e:
    return json.loads(e.content)

  

#
# Predict something
#
def Predict(userid, model, query):
  credentials = StorageByKeyName(
    Credentials, userid, 'credentials').get()
  http = httplib2.Http()
  http = credentials.authorize(http)
  service = build("prediction", "v1.2", http=http)
  body = {'input': {'csvInstance': [query]}}
  prediction = service.predict(body=body, data=model).execute()

  return prediction


def GetPostData(query):
  post_data = json.dumps({
      'input': {
          'csvInstance': [query]
              }
  })
  return post_data



def GetPostDataOld(query):
  data_input = {}
  data_input['mixture'] = query

  post_data = json.dumps({
      'data': {
          'input': data_input
              }
  })
  return post_data







application = webapp.WSGIApplication([
            ('/adm/', MainPage),                     
            ('/adm/exit', Logout),            
            ('/adm/new', AdmNewModel),
            ('/adm/delete', AdmDeleteModel),            
            ('/adm/api/train', AdmTrain),
            ('/adm/api/trainstatus', AdmTrainStatus),
            ('/adm/auth', OAuthHandler),
            ('/adm/debug_oauth_check', oAuthCheck2)
            ],
            debug=True)


def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
