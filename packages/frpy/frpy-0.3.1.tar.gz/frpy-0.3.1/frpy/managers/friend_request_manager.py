from ..rest import Rest

class FriendRequestManager(list):
	def __init__(self, client):
		self.client = client
		self.outgoing = set()

	def accept(self, uid):
		uid = str(uid).lower()
		for req in self:
			if req.user.get('id') == uid or req.user.get('username') == uid:
				return req.accept()

		return False

	def reject(self, uid):
		uid = str(uid).lower()
		for req in self:
			if req.user.get('id') == uid or req.user.get('username') == uid:
				return req.reject()

		return False

	def send(self, username):
		username = username.lower()
		if username in self.outgoing:
			return False

		res = Rest.post('friends/send_friend_request', data={'u_name':username})
		return res and not self.outgoing.add(username)