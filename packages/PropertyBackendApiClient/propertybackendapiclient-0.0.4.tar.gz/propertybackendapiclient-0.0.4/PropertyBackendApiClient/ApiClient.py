
import PythonAPIClientBase
from .LoginSession import AdminLoginSession
import json
import requests
import copy
from .Types import UserObj

# From TestHelperSuperclass. Second version is reversed
infoAPIPrefix = '/api/public/info'
loginAPIPrefix = '/api/public/login'
privateUserAPIPrefix = '/api/private/user'
privateAdminAPIPrefix = '/api/private/admin'

infoAPIPrefixExt = '/public/api/info'
loginAPIPrefixExt = '/public/api/login'
privateUserAPIPrefixExt = '/private/api/user'
privateAdminAPIPrefixExt = '/private/api/admin'



class ApiClient(PythonAPIClientBase.APIClientBase):
  frontend_instance = None
  google_credentials_file = None
  google_temporary_token_file = None

  def __init__(self, baseURL, frontend_instance, google_credentials_file, google_temporary_token_file, mock=None, verboseLogging=PythonAPIClientBase.VerboseLoggingNullLogClass()):
    super().__init__(baseURL=baseURL, mock=mock, forceOneRequestAtATime=True, verboseLogging=verboseLogging)
    self.frontend_instance = frontend_instance
    self.google_credentials_file = google_credentials_file
    self.google_temporary_token_file = google_temporary_token_file

  def sendInfoApiRequest(
      self,
      reqFn,
      origin,
      url,
      data,
      loginSession,
      injectHeadersFn,
      skipLockCheck
  ):
    return self.sendRequest(
      reqFn=reqFn,
      origin=origin,
      url=infoAPIPrefixExt + url,
      data=data,
      loginSession=loginSession,
      injectHeadersFn=injectHeadersFn,
      skipLockCheck=skipLockCheck
    )

  def sendLoginApiRequest(
      self,
      reqFn,
      origin,
      url,
      data,
      loginSession,
      injectHeadersFn,
      skipLockCheck
  ):
    return self.sendRequest(
      reqFn=reqFn,
      origin=origin,
      url=loginAPIPrefixExt + url,
      data=data,
      loginSession=loginSession,
      injectHeadersFn=injectHeadersFn,
      skipLockCheck=skipLockCheck
    )

  def sendUserApiRequest(
      self,
      reqFn,
      origin,
      url,
      data,
      loginSession,
      injectHeadersFn,
      skipLockCheck
  ):
    return self.sendRequest(
      reqFn=reqFn,
      origin=origin,
      url=privateUserAPIPrefixExt + url,
      data=data,
      loginSession=loginSession,
      injectHeadersFn=injectHeadersFn,
      skipLockCheck=skipLockCheck
    )

  def sendAdminApiRequest(
      self,
      reqFn,
      origin,
      url,
      data,
      loginSession,
      injectHeadersFn,
      skipLockCheck,
      params = None
  ):
    return self.sendRequest(
      reqFn=reqFn,
      origin=origin,
      url=privateAdminAPIPrefixExt + url,
      data=data,
      params=params,
      loginSession=loginSession,
      injectHeadersFn=injectHeadersFn,
      skipLockCheck=skipLockCheck
    )


  def getServerInfo(self):
    url = "/serverinfo"
    result = self.sendInfoApiRequest(
      reqFn=requests.get,
      origin=None,
      url=url,
      data=None,
      loginSession=None,
      injectHeadersFn=None,
      skipLockCheck=True
    )
    print(result.status_code)
    if result.status_code != 200:
      print("Error Calling url:", url)
      print("Response code:", result.status_code)
      print("Response text:", result.text)
      raise Exception("Could not get server info")
    return json.loads(result.text)

  def getLoginSession(self, apikey):
    return AdminLoginSession(APIClient=self, apikey=apikey)

  def getMyProfile(self, loginSession):
    result = self.sendUserApiRequest(
      reqFn=requests.get,
      origin=None,
      url="/me",
      data=None,
      loginSession=loginSession,
      injectHeadersFn=None,
      skipLockCheck=True
    )
    if result.status_code != 200:
      print("Error getting user profile")
      print("status", result.status_code)
      print("response", result.text)
      raise Exception("Error getting user profile")
    resultJson = json.loads(result.text)
    return resultJson

  def getsUsers(self, loginSession):
    offset = 0
    result_items = []

    while True:
      result = self.sendAdminApiRequest(
        reqFn=requests.get,
        origin=None,
        url="/users",
        params={
          "pagesize": 1,
          "offset": offset
        },
        data=None,
        loginSession=loginSession,
        injectHeadersFn=None,
        skipLockCheck=True
      )
      if result.status_code != 200:
        print("Error getting user profile")
        print("status", result.status_code)
        print("response", result.text)
        raise Exception("Error getting user profile")
      resultJson = json.loads(result.text)
      result_items += resultJson["result"]
      offset += resultJson["pagination"]["pagesize"]
      if len(resultJson["result"]) == 0:
        break

    resultObjs = []
    for curresult in result_items:
      resultObjs.append(UserObj(curresult))

    return resultObjs

  def getPatch(self, loginSession, patchid, adminMode=False):
    fn = self.sendUserApiRequest
    if adminMode:
      fn = self.sendAdminApiRequest
    result = fn(
      reqFn=requests.get,
      origin=None,
      url="/patches/" + patchid,
      data=None,
      loginSession=loginSession,
      injectHeadersFn=None,
      skipLockCheck=True
    )
    if result.status_code != 200:
      print("Error getting patch")
      print("status", result.status_code)
      print("response", result.text)
      raise Exception("Error getting patch")
    resultJson = json.loads(result.text)
    return resultJson

  def updatePatch(self, loginSession, patchDict):
    # I build this to fix workflow
    #  but didn't need to use it because loading and resaving the project clears the data error
    raise Exception("Untested")
    result = self.sendAdminApiRequest(
      reqFn=requests.post,
      origin=None,
      url="/patches",
      data=json.dumps(copy.deepcopy(patchDict)),
      loginSession=loginSession,
      injectHeadersFn=None,
      skipLockCheck=True
    )
    if result.status_code != 200:
      print("Error updating patch")
      print("status", result.status_code)
      print("response", result.text)
      raise Exception("Error updating patch")
    resultJson = json.loads(result.text)
    return resultJson

  def getProject(self, loginSession, projectid, adminMode=False):
    fn = self.sendUserApiRequest
    if adminMode:
      fn = self.sendAdminApiRequest
    result = fn(
      reqFn=requests.get,
      origin=None,
      url="/projects/" + projectid,
      data=None,
      loginSession=loginSession,
      injectHeadersFn=None,
      skipLockCheck=True
    )
    if result.status_code != 200:
      print("Error getting project")
      print("status", result.status_code)
      print("response", result.text)
      raise Exception("Error getting project")
    resultJson = json.loads(result.text)
    return resultJson

  def upsertProject(self, loginSession, projectDict, adminMode=False):
    fn = self.sendUserApiRequest
    if adminMode:
      fn = self.sendAdminApiRequest
    result = fn(
      reqFn=requests.post,
      origin=None,
      url="/projects",
      data=json.dumps(projectDict),
      loginSession=loginSession,
      injectHeadersFn=None,
      skipLockCheck=True
    )
    if result.status_code != 200:
      print("Error upserting project")
      print("status", result.status_code)
      print("response", result.text)
      raise Exception("Error upserting project")
    resultJson = json.loads(result.text)
    return resultJson
