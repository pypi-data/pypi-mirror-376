from ..rest import Rest
from .base_manager import BaseManager
from ..structures.notification import Notification

class NotificationManager(BaseManager):
	def fetch(self, *args, **kwargs):
		options = kwargs.get('options', {})
		if not options and args:
			arg0 = args[0]
			if isinstance(arg0, dict):
				options = arg0.get('options', arg0)

		if not options.get('force') and args:
			try:
				id = int(args[0])
				if id in self.cache:
					return self.cache[id]
			except (ValueError, TypeError):
				pass

		resp = Rest.get('notifications', True)
		notification_days = resp.get('notification_days') or []

		entries = []
		if notification_days and 'notifications' in notification_days[0]:
			notif_list = notification_days[0]['notifications']
			entries = [Notification(data) for data in notif_list]

			for entry in entries:
				self.cache.set(entry.timestamp, entry)

		return entries