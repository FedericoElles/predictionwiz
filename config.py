def getConfig(what):
  options = {
    'salt':'salt', #any random string
    'pepper':'pepper', #any random string
    'client_id':'xxx', #Visit https://code.google.com/apis/console to            
    'client_secret':'yyy', # generate your client_id, client_secret and to register your redirect_uri.
    'webstore':True # use webstore service
    }
  return options[what]
