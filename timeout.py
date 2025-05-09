from dotenv import dotenv_values


config = dotenv_values(".env")
import time

TIMEOUT_LIMIT = float(config["TIMEOUT_LIMIT"]) # Timeout limit in seconds

def get_current_time():
	"""
	Get the current time in seconds since the epoch.
	"""
	return float(time.time())

def is_timeout(start_time):
	"""
	Check if the time since start_time exceeds the TIMEOUT_LIMIT.
	"""
	print("Checking timeout...", start_time, get_current_time(), TIMEOUT_LIMIT)
	return (get_current_time() - start_time) > TIMEOUT_LIMIT

def remaining_time(start_time):
	"""
	Get the remaining time before timeout.
	"""
	return TIMEOUT_LIMIT - (get_current_time() - start_time)


TIMEOUT_RETURN = {
	"answers": ["Timeout"],
	"idx": [],
	"explanation": ["Timeout"]
}