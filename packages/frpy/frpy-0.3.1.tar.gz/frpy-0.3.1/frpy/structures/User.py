from ..rest import Rest
from ..managers.cosmetic_manager import CosmeticManager
from ..managers.friend_manager import FriendManager
from .base_structure import BaseStructure

class User(BaseStructure):
	def __init__(self, data={}, isClient=False, **kwargs):
		user = data.get('user') or data
		self.cosmetics = CosmeticManager(self, user.get('cosmetics'))
		if not isClient:
			self.friends = FriendManager()
			self._patch(data)

	def _patch(self, data={}):
		user = data.get('user') or data
		self.admin = user.get('admin')
		self.avatar = user.get('img_url_large') or user.get('img_url_medium') or user.get('img_url_small')
		self.classic = user.get('classic')
		self.displayName = user.get('d_name')
		self.forums = user.get('forum_url')
		self.id = user.get('u_id')
		self.moderator = user.get('moderator')
		self.plus = user.get('plus')
		self.username = user.get('u_name')
		if 'activity_time_ago' in data:
			self.lastPlayed = data.get('activity_time_ago')
			# or fetch a friend and compute lastPlayed

		if 'a_ts' in data:
			self.lastPlayedTimestamp = data.get('a_ts')

		if 'created_tracks' in data:
			createdTracks = data.get('created_tracks')
			self.createdTracks = createdTracks.get('tracks')

		if 'friends' in data:
			friends = data.get('friends')
			self.friends.extend([User(friend) for friend in friends.get('friends_data')])

		if 'has_max_friends' in data:
			self.friendLimitReached = data.get('has_max_friends')

		if 'liked_tracks' in data:
			likedTracks = data.get('liked_tracks')
			self.likedTracks = likedTracks.get('tracks')

		if 'recently_ghosted_tracks' in data:
			recentlyCompleted = data.get('recently_ghosted_tracks')
			self.recentlyCompleted = recentlyCompleted.get('tracks')

		if 'recently_played_tracks' in data:
			recentlyPlayed = data.get('recently_played_tracks')
			self.recentlyPlayed = recentlyPlayed.get('tracks') # map as Track structures

		if 'subscribe' in data:
			subscribe = data.get('subscribe')
			if subscribe:
				self.subscriberCount = subscribe.get('count')

		if 'user_info' in data:
			info = data.get('user_info')
			if isinstance(info, dict):
				self.bio = info.get('about')

		if 'user_mobile_stats' in data:
			stats = data.get('user_mobile_stats')
			if stats.get('connected'):
				self.mobileStats = {
					'level': stats.get('lvl'),
					'wins': stats.get('wins'),
					'headCount': stats.get('headCount'),
					'connected': stats.get('connected')
				}

		if 'user_stats' in data:
			stats = data.get('user_stats')
			self.stats = {
				'totalPoints': stats.get('tot_pts'),
				'completed': stats.get('cmpltd'),
				'rated': stats.get('rtd'),
				'comments': stats.get('cmmnts'),
				'created': stats.get('crtd'),
				'headCount': stats.get('head_cnt'),
				'totalHeadCount': stats.get('total_head_cnt')
			}

	def subscribe(self):
		return bool(Rest.post('track_api/subscribe', True, data={
			'sub_uid': self.id,
			'subscribe': 1
		}))

	def transfer_coins(self, amount, message = ''):
		return bool(Rest.post('account/plus_transfer_coins', True, data = {
			'transfer_coins_to': self.username,
			'transfer_coins_amount': amount,
			'msg': message
		}))

	def unsubscribe(self):
		return bool(Rest.post('track_api/subscribe', True, data={
			'sub_uid': self.id,
			'subscribe': 0
		}))

	def ban(self):
		if self.client.user.admin:
			return bool(Rest.post('admin/ban_user', True, data = {
				'ban_secs': int(duration),
				'delete_race_stats': delete_races,
				'username': self.username
			}))

		if self.client.user.moderator:
			return bool(Rest.post('moderator/ban_user', True, data = {
				'u_id': self.id
			}))

		raise Exception("Insufficient privileges")

	def change_email(self, email):
		if self.client.user.admin:
			return bool(Rest.post('admin/change_user_email', True, data = {
				'username': self.username,
				'email': email
			}))

		if self.client.user.moderator:
			return bool(Rest.post('moderator/change_email', True, data = {
				'u_id': self.id,
				'email': email
			}))

		raise Exception("Insufficient privileges")

	def rename(self, username):
		if self.client.user.admin:
			return bool(Rest.post('admin/change_username', True, data={
				'change_username_current': self.username,
				'change_username_new': username
			}))

		if self.client.user.moderator:
			return bool(Rest.post('moderator/change_username', True, data={
				'u_id': self.id,
				'username': username
			}))

		raise Exception("Insufficient privileges")

	def unban(self):
		if self.client.user.moderator:
			return bool(Rest.post('moderator/unban_user', True, data={'u_id': self.id}))
		raise Exception("Insufficient privileges")

	def deactivate(self):
		if not self.client.user.admin:
			raise Exception("Insufficient privileges")
		return bool(Rest.post('admin/deactivate_user', True, data={'username': self.username}))

	def delete(self):
		if not self.client.user.admin:
			raise Exception("Insufficient privileges")
		return bool(Rest.post('admin/delete_user_account', True, data={'username': self.username}))

	def toggle_official_author(self):
		if not self.client.user.moderator:
			raise Exception("Insufficient privileges")
		return bool(Rest.post('moderator/toggle_official_author/' + str(self.id), True))

	def toggle_classic_author(self):
		if not self.client.user.admin:
			raise Exception("Insufficient privileges")
		return bool(Rest.post('admin/toggle_classic_user', True, data={'toggle_classic_uname': self.username}))

	def add_plus_days(self, days, remove):
		if not self.client.user.admin:
			raise Exception("Insufficient privileges")
		return bool(Rest.post('admin/add_plus_days', True, data={
			'add_plus_days': days,
			'username': self.username,
			'add_plus_remove': remove
		}))

	def award_coins(self, coins):
		if not self.client.user.admin:
			raise Exception("Insufficient privileges")
		return bool(Rest.post('admin/add_won_coins', True, data={
			'coins_username': self.username,
			'num_coins': int(coins)
		}))

	def add_messaging_ban(self):
		if not self.client.user.admin:
			raise Exception("Insufficient privileges")
		return bool(Rest.post('admin/user_ban_messaging', True, data={'messaging_ban_username': self.username}))

	def add_uploading_ban(self):
		if not self.client.user.admin:
			raise Exception("Insufficient privileges")
		return bool(Rest.post('admin/user_ban_uploading', True, data={'uploading_ban_username': self.username}))

	def str(self):
		return self.username