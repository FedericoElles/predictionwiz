def getConfig(what):
  options = {
    'salt':'', #any random string
    'pepper':'', #any random string
    'client_id':'', #Visit https://code.google.com/apis/console to            
    'client_secret':'' # generate your client_id, client_secret and to register your redirect_uri.
    }
  return options[what]
