from ..rest import Rest
from .base_manager import BaseManager
from ..structures.comment import Comment

class CommentManager(BaseManager):
	__track = None
	__load_more = True
	def __init__(self, parent, client):
		super().__init__(client)
		self.__track = parent

	def delete(self, cid):
		comment = self.cache.get(cid)
		if comment:
			return comment.delete()
		return False

	def flag(self, cid):
		comment = self.cache.get(cid)
		if comment:
			return comment.flag()
		return False

	def load_more(self, pages=1):
		pages = int(pages)
		comments = []
		if not self.__load_more:
			return comments

		while pages > 0:
			pages -= 1
			if not self.cache:
				break

			# Get the "last" comment by sorted ID (or however you define order)
			last_comment = next(reversed(self.cache.values()))

			data = Rest.post(f'track_comments/load_more/{last_comment.id}')
			new_comments = [Comment(c, self.__track) for c in data.get('track_comments', [])]

			for c in new_comments:
				self.cache[c.id] = c

			comments.extend(new_comments)

			if not data.get('track_comments_load_more'):
				self.__load_more = False
				break

		return comments

	def post(self, msg):
		return Rest.post('track_comments/post', data={
			't_id': self.__track.id,
			'msg': str(msg)
		})