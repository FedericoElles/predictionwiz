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

from __future__ import with_statement

__author__ = 'Robert Kaplow, Federico Elles'

from google.appengine.api import files

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
from config import getConfig

class Credentials(db.Model):
  credentials = CredentialsProperty()

from data import DataModel, ApiKey, getUserHash

#storage api
try:
  files.gs
except AttributeError:
  import gs
  files.gs = gs



#time interpretation
#import texttime
#texttime.LANG = "en"

#_sidChars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
#_defaultTimeout=60*60*24*30 # 30 days
#_defaultCookieName='sid'



#prediction wiz
def onlyAdmins():
  try:
    return getConfig('admin_only')
  except:
    return False

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
      datafile = DataModel().getdatafile(key)
      try:
        Delete(user.user_id(),datafile)
      except:
        modelnotfound = True
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
      utility = cgi.escape(self.request.get('utility'))
      key = cgi.escape(self.request.get('key',''))

      html, utilityOutput = Training(user.user_id(),'insert',datafile,utility)
     
      #save utility
      if utilityOutput: #False on error
        html['utility'] = DataModel().setUtility(key,utility)
      else:
        DataModel().setUtility(key,'None')
        html['utility'] = 'Utility set to None'
      html = json.dumps(html)  
      self.response.out.write (html)

#
# Ask for status of training
#
class AdmTrainStatus(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:      
      datafile = cgi.escape(self.request.get('datafile'))
      html, utilityOutput = Training(user.user_id(),'get',datafile,'')
      html = json.dumps(html)
      self.response.out.write (html)



#
#Sync Models in db with server
#

class AdmList(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:          
      modelList = ModelList(user.user_id())
      html = json.dumps(modelList)
      html = str(len(modelList['items']))
      DMs = DataModel().getmy().run(batch_size=1000)
      myList = []
      myListMap = {}
      for dm in DMs:
        myList.append(dm)
        myListMap[dm.datafile] = True

      #check what available
      notavailable = 0
      for model in modelList['items']:
        try:
          temp = myListMap[model['id']]
          #model available
        except:
          #model not available
          ###self.response.out.write(model['id'])
          aData = model['id'].split('/')
          if len(aData) == 2:
            newmodelkey = DataModel().save(aData[0],aData[1],aData[1],False)
          ###self.response.out.write(newmodelkey + '<br>')          
          notavailable += 1
      html2 = str(len(myList))
      ###self.response.out.write (html + '-' + html2 + ':' + str(notavailable))
      self.redirect("/adm/")
  def get(self):
    self.post()


# ----------
# oAuth2Test
# ----------

class MainPage(webapp.RequestHandler):

  def get(self):
    user = users.get_current_user()
    if user:      
      if (onlyAdmins() and users.is_current_user_admin()) or not onlyAdmins(): 

      
        credentials = StorageByKeyName(
            Credentials, user.user_id(), 'credentials').get()

        if credentials is None or credentials.invalid == True:
          flow = OAuth2WebServerFlow(
              client_id = getConfig('client_id'), 
              client_secret = getConfig('client_secret'),
              scope='https://www.googleapis.com/auth/prediction',
              user_agent='predictionwiz/1.4',
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
          self.redirect(users.create_logout_url("/"))

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
        self.redirect("/adm/")
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
# New API DOC: http://api-python-client-doc.appspot.com/prediction/v1.5/trainedmodels
#
def Training(userid, action, model, utility):
  try:
    utilityOutput = ''

    credentials = StorageByKeyName(
      Credentials, userid, 'credentials').get()
    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build("prediction", "v1.5", http=http)
    train = service.trainedmodels()
    if (action == 'get'):
      start = train.get(id=model).execute()
    if (action == 'insert'):
      #utility = 'French:5\nEnglish:10'
      oUtility = []
      if utility == 'None':
        utility = False
      if utility:
        aUtility = utility.split('\n')
        utilityOutput = "Records: " + str(len(aUtility))
        for rec in aUtility:
          aRec = rec.split(':')
          if len(aRec) == 2:
            try:
              nRecVal =  float(aRec[1])
              oUtility.append({aRec[0]:nRecVal})
              utilityOutput += aRec[0]+':'+nRecVal + '\n'
            except:
              nRecVal = 0
          #else:
          #  utilityOutput += '\nrec split returned ' + len(aRec) + 'values'

            
            
        
      body = {'storageDataLocation' : model, 'id' : model, 'utility':  oUtility}
      start = train.insert(body=body).execute()
    return start, utilityOutput
  except AccessTokenRefreshError:
    return {"error":{"message":"The credentials have been revoked or expired, please re-run the application to re-authorize"}}, False
  except HTTPError,e:
    return json.loads(e.content), False

  

#
# Predict something
#
def Predict(userid, model, query):
  credentials = StorageByKeyName(
    Credentials, userid, 'credentials').get()
  http = httplib2.Http()
  http = credentials.authorize(http)
  service = build("prediction", "v1.5", http=http)
  train = service.trainedmodels()
  body = {'input': {'csvInstance': query.split(',')}}
  prediction = train.predict(body=body, id=model).execute()

  return prediction




#
# Learn something
#
def Learn(userid, model, query, answer):
  credentials = StorageByKeyName(
    Credentials, userid, 'credentials').get()
  http = httplib2.Http()
  http = credentials.authorize(http)
  service = build("prediction", "v1.5", http=http)
  train = service.trainedmodels()
  body = {'label': answer ,'csvInstance': query.split(',')}
  model = train.update(body=body, id=model).execute()

  return model

#
# Delete model
#
def Delete(userid, model):
  credentials = StorageByKeyName(
    Credentials, userid, 'credentials').get()
  http = httplib2.Http()
  http = credentials.authorize(http)
  service = build("prediction", "v1.5", http=http)
  train = service.trainedmodels()
  #body = {'id' : model}
  train.delete( id= model).execute()

  return True


# 
# Get List
#
def ModelList(userid):
  credentials = StorageByKeyName(
    Credentials, userid, 'credentials').get()
  http = httplib2.Http()
  http = credentials.authorize(http)
  service = build("prediction", "v1.5", http=http)
  train = service.trainedmodels()
  
  mList = train.list().execute()

  return mList




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



class oStorageAPICheck(webapp.RequestHandler):
  def get(self):
    filename = self.request.get('filename') or 'api.txt'
    bucket = self.request.get('bucket') or 'pwiz'
 
    filename = '/gs/'+bucket+'/'+filename
    writable_file_name = files.gs.create(filename, mime_type='text/plain')
    with files.open(writable_file_name, 'a') as f:
      f.write('Hello World!')
      f.write('This is my first Google Cloud Storage object!\n')
      f.write('How exciting!')
    files.finalize(writable_file_name)
    self.response.out.write('file '+filename+' was written successfully.')


application = webapp.WSGIApplication([
            ('/adm/', MainPage),
            ('/adm/sync', AdmList),  
            ('/adm/exit', Logout),            
            ('/adm/new', AdmNewModel),
            ('/adm/delete', AdmDeleteModel),            
            ('/adm/api/train', AdmTrain),
            ('/adm/api/trainstatus', AdmTrainStatus),
            ('/adm/auth', OAuthHandler),
            ('/adm/debug_storage', oStorageAPICheck)
            ],
            debug=True)


def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
