def getConfig(what):
  options = {
    'salt':'predictionapi', #any random string
    'pepper':'key', #any random string
    'client_id':'171963544562.apps.googleusercontent.com', #Visit https://code.google.com/apis/console to            
    'client_secret':'7bQAlIeYBOGpSve3nttukuOE', # generate your client_id, client_secret and to register your redirect_uri.
    'webstore':True # use webstore service
    }
  return options[what]
