import requests
from .request_handler import Rest
from ..structures.comment import Comment
from ..structures.race import Race
from ..structures.track import Track
from ..structures.user import User

def get_author_leaderboard():
	return Rest.get("leaderboards/player/lifetime")

def get_category(category):
	return Rest.get(category)

def get_featured_ghosts():
	return requests.get("https://raw.githubusercontent.com/freeridercommunity/featured-ghosts/master/data.json")

def get_player_leaderboard():
	return Rest.get("leaderboards/player/lifetime")

def get_race(track_id, username):
	return Race(Rest.get(f"t/{int(track_id)}/r/{username}"))

def get_random_track(token=None):
	return Track(Rest.get("random/track", token=token))

def get_track(tid):
	tid = int(tid)
	if tid < 1001:
		raise Exception("No tracks exist with an id less than 1001!")

	return Track(Rest.get("t/" + str(tid)))

def get_track_comments(track_id, comment_id=0):
	return Comment(Rest.get(f"track_comments/load_more/{track_id}/{comment_id}"))

def get_track_leaderboard(tid):
	tid = int(tid)
	if tid < 1001:
		raise Exception("No tracks exist with an id less than 1001!")

	return Rest.post("track_api/load_leaderboard", data = {
		't_id': tid
	})

def get_user(uid):
	if isinstance(uid, int):
		uid = Rest.post("friends/remove_friend", False, data = {
			'u_id': uid
		}).get('msg')[25:-31]

	return User(Rest.get("u/" + str(uid)))