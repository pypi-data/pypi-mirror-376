from ..rest import Rest
from .base_structure import BaseStructure

class Comment(BaseStructure):
	track = None
	def __init__(self, data={}, track=None):
		if track:
			self.track = track
		comment = data.get('comment') or data
		self.deletable = comment.get('can_delete')
		self.id = comment.get('id')
		self.flagged = comment.get('flagged')
		self.msg = comment.get('msg')
		self.time = comment.get('time')
		if 'user' in data:
			user = data.get('user')
			self.author = {
				'avatar': user.get('img_url_small'),
				'displayName': user.get('d_name'),
				'username': user.get('u_name')
			}

	def delete(self):
		if not deletable:
			raise Exception("Cannot delete a comment which you did not post!")

		return bool(Rest.get(f'track_comments/delete/{self.track.id}/' + str(self.id)))

	def flag(self):
		return bool(Rest.get(f'track_comments/flag/{self.track.id}/' + str(self.id)))

	def reply(self, msg):
		return bool(Rest.post('track_comments/post', data = {
			't_id': self.track.id,
			'msg': str(msg)
		}))