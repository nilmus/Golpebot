import telebot
from Utils.database_functions import *
from Utils.telebot_init import bot
from Utils.logging_init import *
from Game_functions.golpe_functions import *

# Decorator to ignore dead users
def ignore_dead_users(func):
    def wrapper(message):
        conn, c = prep_database()
        c.execute("SELECT is_alive FROM users WHERE user_id = %s", (message.from_user.id,))
        is_alive = c.fetchone()[0]
        conn.close()
        if not is_alive:
            bot.send_message(message.from_user.id, "Non puoi eseguire quest'azione perchè sei morto. \nPer provare a respawnare, manda /respawn")
        else:
            func(message)
    return wrapper





# Decorator to ignore messages from groups
def ignore_group_messages(func):
    def wrapper(message):
        if message.chat.type == 'private':
            # Execute the original function only for private chats
            return func(message)
        else:
            bot.reply_to(message, "Per usare questa funzione, mandami il comando in privato, qui: @golpegamebot")
    return wrapper




# Decorator to make sure only team admins can access certain functions (i.e. only the team's menu, for now)
def check_team_admin(func):
    def wrapper(message):
        user_id = message.from_user.id
        conn, c = prep_database()
        c.execute("SELECT team_role, team FROM users WHERE user_id = %s", (user_id,))
        team_role, team = c.fetchone()
        conn.close()
        if team_role in ["leader", "politico"]:
            # Execute the original function only if user is a team admin
            return func(message, team_role, team)
        else:
            bot.reply_to(message, "Per usare questa funzione, devi essere un politico del team")
    return wrapper









# Decorator to check whether a golpe is happening
def is_golpe_happening(func):
    '''
    messo prima di Attack
    prende il team del player, e controlla nella table "teams" se quel team ha lo status "golpante"
    se non è così, fa l'attacco normale. altrimenti fa l'attacco normale ma aggiunge alla fine un controllo sullo stato del golpe
    cioè controlla se hai ammazzato qualcuno e se questa kill porta a raggiungere l'obiettivo del golpe (cioè uccidere il leader o il 50%+1 dei politici del team regnante)
    '''
    def wrapper(message):
        # Execute the original function, and assign its return ("survived" or "killed") to a variable
        outcome = func(message)
        # If anything other than a kill, don't bother going on
        if outcome != "killed":
            return
        # Check if user team is golpante
        status = retrieve_team_status(message)
        # If it's not golping, ignore. Otherwise, apply conditions
        if status != "golpante":
            return
        else:
            golpe_won = golpe_check()
            golpe_messages_after_attack(golpe_won, message)
            if golpe_won:
                golpe_consequences(True)
    return wrapper










'''
# Decorator for logging
def log_entry_and_exit(func):
    def wrapper(message):
        # Log entry into function - first must distinguish text messages from inline keyboards
        if type(message) is telebot.types.Message:
            user_link = get_user_link(message.from_user.id)
            telegram_logger.info(f"User {user_link} - {message.text}  -  inizio {func.__name__}")
        elif type(message) is telebot.types.CallbackQuery:
            pass    #otherwise it's too many logs
        # Execute function and retrieve output
        output = func(message)
        # Log exit from function, but only if function returns something
        if output:
            user_link = get_user_link(message.from_user.id)
            telegram_logger.info(f"User {user_link} - fine {func.__name__}: \n{output}")
    return wrapper
'''