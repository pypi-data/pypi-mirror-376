from ..rest import Rest
from ..managers.client_friend_manager import ClientFriendManager
from .friend_request import FriendRequest
from .user import User

class ClientUser(User):
	def __init__(self, data={}, **kwargs):
		super().__init__(data, True, **kwargs)
		self.friends = ClientFriendManager(**kwargs)
		self._patch(data)

	def _patch(self, data={}):
		super()._patch(data)
		if 'friends' in data:
			friends = data.get('friends')
			self.friends.extend([User(friend) for friend in friends.get('friends_data')])

		if 'friend_requests' in data:
			friend_requests = data.get('friend_requests')
			self.friends.requests.extend([FriendRequest(data, parent=self.friends.requests) for data in friend_requests.get('request_data')])

		if 'liked_tracks' in data:
			likedTracks = data.get('liked_tracks')
			self.likedTracks = likedTracks.get('tracks')

	def change_description(self, description):
		return bool(Rest.post('account/edit_profile', True, data={
			'name': 'about',
			'value': description
		}))

	def change_password(self, old_password, new_password):
		return bool(Rest.post('account/change_password', True, data={
			'old_password': old_password,
			'new_password': new_password
		}))

	def change_username(self, username):
		if len(str(username)) < 3:
			raise Exception("Username must be 3 characters or longer")
		return bool(Rest.post('account/edit_profile', True, data={
			'name': 'u_name',
			'value': str(username)
		}))

	def delete_personal_data(self):
		return bool(Rest.post('account/delete_all_personal_data', True))

	def select_profile_image(self, img_type: str):
		return bool(Rest.post('account/update_photo', True, data={'img_type': img_type}))

	def set_forum_password(self, password):
		return bool(Rest.post('account/update_forum_account', True, data={'password': str(password)}))

	def update_personal_data(self, name: str, value):
		return bool(Rest.post('account/update_personal_data', True, data={
			'name': name,
			'value': value
		}))