from ..rest import Rest
from .base_manager import BaseManager
from ..structures.track import Track

class TrackManager(BaseManager):
	def fetch(self, id, options = {}, **kwargs):
		id = str(id)
		options = kwargs.get('options') or options or {}
		if not options.get('force') and self.cache.has(id):
			return self.cache.get(id)

		entry = Rest.get('t/' + id)
		if entry:
			entry = Track(entry)
			self.cache.set(id.lower(), entry)

		return entry

	def challenge(self, users, m, track):
		return Rest.post('challenge/send/', data={
			'users': ','.join(users)
		})

	def comment(self):
		raise("Not implemented")
		# return Rest.post('track_comments/post/')

	def lookup(self, query):
		response = Rest.post('search/t/' + query)
		if response:
			# maybe cache these results
			return [Track(entry) for entry in response.get('tracks')]

		return []

	def flag(self, tid):
		return bool(Rest.get('track_api/flag/' + str(tid), True))

	def rate(self, t_id, vote):
		return Rest.post('track_api/vote/', data={
			't_id': t_id,
			'vote': vote
		})

	def add_to_daily(self, tid, lives = 30, refill_cost = 10, gems = 500):
		return Rest.post('moderator/add_track_of_the_day', True, data={
			't_id': tid,
			'lives': lives,
			'rfll_cst': refill_cost,
			'gems': gems
		})

	def remove_from_daily(self, tid):
		return Rest.post('admin/removeTrackOfTheDay', True, data={
			't_id': self.id,
			'd_ts': None
		})

	def feature(self, tid):
		return Rest.post(f'track_api/feature_track/{str(tid)}/1', True)

	def unfeature(self, tid):
		return Rest.post(f'track_api/feature_track/{str(tid)}/0', True)

	def hide(self, tid):
		# if this.client.user.admin:
		# 	return Rest.post('admin/hide_track', True, data={'track_id': tid})
		return Rest.post('moderator/hide_track/' + str(tid), True)

	def unhide(self, tid):
		return Rest.post('moderator/unhide_track/' + str(tid), True)

	def hide_as_admin(self, tid):
		return Rest.post('admin/hide_track', True, data={'track_id': tid})