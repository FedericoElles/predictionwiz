### UPDATE 1.6 BETA ###
  * Works with Prediction API 1.6


---


# IMPORTANT #
Due to a bug in the Google oAuth2, you must reauthorize the Prediction Wizard Local Installation:

  1. Go to: https://security.google.com/settings/security/permissions?pli=1
  1. Search for your Prediction Wiz installation.
  1. Revoke access
  1. Go to https://***appid***.appspot.com/ and sign in. You are asked again to give  permissions.
  1. The GET API should work now


---


# About #

After installing this app on your Google App Engine Account, you will be able to use the Google Prediction API without writing any line of code.

The webapp will also provide a very simple GET API to ask for predictions from other apps.

### Requirements: ###
  1. Google App Engine Account
  1. App Engine Python Environment

### Setup: ###
  1. Download source.
  1. Change unique App Engine application identifier inside the app.yaml from "predictionwiz" to "your-app-name"
  1. Change the parameters accordingly in the config.py file. Find more info inside the file or below
  1. Deploy app.
  1. Done.

### Google APIs Console setup: ###
  * Go to https://cloud.google.com/console/project
  * Create a new project or choose an existing one
  * Note down the Project Number, e.g. 1234567890 and update it in the config.py file
  * Go to **Settings** tab
    * Enable Billing (at least $10 monthly)
  * Go to APIs & auth tab -> APIs and:
    * Enable Google Cloud Storage
    * Enable Prediction API
  * Go to **Credentials** tab:
    * Copy Client ID to config.py
    * Copy Client secret to config.py
  * Click on Edit settings:
    * Make sure the Redirect URIs are setup correctly. Example:
```
http://localhost:8080/adm/debug_oauth_callback
http://localhost:8080/adm/auth
https://***appid***.appspot.com/adm/debug_oauth_callback
https://***appid***.appspot.com/adm/auth
```


Everything else is done via the HTML GUI:
  * Authenticating via oAuth2
  * Generating learning files from spread sheets
  * Training prediction models
  * Updating models
  * Verifying learning files against models
  * Allowing other apps to make predictions with a dead simple GET API


### Testimonials ###

This is exactly what I needed for my Android Apps! The simple GET api lets
me use prediction without the massive headaches of "in app" OAuth which was
getting in my way!
Thanks a million!

David -  Wed, Jun 27, 2012


### Webstore ###
Webstore is an additional package allowing you to store and fetch value name pairs. This feature is deactivated by default.
Learn more about the idea behind it here: http://illcom.tumblr.com/post/47614089097/hp-quality-center-remember-last-defect-field


### Create API ###
The create API call allows you to create a new prediction model. For this to work, your Appengine app must have permissions to write to your Google Cloud Storage.
  1. Get Appengine Service name: Administration -> Application Settings -> Copy Service Account Name
  1. Set Access: https://cloud.google.com/console/project -> Select project -> Permissions-> Add member -> Enter  Appengine Service name -> Save -> Give Can edit permissions

Source: https://developers.google.com/appengine/docs/python/googlestorage/overview?hl=de#Prerequisites