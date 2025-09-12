from PythonAPIClientBase import LoginSession
import requests
import json

class AdminLoginSession(LoginSession):
  APIClient = None
  apikey = None
  authResponse = None
  def __init__(self, APIClient, apikey):
    self.APIClient = APIClient
    self.apikey = apikey

    self._getNewAuthToken()
    if self.authResponse is None:
      raise Exception("Failed to establish login session using APIKey")

  def _getNewAuthToken(self):
    # Uses API key from App
    post_data = {
      "frontend_instance": self.APIClient.frontend_instance,
      "apikey": self.apikey
    }
    def injectHeaders(headers):
      headers["Content-type"] = "application/json"
      headers["Accept"] = "application/json"

    result = self.APIClient.sendLoginApiRequest(
      reqFn=requests.post,
      origin=None,
      url="/apikeylogin",
      data=json.dumps(post_data),
      loginSession=None,
      injectHeadersFn=injectHeaders,
      skipLockCheck=True
    )
    if result.status_code != 200:
      raise Exception("Failed to login")
    resultJson = json.loads(result.text)
    if resultJson["response"] != "OK":
      raise Exception("Failed to login")
    self.authResponse = {
      "login_token": resultJson["login_token"],
      "refresh_token": resultJson["refresh_token"]
    }


  def injectHeaders(self, headers):
    headers["Authorization"] = "Bearer " + self.authResponse["login_token"]
    headers["Content-type"] = "application/json"
    headers["Accept"] = "application/json"

  def refresh(self):
    return True