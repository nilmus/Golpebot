import datetime
from Utils.database_functions import *

def has_enough_time_passed(last_time : str, hours=0, minutes=0):
    '''Used e.g. for spy, heal, respawn, last_redeemed
    Last time is a string containing the last time that action was performed
    Hours/minutes is the time interval since last (e.g. 15mins for spy)
    
    Returns True if enough time has passed
    Otherwise, returns how much time is left, as a dictionary of hours, minutes, seconds'''
    # Handle the case where last_time is None
    if not last_time:
        return True
    # Use the datetime module to 1. convert it from string to date
    time_of_last_action = datetime.datetime.strptime(last_time, "%d/%m/%Y %H:%M")
    # And 2. add the time interval
    time_of_next_action = time_of_last_action + datetime.timedelta(hours=hours, minutes=minutes)
    # And 3. create present datetime object
    present = datetime.datetime.now()
    # Now do the check
    if present < time_of_next_action:      # if the present moment comes before the time when action can be re-attempted
        hours_left, remainder = divmod((time_of_next_action-present).seconds, 3600)     # divmod returns a tuple of 1. result of division 2. remainder
        minutes_left, seconds_left = divmod(remainder, 60)
        return {"hours" : hours_left, "minutes" : minutes_left, "seconds" : seconds_left}
    elif present >= time_of_next_action:    # if the present moment comes after the time when action can be re-attempted
        return True