from math import floor

def t2t(ticks):
	t = int(ticks) / 30 * 1e3
	e = floor(t / 6e4)
	return e + ':' + str(round(t % 6e4 / 1e3, 2)).zfill(5)