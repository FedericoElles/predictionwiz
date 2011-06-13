#
# This code was created by Federico Elles which
# can be found at http://code.google.com/p/predictionwiz/

from google.appengine.api import users
from google.appengine.ext import db
import hashlib
from config import getConfig

def getUserHash():
  user = users.get_current_user()
  if user:
    return hashlib.md5(getConfig('salt')+user.email()+getConfig('pepper')).hexdigest()
  else:
    return False

#
# DataModel
#
class DataModel(db.Model):
  userhash = db.StringProperty()
  datafile = db.StringProperty()
  caption = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  public = db.BooleanProperty(default=False)

  def save(self,bucket,datafile,caption,public):
    model = DataModel()
    model.datafile = bucket + '/' + datafile
    model.caption = caption
    model.public = public
    model.userhash = getUserHash()
    model.put()
    return str(model.key())

  def drop(self,key):
    model = self.get(key)
    if model:
      if model.userhash == getUserHash():
        model.delete()
    return 0

  def getdatafile(self,key):
    model = self.get(key)
    if model:
      return model.datafile
    else: 
      return False

  def getmy(self):
    records = DataModel.all()
    records.filter('userhash = ',getUserHash())    
    return records

  def getpublic(self):
    records = DataModel.all()
    records.filter('public = ',True)
    return records

  def getuserhash(self,key):
    model = self.get(key)
    if model:
      return model.userhash
    else: 
      return ''

#
# Stores TextFile temporary
#
class TextFile(db.Model):
  id = db.StringProperty()
  text = db.TextProperty()
  date = db.DateTimeProperty(auto_now_add=True)
#
# Store authentification keys
#
class ApiKey(db.Model):
  userhash = db.StringProperty()
  userkey = db.TextProperty(default='') #v2: user.user_id()
  accesskey = db.TextProperty(default='') #API access key
  
  def saveapikey(self,accesskey):
    userhash = getUserHash()
    apikey = self.get_by_key_name(userhash)
    if not apikey:
      apikey = ApiKey(key_name=userhash)
    apikey.userhash = userhash      
    apikey.accesskey = accesskey
    apikey.put()
    return 0

  def save(self,userkey):
    userhash = getUserHash()
    apikey = self.get_by_key_name(userhash)
    if not apikey:
      apikey = ApiKey(key_name=userhash)
    apikey.userhash = userhash      
    apikey.userkey = userkey
    apikey.put()
    return 0

  def getapikey(self):
    userhash = getUserHash()
    apikey = self.get_by_key_name(userhash)
    if apikey:
      return apikey.accesskey
    else:
      return ''

  def getbyuser(self):
    userhash = getUserHash()
    apikey = self.get_by_key_name(userhash)
    if apikey:
      return apikey.userkey, apikey.accesskey
    else:
      return '',''

  def getbymodel(self,model):
    userhash = DataModel().getuserhash(model)
    apikey = self.get_by_key_name(userhash)
    if apikey:
      return apikey.userkey, apikey.accesskey
    else:
      return '',''
