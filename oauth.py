import web
import os
import requests
import urllib, urllib2, httplib
import json 
from sanction import Client

from StringIO import StringIO


web.config.debug = False
# get a Client ID and Secret from 
# https://login.rally1.rallydev.com/accounts/index.html#/clients
CLIENT_ID = os.environ.get('CLIENT_ID', '') 
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '') 
# Server URL must match the one specified when creating the client
SERVER_URL = os.environ.get('SERVER_URL', '') + "/oauth-redirect"


# We will use these to make WSAPI calls
RALLY_WSAPI_URL = "https://rally1.rallydev.com"
RALLY_USER_URL = RALLY_WSAPI_URL + "/slm/webservice/v2.x/user"
RALLY_STORIES_URL = RALLY_WSAPI_URL + "/slm/webservice/v2.x/hierarchicalrequirement"

try:
	c = Client(auth_endpoint = "https://rally1.rallydev.com/login/oauth2/auth",
			token_endpoint = "https://rally1.rallydev.com/login/oauth2/token",
			client_id = CLIENT_ID,
			client_secret = CLIENT_SECRET)

except Exception, e:
	print "Failed to init the OAuth2 Client " + str(e)
	exit(0)


urls = (
	'/', 'display_stories', 
	'/login', 'login',
	'/logout', 'logout',
	'/oauth-redirect', 'redirect' 
)

app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'access_token' : None})
render = web.template.render('templates')

class display_stories:
	def GET(self, *args, **kwargs):
		if not session.get("access_token"): # redirect if we aren't logged in
			raise web.seeother('/login')
		
		
		r = requests.get(RALLY_USER_URL, headers = { "zsessionid" : session["access_token"] })
		user_resp = r.json()
		username = user_resp.get("User", {}).get("UserName")
		if not username:
			raise Exception("No username found")

		story_params = { "fetch" : "Name", "query" : "(Owner = dgriffin@rallydev.com)" }
		r = requests.get( RALLY_STORIES_URL, params=story_params, headers = { "zsessionid" : session["access_token"], "Accept" : "application/json" })
		return render.index(username, r.json()["QueryResult"]["Results"]) 

class login:
	def GET(self, *args, **kwargs):
		# redirect to the Rally OAuth server
		raise web.seeother(c.auth_uri(redirect_uri = SERVER_URL, scope="openid"))

class logout:
	def GET(self, *args, **kwargs):
		session.access_token = None
		return "Logged out"

class redirect:
	def GET(self, *args, **kwargs):
		code = web.input( code = '')["code"]
		
		# we lookup the access token using the speicified code
		# we need to send the same redirect_uri even though we don't redirect
		access_token = c.request_token( redirect_uri = SERVER_URL, code = code )
		# set the access_token on the session
		session.access_token = c.access_token
		
		raise web.seeother('/')


if __name__ == "__main__":
	app.run()
