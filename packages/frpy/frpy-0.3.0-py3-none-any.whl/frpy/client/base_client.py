import time
from ..rest import Rest
from ..utils.event_emitter import EventEmitter
from ..utils.events import Events
from ..structures.cosmetic import Cosmetic
from ..structures.notification import Notification
from ..structures.client_user import ClientUser

class BaseClient(EventEmitter):
	__interval = 1e3
	__token = None
	def __init__(self, **kwargs):
		self.user = None
		if kwargs.get('listen', True):
			self.__interval = int(kwargs.get('interval', 1e3))
			self.once('ready', self.__requestDatapoll)

	def __requestDatapoll(self, *args):
		resp = self._datapoll()
		# resp['notification_count'] = 1 # debug
		if resp.get('notification_count') > 0:
			notifications = self.notifications.fetch()
			self.emit('raw', notifications)
			for notification in notifications:
				self.emit(notification.id, notification)

		time.sleep(self.__interval / 1e3)
		self.__requestDatapoll()

	def _datapoll(self):
		return Rest.post('datapoll/poll_request', True, data={'notifications': 'true'})

	def _throw(self, exception):
		if self.listeners('error') > 0:
			self.emit('error', exception)
		else:
			raise exception

	def login(self, token):
		if isinstance(token, dict):
			res = Rest.post('auth/standard_login', data=token)
			if 'app_signed_request' in res:
				token = res.get('app_signed_request')

		res = Rest.assertToken(token)
		if not res:
			return

		self.__token = token
		self.user = ClientUser(Rest.get('u/' + res.get('d_name')), client=self)
		for i, partial in enumerate(self.user.friends):
			self.user.friends[i] = self.users.fetch(partial.username)

		for head in [Cosmetic(data) for data in Rest.get('store/gear').get('gear').get('head_gear')]:
			self.user.cosmetics.cache.set(head.id, head)

		self.emit(Events.get('ClientReady'))
		return self

	def logout(self):
		Rest.deleteToken()
		self.emit('disconnected')

	@staticmethod
	def get_token(*args, **kwargs):
		usr = None
		pwd = None

		if len(args) == 2:
			usr, pwd = args
		elif len(args) == 1:
			arg0 = args[0]
			if isinstance(arg0, dict):
				usr = arg0.get('username') or arg0.get('login')
				pwd = arg0.get('password') or arg0.get('pwd')
			elif isinstance(arg0, (set, list, tuple)) and len(arg0) == 2:
				usr, pwd = tuple(arg0)
			else:
				raise ValueError("Invalid argument: must be dict, set, list, tuple, or two positional strings")
		else:
			usr = kwargs.get('username') or kwargs.get('login')
			pwd = kwargs.get('password') or kwargs.get('pwd')

		if not usr or not pwd:
			raise ValueError("Username and password must be provided")

		return Rest.post(
			'auth/standard_login',
			data={'login': usr, 'password': pwd},
			raw=True
		).get('app_signed_request')