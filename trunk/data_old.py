#
# This code was created by Federico Elles which
# can be found at http://code.google.com/p/predictionwiz/

from google.appengine.api import users
from google.appengine.ext import db
import hashlib

def getUserHash():
    user = users.get_current_user().email()
    return hashlib.md5('salt'+user+'pepper').hexdigest()

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
      return ''    

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

class ApiKey(db.Model):
  userhash = db.StringProperty()
  userkey = db.TextProperty()

  def save(self,userkey):
    userhash = getUserHash()
    apikey = self.get_by_key_name(userhash)
    if not apikey:
      apikey = ApiKey(key_name=userhash)
    apikey.userhash = userhash      
    apikey.userkey = userkey
    apikey.put()
    return 0

  def get(self):
    userhash = getUserHash()
    apikey = self.get_by_key_name(userhash)
    if apikey:
      return apikey.userkey
    else:
      return ''

  def getbymodel(self,model):
    userhash = DataModel().getuserhash(model)
    apikey = self.get_by_key_name(userhash)
    if apikey:
      return apikey.userkey
    else:
      return ''    
