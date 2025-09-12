from ..rest import Rest
from .base_client import BaseClient
from ..managers.notification_manager import NotificationManager
from ..managers.track_manager import TrackManager
from ..managers.user_manager import UserManager

class Client(BaseClient):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.notifications = NotificationManager(self)
		self.tracks = TrackManager(self)
		self.users = UserManager(self)

	def changeName(self, username):
		return Rest.post(f'account/edit_profile/', data = {
			'name': 'u_name',
			'value': username
		})

	def changeDesc(self, description):
		return Rest.post('account/edit_profile/', data = {
			'name': 'about',
			'value': description
		})

	def changePassword(self, old_password, new_password):
		return Rest.post('account/change_password/', data = {
			old_password,
			new_password
		})

	def changeForumsPassword(self, password):
		return Rest.post('account/update_forum_account/', data = {
			password
		})

	def redeemCoupon(self):
		return Rest.post('store/redeemCouponCode/')

	def transferCoins(self, user, amount, message = ''):
		return bool(Rest.post('account/plus_transfer_coins', data = {
			'transfer_coins_to': user,
			'transfer_coins_amount': amount,
			'msg': message
		}))