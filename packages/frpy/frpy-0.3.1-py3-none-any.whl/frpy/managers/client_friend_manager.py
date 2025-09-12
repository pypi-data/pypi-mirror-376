from ..rest import Rest
from .friend_manager import FriendManager
from .friend_request_manager import FriendRequestManager

class ClientFriendManager(FriendManager):
	def __init__(self, **kwargs):
		self.requests = FriendRequestManager(**kwargs)

	def add(self, username):
		username = username.lower()
		for friend in self:
			if friend.username == username:
				return True

		for req in self.requests:
			if req.user.get('username') == username:
				return req.accept()

		return self.requests.send(username)

	def remove(self, uid):
		for friend in self:
			if friend.get('username') == uid:
				uid = friend.id

		return Rest.post('friends/remove_friend', data = {
			'u_id': uid
		}).get('result')