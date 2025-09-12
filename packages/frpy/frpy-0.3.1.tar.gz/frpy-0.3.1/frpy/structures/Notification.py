from .base_structure import BaseStructure
from .comment import Comment
from .track import Track
from .user import User
from ..utils.events import Events

class Notification(BaseStructure):
	def __init__(self, data):
		self.id = self.parseId(data)
		if 'message' in data:
			self.message = data.get('message')

		if 'track' in data:
			self.track = Track(data.get('track'))
			if 'comment' in data:
				self.comment = Comment(self.track, data.get('comment'))

		if 'user' in data:
			self.user = User(data.get('user'))

		self.timeAgo = data.get('time')
		self.timestamp = data.get('ts')

	@staticmethod
	def parseId(data):
		if data.get('friend_lb_passed'):
			return Events.get('FriendLeaderboardPassed')
		elif data.get('friend_req_accptd'):
			return Events.get('FriendAdd')
		elif data.get('friend_req_rcvd'):
			return Events.get('FriendRequest')
		elif data.get('friend_t_challenge'):
			return Events.get('TrackChallenge')
		elif data.get('mobile_account_linked_award'):
			return Events.get('MobileAccountLinkedAward')
		elif data.get('subscribed_t_publish'):
			return Events.get('SubscribedTrackPublish')
		elif data.get('track_lb_passed'):
			return Events.get('TrackLeaderboardPassed')
		elif data.get('t_uname_mention'):
			return Events.get('TrackUsernameMention')
		elif data.get('transferred_coins'):
			return Events.get('TransferredCoins')