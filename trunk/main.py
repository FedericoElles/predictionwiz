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
import webapp2
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

try:
  import json
except ImportError:
  from django.utils import simplejson as json

from data import DataModel, TextFile, ApiKey, getUserHash, DictModel
from adm import Predict, Learn, writeToGS, userOK, createDM, trainDM, statusDM, modelOK
from config import getConfig

def writeTemplate(self, name, template_values):
  path = os.path.join(os.path.dirname(__file__), name)
  self.response.write(template.render(path, template_values))

def onlyAdmins():
  try:
    return getConfig('admin_only')
  except:
    return False

#
# User Frontpage
#
class MainPage(webapp2.RequestHandler):
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



    #  self.response.write('Hello World')


#
# Sign in
#
class SignIn(webapp2.RequestHandler):
  def get(self):
    self.redirect(users.create_login_url('/'))    

#
# Prediction API for POST and GET
#
class Prediction(webapp2.RequestHandler):
  def post(self):
    model = cgi.escape(self.request.get('model')) #key
    post = cgi.escape(self.request.get('content'))
    downcase = cgi.escape(self.request.get('downcase','n'))
    caching = cgi.escape(self.request.get('caching','0'))
    try:
      caching = int(caching)
    except:
      caching = 0

    if downcase == 'y':
      post = post.lower()

    #result = False
  
     
    # Make the Google Prediction API call
    user = users.get_current_user()
    if user:
      userid, apikey = ApiKey().getbyuser()
    else:
      userid, apikey = ApiKey().getbymodel(model)

    datafile = False
    mydatamodel = DataModel().get(model)
    project = ''
    if mydatamodel:
      if mydatamodel.public or mydatamodel.userhash == getUserHash():
        datafile = mydatamodel.datafile
        project = mydatamodel.project
    
    addreturn = self.request.get('addreturn','')
    addjson = self.request.get('addjson','')

    
   
    if datafile and userid and post:
      memkey = datafile+'//'+userid+'//'+post
      #try:
      if caching > 0:
        cache = memcache.get(memkey)
        if cache is not None:
          data = cache
        else:
          data = Predict(userid, datafile, post, project) 
          memcache.add(memkey, data, caching*60)
      else:
        data = Predict(userid, datafile, post, project) 
           
     
      if addreturn:
        try:
          if 'outputLabel' in data:
            self.response.write(data['outputLabel'])
          elif 'outputValue' in data:
            self.response.write(data['outputValue'])        
          else:
            self.response.write(json.dumps(data))
        except:
          self.response.write(json.dumps(data))   
        self.response.write(self.request.get('addreturn',''))
      else:
        self.response.write(json.dumps(data))

      if addjson:
        self.response.write(addjson)
    else:
      if addreturn:
        self.response.write( 'error'+addreturn)
      else:
        self.response.write( '{"error":"user, model or post were empty"}')
        

  def get(self):
    model = cgi.escape(self.request.get('model')) #key
    post = cgi.escape(self.request.get('content'))
    downcase = cgi.escape(self.request.get('downcase','n'))
    caching = cgi.escape(self.request.get('caching','0'))
    useformat = cgi.escape(self.request.get('format','default'))
    
    try:
      caching = int(caching)
    except:
      caching = 0

    if downcase == 'y':
      post = post.lower()

    result = False

    memkey = model+'//'+post
    if caching > 0:
      cache = memcache.get(memkey)
      if cache is not None:
        result = cache

    if not result:
      # Make the Google Prediction API call
      user = users.get_current_user()
      if user:
        userid, apikey = ApiKey().getbyuser()
      if not user or not userid:
        userid, apikey = ApiKey().getbymodel(model)

      datafile = False
      project = ''
      mydatamodel = DataModel().get(model)
      if mydatamodel:
        #if mydatamodel.public or mydatamodel.userhash == getUserHash(): #not required since you don't want to make a model public to access it.
        datafile = mydatamodel.datafile
        project = mydatamodel.project

      if datafile and userid and post:
        data = Predict(userid, datafile, post, project)          

        if useformat == 'default':
          if 'outputLabel' in data:
            result = data['outputLabel']
          elif 'outputValue' in data:
            result = data['outputValue']
          else:
            result = json.dumps(data)
        elif useformat == 'json':
          result = json.dumps(data)
        elif useformat == 'comma':
          if data['outputMulti']:
            result = ''
            for element in data['outputMulti']:
              result = result + element['label'] + ',' + element['score'] + ','
            result = result + data['outputLabel'] + ','  + data['id']
            #result = result[:-1]
          
      else:
        result = 'ERROR: model or content missing'

      if caching > 0:
        memcache.add(memkey, result, caching*60)


    #always print add return reference
    self.response.write(str(result))  
    self.response.write(self.request.get('addreturn',''))      
    


#
# Learning API for GET
#
class Learning(webapp2.RequestHandler):
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
        self.response.write(model['trainingStatus'])
      elif 'kind' in model:
        self.response.write(model['kind'])
      else:
        self.response.write('ERROR: trainingStatus not found in returned model. Dump: '+json.dumps(model))
     
    else:
      self.response.write('ERROR: model or content missing')

    #always print add return reference
    self.response.write(self.request.get('addreturn',''))      

#
# upload textfile, return id
#
class Text(webapp2.RequestHandler):
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
        self.response.write(domain+'?key='+key)
      except:
         self.response.write('Error'+text+','+key)
    else:
      self.response.write('')

  def get(self):
    key = cgi.escape(self.request.get('key',''))
    if key:
      textfile = TextFile().get_by_key_name(key)
      self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
      #self.response.headers['Content-Length'] = len(textfile.text)
      self.response.write(textfile.text)


class Demo(webapp2.RequestHandler):
  def get(self,model,title):
    template_values = {'model':model,
                       'title':title
                      }
    writeTemplate(self, 'demo.html', template_values)    


class DemoCreate(webapp2.RequestHandler):
  def get(self):
    template_values = {}
    writeTemplate(self, 'demo_create.html', template_values)    


class Creating(webapp2.RequestHandler):
  def post(self):
    data = cgi.escape(self.request.get('data',''))
    bucket = cgi.escape(self.request.get('bucket',''))
    filename = cgi.escape(self.request.get('name',''))
    userhash = cgi.escape(self.request.get('hash',''))
    error = ''

    if data == '': error = 'data value blank'
    if bucket == '': error = 'bucket value blank'
    if filename == '': error = 'file name value blank'
    if userhash == '': error = 'hash  value blank'
    if userhash:
      if not userOK(userhash): error = 'userhash not found'

    if error:
      self.response.write('ERROR '+error)
    else:
      modelName = writeToGS(bucket,filename,data)
      #self.response.write(modelName)
      modelKey = createDM(bucket,filename,modelName,userhash)

      userid, apikey = ApiKey().getbymodel(modelKey)
      
      feedback = trainDM(userid, modelName)

      if 'error' in feedback:
         self.response.write ('ERROR ' + feedback['error']['message'])
      else:
        #html = json.dumps(feedback)  
        self.response.write (modelKey)


class Creating2(webapp2.RequestHandler):
  def post(self):
    fileContent = cgi.escape(self.request.get('fileContent',''))
    bucketName = cgi.escape(self.request.get('bucketName',''))
    fileName = cgi.escape(self.request.get('fileName',''))
    hashKey = cgi.escape(self.request.get('hashKey',''))
    error = ''

    if fileContent == '': error = 'fileContent value blank'
    if bucketName == '': error = 'bucketName value blank'
    if fileName == '': error = 'fileName name value blank'
    if hashKey == '': error = 'hashKey value blank'
    if hashKey:
      if not userOK(hashKey): error = 'hashKey not found'

    if error:
      self.response.write('{"error":"'+error+'"}')
    else:
      modelName = writeToGS(bucketName,fileName,fileContent)
      #self.response.write(modelName)
      modelKey = createDM(bucketName,fileName,modelName,hashKey)

      userid, apikey = ApiKey().getbymodel(modelKey)
      
      feedback = trainDM(userid, modelName)

      if 'error' in feedback:
         self.response.write ('{"error":"'+ feedback['error']['message']+'"}')
      else:
        #html = json.dumps(feedback)  
        self.response.write ('{"modelKey":"'+modelKey+'","feedback":'+json.dumps(feedback)+"}")        
  def get(self):
    self.post()

# DONE <accuracy>
# RUNNING
# ERROR <reason>
class Status(webapp2.RequestHandler):
  def get(self):
    model =self.request.get('model','')
    error = ''
    if model == '': error = 'model value blank'

    if model:
      if not modelOK(model):
        error = 'model not found'
      else:
        userhash = DataModel().getuserhash(model)
        if userhash == '':
          error = 'user not available for model'
    
    if error:
      self.response.write('ERROR '+error)
    else:
      userid, apikey = ApiKey().getbymodel(model) 
      feedback = statusDM(userid, model)
      #self.response.write ('Userhash:'+userid)
      #self.response.write ('Model: '+model)  
      
      if 'error' in feedback:
         self.response.write ('ERROR ' + feedback['error']['message'])
      else:
        status = feedback['trainingStatus']
        if status == 'DONE':
          if 'classificationAccuracy' in feedback['modelInfo']:
            accu = feedback['modelInfo']['classificationAccuracy']
            self.response.write (status+' '+str(accu))
          else:
            self.response.write ('ERROR This is no classification model')
        else:
          self.response.write (status)   
        #html = json.dumps(feedback)  
        #self.response.write (html)      


class DictSet(webapp2.RequestHandler):
  def get(self,name):
    key = cgi.escape(self.request.get('key',''))
    value = cgi.escape(self.request.get('value',''))
    
    if key and value and name:
      self.response.write (DictModel().save(name,key,value))
    else:
      self.response.write ('key or value parameter missing')

class DictGet(webapp2.RequestHandler):
  def get(self,name):
    key = cgi.escape(self.request.get('key',''))

    if key:
      self.response.write (DictModel().getValue(name,key))
    else:
      self.response.write ('key missing')

class DictDelete(webapp2.RequestHandler):
  def get(self,name):
    key = cgi.escape(self.request.get('key',''))
    if key:
      self.response.write (DictModel().deleteValue(name,key))
    else:
      self.response.write ('key missing')

class DictEmpty(webapp2.RequestHandler):
  def get(self,name):
    self.response.write ('not yet available')
    
app = webapp2.WSGIApplication([
            ('/', MainPage),
            ('/api/predict', Prediction),
            ('/api/learn', Learning),
            ('/api/create', Creating),
            ('/api/status', Status),
            ('/api2/create', Creating2),           
            ('/demo/(.*)/(.*)', Demo),
            ('/demo/create', DemoCreate),
            ('/text', Text),
            ('/signin', SignIn),
            ('/dict/(.*)/set', DictSet),
            ('/dict/(.*)/get', DictGet),
            ('/dict/(.*)/delete', DictDelete),
            ('/dict/(.*)/empty', DictEmpty)            
            ],debug=True)

