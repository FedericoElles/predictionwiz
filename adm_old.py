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
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import google_prediction


class BlogComment(db.Model):
  """ Represents a comment from the application. This will get stored to the
  data store.
  """
  content = db.TextProperty()
  tag = db.StringProperty(multiline=True)
  best_score = db.FloatProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  author = db.UserProperty()


class MainPage(webapp.RequestHandler):
  """ Represents the main page of the blog. It displays the current comments as
  well as the input box for a new comment.
  """

  def get(self):

    self.response.out.write("""<html><head>
      <link type="text/css" rel="stylesheet" href="/stylesheets/main.css" />
      </head><body>""")
    self.response.out.write("""
    <div>
    <img src="http://www.google.com/images/icons/feature/api-b128.png"
    class="center"/>
    <br /><br />
    <h2>This blog is a use case for the Google Prediction API. Imagine this
    is your favorite physics blog, which will track cutting edge physics
    research for a general audience. Unfortunately, you have a problem with
    spam comments every time you add a new post. Luckily, you've heard of the
    Google Prediction API and you try to see how well it can do at classifying
    spam comments with a minimum dataset.</h2>
    </div>""")

    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
    comments = db.GqlQuery('SELECT * FROM BlogComment '
                           'ORDER BY date DESC LIMIT 50')
    for comment in comments:
      self.response.out.write('<hr />')
      if comment.tag == 'spam':
        self.response.out.write('<div class="spam">')
      else:
        self.response.out.write('<div class="ham">')
      if comment.author:
        self.response.out.write('<b>%s</b> wrote:' % comment.author.nickname())
      else:
        self.response.out.write('An anonymous person wrote:')
      if comment.content:
        self.response.out.write('<blockquote>%s</blockquote>'%(comment.content))
      if comment.tag:
        self.response.out.write('Marked as %s' % comment.tag)
      if comment.best_score:
        self.response.out.write(', score is %f ' % comment.best_score)
      self.response.out.write('</div>')

    self.response.out.write("""Post comment:
              <form action="/posted" method="post">
                <div><textarea name="content" rows="20" cols="80"></textarea>
                </div>
                <input type="checkbox" name="real_submit" value="true" />
                Actually Submit <br />
                <div><input type="submit" value="Categorize"></div>
              </form>
            </body>
          </html>""")


class Moderation(webapp.RequestHandler):
  """ Represents the moderation page for the blog. It will show the
  classification for the new comment as well as the scores.
  """


  def post(self):
    # Get the authentication token.
    auth = getAuth()
    # Set your model here:
    model = 'metro/language_id.txt'
    # Get the post from the HTML form
    post = cgi.escape(self.request.get('content'))
    # Make the Google Prediction API call
    [prediction, scores] = google_prediction.Predict(auth, model, [post])

    real_submit = cgi.escape(self.request.get('real_submit'))
    self.response.out.write("""<html><head>
      <link type="text/css" rel="stylesheet" href="/stylesheets/main.css" />
      </head><body>""")

    self.response.out.write('You wrote:<br /><br />')
    self.response.out.write(post)
    self.response.out.write('<br /><br />')
    self.response.out.write('Your comment has been flagged as: <pre>')
    self.response.out.write(cgi.escape(prediction))
    self.response.out.write('<br /><br /><b>Statistics:</b> <br />')
    for key, value in scores.items():
      self.response.out.write('label is %s, score is %s<br />' %(key, value))
    self.response.out.write('</pre>')

    if real_submit == 'true':
      # Store the blog comment
      comment = BlogComment()
      comment.content = post
      comment.tag = cgi.escape(prediction)
      comment.best_score = scores[prediction]

      # Add author if available
      if users.get_current_user():
        comment.author = users.get_current_user()
      comment.put()  # Save the comment to our datastore
      self.response.out.write('<br /><br />Thank you for posting!')
    self.response.out.write('</body></html>')


# You need to create a file auth-token which has the token returned from a
# google_prediction.get_auth() call
def getAuth():
    auth_file = open('auth-token', 'r')
    auth = auth_file.read()
    auth_file.close()
    return auth.strip()

class AdmGetToken(webapp.RequestHandler):
  def get(self):
    user = self.request.get('user')
    userpass = self.request.get('pass') + '..'
    self.response.out.write (google_prediction.GetAuthentication(email,password))

class AdmTrain(webapp.RequestHandler):
  def get(self):
    datafile = 'metro/language_id.txt'
    self.response.out.write (google_prediction.Train(getAuth(),datafile))

class AdmTrainStatus(webapp.RequestHandler):
  def get(self):
    datafile = 'metro/language_id.txt'
    self.response.out.write (google_prediction.TrainStatus(getAuth(),datafile))




application = webapp.WSGIApplication([
            ('/', MainPage),
            ('/posted', Moderation),
            ('/adm/gettoken', AdmGetToken),
            ('/adm/train', AdmTrain),
            ('/adm/trainstatus', AdmTrainStatus)                        
            ],
            debug=True)


def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
