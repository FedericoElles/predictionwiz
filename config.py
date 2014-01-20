def getConfig(what):
  options = {
    'salt':'salt', #any random string
    'pepper':'pepper', #any random string
    'client_id':'xxx', #Visit https://code.google.com/apis/console to            
    'client_secret':'yyy', # generate your client_id, client_secret and to register your redirect_uri.
    'project':'9999999999999', #NEW: Attention: Number
    #1 Go to https://cloud.google.com/console/project
    #2 Select your predictionwiz app and take a look at the Projekt Number    
    'webstore':False, # use webstore service,
    'admin_only':False # allow only app admins access
    }
  return options[what]
