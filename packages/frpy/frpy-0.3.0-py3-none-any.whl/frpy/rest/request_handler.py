import requests
from urllib.parse import urljoin
from .constants import API_BASE_URL, MAX_RETRIES, TIMEOUT
from .exceptions import AuthenticationError, FreeRiderHDAPIError

class Rest:
	def __init__(self, *args, **kwargs):
		self.__token = None
		if 'token' in kwargs:
			self.__token = kwargs['token']
		elif args:
			arg0 = args[0]
			if isinstance(arg0, dict):
				self.__token = arg0.get('token')
			else:
				self.__token = arg0

		if self.__token is None:
			raise AuthenticationError(self.__token)

	__session = None
	@staticmethod
	def request(*args, raw=False, **kwargs):
		args = list(args)
		require_token = False
		if args:
			last_arg = args[-1]
			if isinstance(last_arg, bool):
				require_token = args.pop(-1)
		require_token = kwargs.pop('require_token', require_token)

		app_signed_request = kwargs.pop('token', Rest.__session and Rest.__session.get('token') or None)
		if require_token and not app_signed_request:
			raise AuthenticationError("Client is not logged in!")

		method = kwargs.pop('method', 'get')
		path = kwargs.pop('path', args.pop(0))
		url = urljoin(f'{API_BASE_URL}/', path)
		params = {'ajax': '', 't_1': 'ref', 't_2': 'frpy'}
		if app_signed_request:
			params['app_signed_request'] = app_signed_request

		resp = getattr(requests, method)(url, params=params, timeout=TIMEOUT, **kwargs)
		resp.raise_for_status()  # raises exception when not a 2xx response
		if resp.headers['content-type'].strip().startswith('application/json'):
			res = resp.json()
			if res.get('result') == False or res.get('code') == False:
				raise FreeRiderHDAPIError(res.get('msg'))
			return res.get('data') if not raw and 'data' in res else res

		raise FreeRiderHDAPIError(f"Unexpected response: {res.text}")

	@staticmethod
	def get(*args, **kwargs):
		return Rest.request(*args, **kwargs)

	@staticmethod
	def post(*args, **kwargs):
		return Rest.request(*args, **kwargs, method='post')

	@staticmethod
	def assertToken(token):
		res = Rest.get("account/settings", token=token)
		if 'user' not in res:
			raise AuthenticationError("Invalid token!")

		Rest.__session = {
			'token': token,
			'user': res.get('user')
		}

		return res.get('user')

	@staticmethod
	def deleteToken():
		Rest.__session = None

	@staticmethod
	def clientUser():
		return Rest.__session and Rest.__session.get('user')