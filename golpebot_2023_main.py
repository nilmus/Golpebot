import telebot
import logging
import json
import random
import datetime
import time

import http.server
import socketserver
import threading
import requests

from Utils.database_functions import *
from Utils.decorators import *
from Utils.telebot_init import bot
from Utils.logging_init import *
from Utils.time_functions import *
from Utils.chat_functions import *
from Utils.keyboard_functions import *
from Game_functions.golpe_functions import *
from Game_functions.attack_functions import *
from Game_functions.spy_functions import *
from Game_functions.transactions_functions import *
from Game_functions.heal_functions import *
from Game_functions.merchant_functions import *




## The following are some variables that need to be global, to work across functions
# Dictionary to store user states
user_states = {}
#REGISTRATION: Dictionary to store user team (while allocating; whereas permanent storage is in the database)
user_team_allocation = {}
#REGISTRATION: Dictionary to store user skills (while allocating; whereas permanent storage is in the database)
user_skill_allocation = {}
#MENU-ZAINO: Dictionary to store item (while using; whereas permanent storage is in the database)
user_using_item = {}
#LAVORO: Dictionary to store job chosen while finding job
user_choosing_job = {}

# The following are global variables so that if I want to change any, I only have to change it here and not in several places all over the code
hours_to_respawn = 12
hours_golpe = 1
hours_elections = 2
minutes_between_spy = 15
minutes_between_heal = 30
# The following variables set the standard for what a high skill-points should be. I should update it if the game picks on to reflect the improving players.
good_luck = 100
good_intelligence = 100
# My telegram ID
admin_id = 213495775
# GOLPECITY group telegram ID
group_id = -1001117818382
#group_id = admin_id #testing


# Load the items JSON file
with open('JSONs/items.json', 'r') as file:
    items = json.load(file)["items"]

# Load the arms JSON file
with open('JSONs/arms.json', 'r') as file:
    arms = json.load(file)["arms"]

# Load the jobs JSON file
with open('JSONs/jobs.json', 'r') as file:
    jobs = json.load(file)["jobs"]





#########
# START #
#########
@bot.message_handler(commands=['start', 'help'])
@ignore_group_messages
def send_welcome(message):
    user_exists = is_user_registered(message)
    if user_exists:
        answer = '''Hai bisogno di aiuto? Prova con questi:
- [Intro](https://telegra.ph/GOLPE-12-12-2)
- [Team](https://telegra.ph/GOLPE---I-team-12-12)
- [Soldi](https://telegra.ph/GOLPE---I-soldi-12-12)
- [Punti abilita](https://telegra.ph/GOLPE---I-punti-abilit%C3%A0-12-12)
- [Oggetti e armi](https://telegra.ph/GOLPE---oggetti-e-armi-12-12)
- [GOLPE!](https://telegra.ph/GOLPE---GOLPE-12-12)
        '''
        bot.reply_to(message, answer, parse_mode='Markdown')
        telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} ha mandato /start")
    if not user_exists:
        answer = "Benvenuto! Sei pronto a <b>GOLPARE?</b> \nPremi /registrazione per iniziare!"
        bot.reply_to(message, answer, parse_mode='HTML')
        user_link = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
        telegram_logger.info(f"Nuovo utente {user_link} ha mandato /start")
    return answer




















########
# INFO #
########
@bot.message_handler(commands=['info'])
def info(message):
    # Retrieve which team is regnante and which are not
    conn, c = prep_database()
    c.execute("SELECT team FROM teams WHERE status = 'regnante'")
    reigning_team = c.fetchone()[0]
    c.execute("SELECT team FROM teams WHERE status != 'regnante'")
    not_reigning_team_1 = c.fetchone()[0]
    not_reigning_team_2 = c.fetchone()[0]
    # Retrieve number of members of each team
    c.execute("SELECT username FROM users WHERE team = 'ROSSO'")
    number_rosso = len(c.fetchall())
    c.execute("SELECT username FROM users WHERE team = 'BLU'")
    number_blu = len(c.fetchall())
    c.execute("SELECT username FROM users WHERE team = 'NERO'")
    number_nero = len(c.fetchall())
    # Send message
    text = f'''<b>Team al governo:</b> {reigning_team}

Numero di membri:
- team ROSSO: {number_rosso}
- team BLU: {number_blu}
- team NERO: {number_nero}'''
    bot.reply_to(message, text, parse_mode='HTML')
    telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /info")



















# per gli altri che leggono: la registrazione segue un paradigma (gli user_states) che ho abbandonato e cambiato nelle altre funzioni
# qui lo lascio perchè cmq funziona e il testing è più difficile per la registrazione
# le altre funzioni così sono il menu personale e il lavoro, che invece potrei portare al nuovo paradigma in futuro
#################
# REGISTRAZIONE #
#################
# Percorso: registration_starter ->
# -> team_selection -> handle_inline_callback (state="waiting_for_team_choice") -> process_team_selection ->
# -> allocate_skill_points_starter -> handle_inline_callback (state="waiting_for_skill_points_allocation") -> process_skill_points_allocation
# -> registration_finalizer
@bot.message_handler(commands=['registrazione'])
@ignore_group_messages
def registration_starter(message):
    # Get the user's telegram ID and check if it's already registered (see the same thing done in the send_welcome function for more detail)
    user_telegram_id = message.from_user.id
    conn, c = prep_database()
    c.execute('SELECT * FROM users WHERE user_id = %s', (user_telegram_id,))
    user_exists = c.fetchone()
    conn.close()
    if user_exists != None:
        answer = "Bro sei già dentro!!!"
        bot.reply_to(message, answer)
    if user_exists == None:
        user_link = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
        telegram_logger.info(f"Nuovo utente {user_link} ha mandato /registrazione")
        # refer to Team choice
        team_selection(message)
        # The general organization is: every new message from the user is a new step; so, instead of logical steps, it's dictated by user message. I couldn't get it to work otherwise

def team_selection(message):
    # Create an instance of an inline keyboard, and add buttons
    team_inline_keyboard = telebot.types.InlineKeyboardMarkup()
    team_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='Team Rosso', callback_data='ROSSO'))
    team_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='Team Blu', callback_data='BLU'))
    team_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='Team Nero', callback_data='NERO'))
    # Send the inline keyboard
    bot.send_message(message.from_user.id, "Per prima cosa scegli il tuo <b>team</b>", parse_mode='HTML', reply_markup=team_inline_keyboard)
    # Referral to the specific function for inline buttons is implicit; it's based on states
    user_states[message.from_user.id] = "waiting_for_team_choice"

def process_team_selection(call):
    # Register the selected team (in the global variable; will get written into the database during registration finalizer)
    user_team_allocation[call.from_user.id] = call.data
    # Give feedback
    bot.answer_callback_query(call.id, "Ok!")
    bot.send_message(call.from_user.id , f"Hai scelto il team {user_team_allocation[call.from_user.id]}")
    # Update user state
    user_states.pop(call.from_user.id)
    # Log
    user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"
    telegram_logger.info(f"Nuovo utente {user_link} - in /registrazione - ha scelto il team")
    # Refer to next function
    allocate_skill_points_starter(call)

def allocate_skill_points_starter(call):
    bot.send_message(call.from_user.id , "Adesso puoi distribuire i tuoi 10 <i>punti abilità</i> iniziali come preferisci", parse_mode='HTML')
    # Update user state. This will be useful for the handler of inline buttons
    user_states[call.from_user.id] = "waiting_for_skill_points_allocation"
    # Initialize skill points dictionary.
    user_skill_allocation[call.from_user.id] = {
        'total' : 10,
        'FRZ' : 0,
        'INT' : 0,
        'FOR' : 0
        }
    # Retrieve the inline keyboard and text from the dedicated function
    skills_inline_keyboard = create_inline_keyboard_for_skill_points(call)[0]
    skills_text = create_inline_keyboard_for_skill_points(call)[1]
    # Send the inline keyboard
    bot.send_message(call.from_user.id, skills_text, parse_mode='HTML', reply_markup=skills_inline_keyboard)

# the following is a dedicated function to make it easier to create and update the keyboard
def create_inline_keyboard_for_skill_points(call):
    # Create keyboard skeleton; needed bc the easiest way to format it the way I want, is to have each row be a list
    keyboard_skeleton = []
    # Add buttons (to add the 12 buttons, I could either write 12 lines, or do this)
    skills_buttons = ['FRZ', 'INT', 'FOR']
    points_buttons = ['+5', '+1', '-1', '-5']
    for point in points_buttons:
        row_of_buttons = []
        for skill in skills_buttons:
            row_of_buttons.append(telebot.types.InlineKeyboardButton(text=f'{point} {skill}', callback_data=f'{skill}_{point}'))
        keyboard_skeleton.append(row_of_buttons)
    # And then add the final button
    keyboard_skeleton.append([telebot.types.InlineKeyboardButton(text='Fatto!', callback_data='DONE')])
    # Transform the keyboard skeleton into the real keyboard
    skills_inline_keyboard = telebot.types.InlineKeyboardMarkup(keyboard_skeleton)
    # Text to accompany the inline keyboard; made separate for 1. readability 2. updateability
    skills_text = f'''<b><i>SU COSA PUNTERAI?</i></b>
<b>FORZA</b>(FRZ): Aiuta nel <i>combattimento</i>
<b>INTELLIGENZA</b>(INT): Aiuta nel <i>guadagno</i>
<b>FORTUNA</b>(FRT): Aiuta nella <i>fortuna</i>
\n<b>Attualmente hai scelto:</b>
Forza: {user_skill_allocation[call.from_user.id]['FRZ']} punti
Intelligenza: {user_skill_allocation[call.from_user.id]['INT']} punti
Fortuna: {user_skill_allocation[call.from_user.id]['FOR']} punti
\n<b>Punti rimanenti</b>: {user_skill_allocation[call.from_user.id]['total']}'''
    return [skills_inline_keyboard, skills_text]

def process_skill_points_allocation(call):
    # Every time a button on the skill keyboard is pressed, it goes to this function
    # First it checks if the button was Fatto or any other
    # Second it checks if the operation is valid (e.g. user isn't trying to get more points than 10)
    # Third it goes through with the processing
    
    if call.data == 'DONE':
        # If all points were assigned
        if user_skill_allocation[call.from_user.id]['total'] == 0:
            # Give feedback
            bot.answer_callback_query(call.id, "Ok!")
            # Remove waiting state
            user_states.pop(call.from_user.id)
            # Refer to registration_finalizer
            registration_finalizer(call)
            # Log
            user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"
            telegram_logger.info(f"Nuovo utente {user_link} - in /registrazione - ha assegnato i punti abilità")
        # If there's still points to be assigned
        else:
            # warning
            bot.answer_callback_query(call.id, "Hai ancora dei punti da assegnare!", show_alert=True)
    
    # I still chose to check that it begins with FRZ,INT,FOR, to avoid too broad else statements
    elif call.data.split('_')[0] == 'FRZ' or 'INT' or 'FOR':
        # Check hypothetical balance after transaction
        points_balance = user_skill_allocation[call.from_user.id]['total'] - int(call.data.split('_')[1])
        # If user does not have enough remaining points
        if points_balance < 0:
            # warning
            bot.answer_callback_query(call.id, "Non hai abbastanza punti! \nSei hai finito, premi su Fatto", show_alert=True)
            # Log
            user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"
            telegram_logger.info(f"Nuovo utente {user_link} - in /registrazione - ha provato a mettersi più di 10 punti")
        # If user pressed -1 or -5 and are trying to get below zero (negative score)
        elif points_balance > 10:
            # warning
            bot.answer_callback_query(call.id, "Non puoi avere punteggio negativo! Ma ce la fai?")
            # Log
            user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"
            telegram_logger.info(f"Nuovo utente {user_link} - in /registrazione - ha provato ad avere un punteggio negativo")
        ## If user has enough remaining points
        elif points_balance >= 0 and points_balance <= 10:
            # Update skills allocation dictionary
            skill = call.data.split('_')[0]
            point = int(call.data.split('_')[1])
            user_skill_allocation[call.from_user.id][skill] += point
            user_skill_allocation[call.from_user.id]['total'] -= point
            # Give feedback
            bot.answer_callback_query(call.id, "Ok!")
            # Ask the dedicated function to re-generate the text and keyboard
            skills_inline_keyboard = create_inline_keyboard_for_skill_points(call)[0]
            skills_text = create_inline_keyboard_for_skill_points(call)[1]
            # Update the inline keyboard (does so by retrieving the message ID from the call)
            bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=skills_text, parse_mode='HTML', reply_markup=skills_inline_keyboard)


def registration_finalizer(call):
    # Get the user's telegram ID
    user_telegram_id = call.from_user.id
    # Get the user's telegram username
    user_telegram_username = call.from_user.username
    # Get the team and skills (a few lines more, yes, but it improves readability)
    team = user_team_allocation[call.from_user.id]
    forza = user_skill_allocation[call.from_user.id]['FRZ']
    intelligenza = user_skill_allocation[call.from_user.id]['INT']
    fortuna = user_skill_allocation[call.from_user.id]['FOR']
    # Prep things before writing into database
    conn, c = prep_database()
    # Write into database
    c.execute('''
                INSERT INTO users(user_id, username, team, playing_since, forza, intelligenza, fortuna, tg_name)
                VALUES(%s,%s,%s,TO_CHAR(NOW(), 'DD/MM/YYYY'),%s,%s,%s,%s)''',
                (user_telegram_id, user_telegram_username, team, forza, intelligenza, fortuna, call.from_user.first_name)
                )
    conn.commit()
    conn.close()
    bot.send_message(call.from_user.id, "Fatto! Sei dentro! \n\nPer stampare la tua carta d'identità, basta mandare /idcard \n\nPer più informazioni sul gioco, manda /help")
    time.sleep(2)
    group_invite_link = bot.create_chat_invite_link(group_id, member_limit=1)
    group_invite_link = group_invite_link.invite_link
    bot.send_message(call.from_user.id, f"Non dimenticare di entrare nella città virtuale! \n {group_invite_link}")
    # Reset the global variables
    user_team_allocation.pop(call.from_user.id)
    user_skill_allocation.pop(call.from_user.id)
    # Notify me in private chat that there's a new user
    user_link = get_user_link(call.from_user.id)
    bot.send_message(admin_id, f"Nuovo utente! \n{user_link}")










@bot.message_handler(commands=['database'])
def log_database(message):
    # check that it's me first
    if message.from_user.id != admin_id:
        bot.reply_to(message, 'Stanotte alle 3 ti taglierò la gola nel sonno')
        telegram_logger.warning(f"L'UTENTE {get_user_link(message.from_user.id)} HA MANDATO /database")
        return
    # Read into database
    conn, c = prep_database()
    c.execute('SELECT * FROM users')
    rows = c.fetchall()
    columns = [description[0] for description in c.description]
    conn.close()
    text = "\n".join(str(row) for row in rows)
    telegram_logger.info(f"DATABASE UTENTI \n{columns} \n{text}") # this ordeal is needed to print each user on a new line
    bot.reply_to(message, "Fatto, capo")
            




















####################
# CARTA D'IDENTITA #
####################
@bot.message_handler(commands=['idcard'])
def id_card(message):
    # Get user ID and username
    user_telegram_id = message.from_user.id
    user_link = get_user_link(user_telegram_id)
    # Prep database
    conn, c = prep_database()
    # Read database
    c.execute('SELECT team, playing_since FROM users WHERE user_id = %s', (user_telegram_id,))
    fetched = c.fetchone()
    # Before going on, this is the right time to check that user is registered
    if not fetched:
        bot.reply_to(message, "Ma non sei registrato! \nSu, premi qua /registrazione")
        telegram_logger.info(f"Utente {message.from_user.first_name} - fine /idcard (non era registrato)")
    elif fetched:
        user_team = fetched[0]
        user_registration_date = fetched[1]
        # Prima di controllare il lavoro, controlla se ha un team role
        c.execute("SELECT team_role FROM users WHERE team_role != 'nullità' AND user_id = %s", (user_telegram_id,))
        team_role = c.fetchone()
        if team_role:
            user_job = f"{team_role[0]} del team {user_team}"
        else:
            c.execute("SELECT job_name FROM job WHERE user_id = %s", (user_telegram_id,))
            user_job = c.fetchone()
            if user_job:
                user_job = user_job[0]
            else:
                user_job = "disoccupato"
        text_id_card = f'''
<b><u>Carta d'identità del cittadino</u></b> {user_link}
\n<b>Team:</b> {user_team}
<b>Lavoro:</b> {user_job}
<b>Giocatore dal:</b> {user_registration_date}
'''
        bot.reply_to(message, text_id_card, parse_mode='HTML')
        telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /idcard - {text_id_card}")
        conn.close()



















#uguale come sopra per /registrazione; non penso lo cambierò a breve
##################
# MENU PERSONALE #
##################
# Percorso: personal_menu_starter -> handle_inline_callback -> personal_menu (inline handler) -> depends! specific function for specific parts of the menu!
# In generale, per passare da una funzione all'altra potrebbero servire: user_states, situation
@bot.message_handler(commands=['menu'])
@ignore_group_messages
def personal_menu_starter(message):
    # Update state
    user_states[message.from_user.id] = "browsing_menu"
    # Retrieve the inline keyboard and text from the dedicated function
    # Pass no argument so that "call" gets defaulted as zero and the function knows it comes from here (instead of from the inline handler)
    menu_text, menu_inline_keyboard = create_inline_keyboards_for_personal_menu()
    # Send the inline keyboard
    bot.send_message(message.from_user.id, menu_text, parse_mode='HTML', reply_markup=menu_inline_keyboard)
    telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - inizio /menu")
    # Done. From now on, it's the inline handler's job

# This is the dedicated function that will be referred to by the handle_inline_callback
def process_personal_menu(call):
    # Prep database
    conn, c = prep_database()

    if call.data == 'zaino':
        # Read database
        c.execute('SELECT item_name, quantity FROM inventory WHERE user_id = %s', (call.from_user.id,))
        fetched = c.fetchall()
        # Se lo zaino è vuoto...
        if not fetched:
            # Crea questo parametro che verrà passato alla funzione che crea la inline keyboard
            situation = 'zaino_vuoto'
        # Se lo zaino ha qualcosa...
        elif fetched:
            # Crea questo parametro che verrà passato alla funzione che crea la inline keyboard
            situation = 'zaino_pieno'
        # Cambia lo user state (segnala che utente è a un livello 2 del menu)
        user_states[call.from_user.id] = "browsing_menu_zaino"
        
    elif call.data == 'armeria':
        # Read database
        c.execute('SELECT arm_name, ammo FROM armory WHERE user_id = %s', (call.from_user.id,))
        fetched = c.fetchall()
        ## Se l'armeria è vuota...
        if not fetched:
            # Crea questo parametro che verrà passato alla funzione che crea la inline keyboard
            situation = 'armeria_vuota'
        ## Se ha qualcosa...
        elif fetched:
            # Crea questo parametro che verrà passato alla funzione che crea la inline keyboard
            situation = 'armeria_piena'
        # Cambia lo user state (segnala che utente è a un livello 2 del menu)
        user_states[call.from_user.id] = "browsing_menu_armeria"
    
    elif call.data == 'dati':
        # Read database
        c.execute("SELECT bank, is_alive, hp, time_of_death, forza, intelligenza, fortuna, team_role, team FROM users WHERE user_id = %s", (call.from_user.id,))
        bank, is_alive, hp, time_of_death, forza, intelligenza, fortuna, team_role, team = c.fetchone()
        # Handle the part on alive/hp/tod
        if is_alive:    # this is to simplify text_dati
            salute_text = ["vivo", f"Punti salute : {hp}"]
        elif not is_alive:
            salute_text = ["morto", f"Ora del decesso: {time_of_death}"]
        # Now handle the part on job/role
        if team_role == 'nullità':
            c.execute("SELECT job_name, contract_expiry_date FROM job WHERE user_id = %s", (call.from_user.id,))
            fetched = c.fetchone()
            if fetched in [None, [], ""]:
                job_text = "Lavoro: disoccupato"
            if fetched[0] == 'TEAMROLE':    #this is the edge case where a user has been fired from teamrole, but has not found a private job yet
                job_text = "Lavoro: disoccupato"
            else:
                job_name, contract_expiry_date = fetched
                job_salary, job_frequency = [jobs[job_name]["salary"], jobs[job_name]["frequency_hours"]]
                job_text = f"Lavoro: {job_name} \nStipendio: {job_salary} soldi ogni {job_frequency}h (max {round(job_salary*(24/job_frequency))} soldi/giorno) \nContratto valido fino al: {contract_expiry_date}"
        else:    #i.e. if user has a team role
            c.execute("SELECT salaries->%s FROM teams WHERE team = %s", (team_role, team))
            role_salary = c.fetchone()[0]
            job_text = f"Ruolo nel team: {team_role} \nSalario: {role_salary} soldi ogni 24h"
        # Ok il messaggio ha 3 sezioni: 1. Salute (vivo/morto, hp/tod) 2. Soldi (banca, lavoro) 3. Abilità (int frz for)
        text_dati = f'''<code>Visualizzazione dati @{call.from_user.username}</code>
<u>1. Salute</u>
Attualmente: {salute_text[0]}
{salute_text[1]}
<i>Per recuperare salute, puoi chiedere a un medico, oppure usare degli oggetti.
Per respawnare, puoi mandare /respawn.</i>

<u>2. Soldi</u>
Conto in banca: {bank} soldi
{job_text}
<i>Per lavorare, manda /lavora.
Per trovare lavoro quando scade il contratto, manda /trovalavoro.</i>

<u>3. Abilità</u>
Forza: {forza}
Intelligenza: {intelligenza}
Fortuna: {fortuna}
<i>Per migliorare le tue abilità, puoi usare degli oggetti.</i>
'''
        inline_keyboard = {"<- indietro" : {"callback_data" : "indietro"}}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard)
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_dati, parse_mode='HTML', reply_markup=inline_keyboard)
        # Cambia lo user state (segnala che utente è a un livello 2 del menu)
        user_states[call.from_user.id] = "browsing_menu_armeria" #sic, bc it's just "indietro" so it works
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /menu - \n\n{text_dati}")
        return
    elif call.data == 'chiudi':
        # Edit message
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text="Menu chiuso.")
        # Update user state
        user_states.pop(call.from_user.id)
        return
    
    # (Il seguente è un tronco comune valido sia per zaino che per armeria; mentre non per "chiudi" perchè quell'ELIF include un return che termina la funzione)
    # Qui è dove viene passato il parametro alla funzione che crea la inline keyboard
    menu_text, menu_inline_keyboard = create_inline_keyboards_for_personal_menu(call, situation, fetched)
    # Edita il messaggio (serve distinguere zaino vs armeria perchè 1. HTML vs Markdown, e 2. uno ha la inline keyboard e uno no)
    bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=menu_text , parse_mode='HTML', reply_markup=menu_inline_keyboard)
    # Se zaino:   A questo punto, la prossima call verrà gestita dall'inline handler, che dato che è cambiato lo user_state, la manderà a process_personal_menu_zaino o a process_personal_menu_armeria

    # Close database
    conn.close()
    # Log
    return situation

# A function to handle the second and third layer of the personal menu: menu_zaino e menu_zaino_usaoggetti
def process_personal_menu_zaino(call):
    # The first IF understands which layer we're in
    if user_states[call.from_user.id] == 'browsing_menu_zaino':
        # The possible calls are 1. "indietro" 2. one of the items
        if call.data == 'indietro':
            # Cambia lo user state (segnala che utente è tornato al livello 1 del menu)
            user_states[call.from_user.id] = "browsing_menu"
            # Edita il messaggio
            # Calling the create_inline_keyboards_for_personal_menu function without arguments yields the initial menu
            # Used list unpacking syntax to only call the function once
            menu_text, menu_inline_keyboard = create_inline_keyboards_for_personal_menu()
            bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=menu_text , parse_mode='HTML', reply_markup=menu_inline_keyboard)
        else:
            # Pass this situation to the keyboard creator function
            situation = 'using_items'
            menu_text, menu_inline_keyboard = create_inline_keyboards_for_personal_menu(call, situation)
            # Edit the message
            bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=menu_text , parse_mode='HTML', reply_markup=menu_inline_keyboard)
            # Edit user_states, so upon next call, the next half of this function will get executed
            user_states[call.from_user.id] = 'browsing_menu_zaino_usaoggetti'
            # Update user_using_item, so next part know which item is being used
            user_using_item[call.from_user.id] = call.data
    elif user_states[call.from_user.id] == "browsing_menu_zaino_usaoggetti":
        # The possible calls are 1. "SI SI SI" 2. "indietro"
        if call.data == 'indietro':
            # Cambia lo user state (segnala che utente è tornato al livello 1 del menu)
            # Perchè farlo tornare al livello 2 richiederebbe conservare il fetched, cioè i dati sull'inventorio, oppure riaprire il database... non ho voglia
            user_states[call.from_user.id] = "browsing_menu"
            # Edita il messaggio
            # Calling the create_inline_keyboards_for_personal_menu function without arguments yields the initial menu
            # Used list unpacking syntax to only call the function once
            menu_text, menu_inline_keyboard = create_inline_keyboards_for_personal_menu()
            bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=menu_text , parse_mode='HTML', reply_markup=menu_inline_keyboard)
        elif call.data == "sì":
            # Get the item's perk
            item_perk = items[user_using_item[call.from_user.id]]["properties"]
            # Split the perk into what is being upgraded and the amount of the upgrade (by splitting the string at the underscore)
            attribute, base_bonus = item_perk.split('__')
            # In the future I might add items that reset spytime, or other stuff. So, the next IF checks what general type of attribute is being upgraded
            if attribute in ['forza', 'intelligenza', 'fortuna', 'hp']:
                # Update quantity of item in user's inventory (-1)
                ## If new quantity is 0, remove item from inventory! (this has to be done with every function that modifies quantity of items or arms)
                ## Ok I managed this by creating a trigger! So sqlite does all that automatically
                conn, c = prep_database()
                c.execute('''UPDATE inventory
                          SET quantity = quantity -1
                          WHERE user_id = %s AND item_name = %s''',
                          (call.from_user.id, user_using_item[call.from_user.id])
                          )
                # Calculate bonus
                ## Read the user's luck
                c.execute("SELECT fortuna FROM users WHERE user_id = %s", (call.from_user.id,))
                fortuna = c.fetchone()[0]
                ## Delegate to specific function
                bonus = luck_modifier(base_bonus, fortuna, [0.6, 1.4])
                # Apply bonus
                c.execute(f'''UPDATE users
                          SET {attribute} = {attribute} + {bonus}
                          WHERE user_id = %s
                            ''',
                            (call.from_user.id,)
                            )
                # Commit and close database
                conn.commit()
                conn.close()
                # Close menu
                if attribute in ['forza', 'intelligenza', 'fortuna']:     # this text is the only difference between upgrading skills and hp
                    closure_text = f'Abilità <b>{attribute}</b> aumentata di <b>{bonus} punti!</b>\n\nPuoi visualizzare i tuoi nuovi punteggi andando su "Visualizza dati" nel /menu'
                if attribute == 'hp':
                    closure_text = f'<b>Punti salute</b> aumentati di <b>{bonus} punti!</b>\n\nPuoi visualizzare i tuoi nuovi punteggi andando su "Visualizza dati" nel /menu'
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=closure_text, parse_mode='HTML')
            
            elif attribute == 'all':
                # Update quantity of item in user's inventory (-1)
                conn, c = prep_database()
                c.execute('''UPDATE inventory
                          SET quantity = quantity -1
                          WHERE user_id = %s AND item_name = %s''',
                          (call.from_user.id, user_using_item[call.from_user.id])
                          )
                # Calculate bonus
                ## Read the user's luck
                c.execute("SELECT fortuna FROM users WHERE user_id = %s", (call.from_user.id,))
                fortuna = c.fetchone()[0]
                ## Delegate to specific function
                bonus = luck_modifier(base_bonus, fortuna, [0.8, 1.2])    #accept a smaller range of variation than single-attribute objects, bc this affects all 3, so any deviation is x3
                # Apply bonus
                c.execute(f'''UPDATE users
                          SET forza = forza+{bonus}, intelligenza = intelligenza+{bonus}, fortuna = fortuna+{bonus}
                          WHERE user_id = %s
                            ''',
                            (call.from_user.id,)
                            )
                # Commit and close database
                conn.commit()
                conn.close()
                # Close menu
                closure_text = f'<b>Forza, intelligenza, e fortuna</b> aumentate di <b>{bonus} punti!</b>\n\nPuoi visualizzare i tuoi nuovi punteggi andando su "Visualizza dati" nel /menu'
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=closure_text, parse_mode='HTML')
            
            elif base_bonus == "reset":     #così vale per tutti i tipi: timeofspy, timeofheal...
                # Update quantity of item in user's inventory (-1)
                conn, c = prep_database()
                c.execute('''UPDATE inventory
                          SET quantity = quantity -1
                          WHERE user_id = %s AND item_name = %s''',
                          (call.from_user.id, user_using_item[call.from_user.id])
                          )
                # Reset the attribute
                c.execute(f'''UPDATE users
                          SET {attribute} = NULL
                          WHERE user_id = %s
                            ''',
                            (call.from_user.id,)
                            )
                # Commit and close database
                conn.commit()
                conn.close()
                # Close menu
                closure_text = f'<b>Tempo di attesa resettato!</b>'
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=closure_text, parse_mode='HTML')

            # Update user_states
            user_states.pop(call.from_user.id)
            user_using_item.pop(call.from_user.id)
            # Log
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /menu - \n\n{closure_text}")
        
def process_personal_menu_armeria(call):
    # The possible calls are 1. an arm 2. "indietro"
    if call.data == 'indietro':
        # Cambia lo user state (segnala che utente è tornato al livello 1 del menu)
        user_states[call.from_user.id] = "browsing_menu"
        # Edita il messaggio
        # Calling the create_inline_keyboards_for_personal_menu function without arguments yields the initial menu
        menu_text, menu_inline_keyboard = create_inline_keyboards_for_personal_menu()
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=menu_text , parse_mode='HTML', reply_markup=menu_inline_keyboard)
    else:
        # Pass this situation to the keyboard creator function
        situation = 'viewing_arms'
        menu_text, menu_inline_keyboard = create_inline_keyboards_for_personal_menu(call, situation)
        # Edit the message
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=menu_text , parse_mode='HTML', reply_markup=menu_inline_keyboard)
        # Don't edit user_states, so that if "indietro" is pressed on the next level of the menu, it will be handled in the same way as in this level
        return situation

# A dedicated function to make it easier to create and update the keyboards (akin to skill points allocation)
# Parameter 'call' is defaulted to 0 bc this function might get called from personal_menu_starter, which handles a message and not a call
# Getting the 'fetched' as a parameter allows to avoid opening the database another time
def create_inline_keyboards_for_personal_menu(call=0, situation="", fetched=None):
    # Start by just creating an instance of a keyboard; then depending on the circumstance, will add different buttons
    menu_inline_keyboard = telebot.types.InlineKeyboardMarkup()
    # If reference was from the menu starter
    if call == 0:
        # This is the initial text
        menu_text = "Cosa desideri fare?"
        # Build the initial keyboard
        menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='Apri zaino', callback_data='zaino'))
        menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='Apri armeria', callback_data='armeria'))
        menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='Visualizza dati', callback_data='dati'))
        menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='Chiudi menu', callback_data='chiudi'))
    ## If reference was from inline handler
    if call != 0:
        if situation == 'zaino_vuoto':
            menu_text = "<i>Sei un nullatenente!</i> \nPuoi comprare oggetti dal /mercante, o da altri giocatori"
            menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='<- indietro', callback_data='indietro'))
        if situation == 'armeria_vuota':
            menu_text = "<i>Marescià, non tengo armi!</i> \nPuoi comprare armi dal /mercante, o da altri giocatori"
            menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='<- indietro', callback_data='indietro'))
        if situation == 'zaino_pieno':
            for item in fetched:
                 # What is fetched is a list of rows, where each row is a tuple of item_name and quantity
                 # so, it has to be unpacked and stringified (I used tuple unpacking syntax)
                 item_name, quantity = item
                 menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text=f"{item_name} ({quantity})", callback_data=f"{item_name}"))
            text = '\n'.join(str(item) for item in fetched)
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - contenuto zaino - \n\n{text}")
            # E alla fine aggiungi il tasto indietro
            menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='<- indietro', callback_data='indietro'))
            menu_text = "Seleziona un oggetto per visualizzarlo e decidere se usarlo. \nOppure torna indietro"
        if situation == 'using_items':
            # Message wil be: item description, list price, ask for confirmation (vuoi usarlo?); keyboard = sì, <- indietro
            # Add the text    (remember that items is a global variable that has the items.json file loaded into it)
            item_name = call.data
            item_description = items[item_name]["description"]
            item_price = items[item_name]["list_price"]
            menu_text = f"<b>Oggetto: {item_name}</b> \n\n{item_description} \nValore: {item_price} soldi \n\nVuoi usarlo?"
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - dialogo oggetto - \n\n{menu_text}")
            # Add the buttons
            menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='SI SI SI', callback_data='sì'))
            menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='<- indietro', callback_data='indietro'))
        if situation == 'armeria_piena':
            # Ho provato a fare che manda una lista testuale ma telegram non supporta le tabelle quindi niente, lo faccio inline
            for arm_name, ammo in fetched:
                 # What is fetched is a list of rows, where each row is a tuple of arm_name and ammo
                 # Used tuple unpacking within the FOR statement
                 menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text=f"{arm_name} ({ammo} munizioni)", callback_data=f"{arm_name}"))
            text = '\n'.join(str(arm) for arm in fetched)
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - contenuto armeria - \n\n{text}")
            # E alla fine aggiungi il tasto indietro
            menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='<- indietro', callback_data='indietro'))
            menu_text = f"Ecco i tuoi ferri. \n<u>Qui puoi solo visualizzarli.</u> Se vuoi usarli contro qualcuno, usa /attacco."
        if situation == 'viewing_arms':
            # Message wil be: arm description, stats, list price; keyboard = sì, <- indietro
            # Add the text    (remember that arms is a global variable that has the arms.json file loaded into it)
            arm_name = call.data
            arm_description = arms[arm_name]["description"]
            arm_damage = arms[arm_name]["damage"]
            arm_loudness = arms[arm_name]["loudness"]
            arm_price = arms[arm_name]["list_price"]
            arm_strength_requirement = arms[arm_name]["required_strength"]
            menu_text = f"<b>Arma: {arm_name}</b> \n\n{arm_description} \n\nDanno: {arm_damage} \nRumore: {arm_loudness}/100 \nForza richiesta: {arm_strength_requirement} punti \nValore: {arm_price} soldi \n\nPer usare quest'arma, usa /attacco"
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - dialogo arma - \n\n{menu_text}")
            # Add the button
            menu_inline_keyboard.add(telebot.types.InlineKeyboardButton(text='<- indietro', callback_data='indietro'))
    return [menu_text, menu_inline_keyboard]




















###########
# ATTACCO #
###########
'''
    Step 1: choose who you want to attack
    Step 2: choose the weapon
    Step 3: calculate damage
    Step 4: apply
    Step 5: send messages
'''
@bot.message_handler(commands=['attacco'])
@ignore_dead_users
@ignore_group_messages
def attack_starter(message):
    telegram_logger.info(f"User {get_user_link(message.from_user.id)} - inizio /attacco")
    # Display the first page only
    list_of_pages = create_keyboard_of_users('attack_choose_user')
    text = "<code>Procedura di attacco attivata.</code> \nScegli l'utente che vuoi sparare in testa!"
    display_page_number(list_of_pages, 0, text, message, mode='send')

@bot.callback_query_handler(func=lambda message: message.data.startswith("attack_choose_user"))
def attack_choose_user(call):    #'attack_choose_user {page_number} {data}'
    # Possible situations: 1. changed page of keyboard 2. pressed on target user
    if has_changed_page(call):
        new_page_number = change_page_number(call)
        text = "Scegli l'utente che vuoi attaccare!"
        display_page_number(create_keyboard_of_users('attack_choose_user'), new_page_number, text, call)
    else:
        attack_choose_weapon_starter(call)

def attack_choose_weapon_starter(call):
    list_of_weapons = get_list_of_weapons(call)
    # Check that user has weapons
    if list_of_weapons:
        target_id = retrieve_data(call)
        list_of_pages = create_keyboard_of_weapons('attack_choose_weapon', list_of_weapons, target_id)
        text = "<i>Scegli il ferro</i>"
        display_page_number(list_of_pages, 0, text, call, 1)
    else:
        text = "<i>Ma che fai? Come pensi di aprire un cranio se non hai un'arma?</i> \n\nPassa dal /mercante o chiedi a un altro utente, e riprova"
        bot.edit_message_text(text, call.from_user.id, call.id, parse_mode='HTML')

@bot.callback_query_handler(func=lambda message: message.data.startswith("attack_choose_weapon"))
def attack_choose_weapon(call):
    if has_changed_page(call):
        new_page_number = change_page_number(call)
        text = "Ma quanti ferri tieni?? Scegline uno!"
        display_page_number(create_keyboard_of_users('attack_choose_weapon'), new_page_number, text, call)
    else:
        weapon = retrieve_data(call)
        target_id = call.data.split(' ')[-2]
        if weapon_has_ammo(weapon, call.from_user.id):
            attack_ask_confirmation(call)
        else:
            bot.answer_callback_query(call.id, "Quest'arma è scarica! \n\nCompra delle munizioni dal /mercante, o chiedile al tuo team", show_alert=True)

def attack_ask_confirmation(call):
    target_id = call.data.split(' ')[-3]
    weapon = call.data.split(' ')[-1]
    # Check arm's strength requirement
    if not user_meets_strength_requirement(call, weapon):
        bot.answer_callback_query(call.id, "Non hai abbastanza Forza per usare quest'arma! \n\nProva a usare degli oggetti per potenziarti", show_alert=True)
        return
    # Ask confirmation
    attack_confirmation_keyboard = {
        "SI SI SI VOGLIO IL SANGUE" : {"callback_data" : f"attack_confirmation {target_id} {weapon} sì"},
        "No, la violenza non è mai la soluzione" : {"callback_data" : f"attack_confirmation no"}
    }
    attack_confirmation_keyboard = telebot.util.quick_markup(attack_confirmation_keyboard, row_width=1)
    confirmation_text = f"Stai per attaccare {get_user_link(target_id)} con l'arma <b>{weapon}</b>  \n\n<i>Confermi?</i>"
    bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=confirmation_text, parse_mode='HTML', reply_markup=attack_confirmation_keyboard)

@bot.callback_query_handler(func=lambda message: message.data.startswith("attack_confirmation"))
@is_golpe_happening
def attack_gave_confirmation(call):
    if retrieve_data(call) == 'no':
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text="Bruh. \n\n<code>Procedura di attacco terminata</code>", parse_mode='HTML')
        telegram_logger.info(f"User {get_user_link(call.from_user.id)} - fine /attacco — il bro ha selezionato 'la violenza non è mai la soluzione' ")
    elif retrieve_data(call) == 'sì':
        target_id = call.data.split(' ')[-3]
        weapon = call.data.split(' ')[-2]
        # Retrieve all values needed for calculations
        attacker_strength, attacker_luck, attacker_team_role, weapon_damage, weapon_loudness, target_hp = retrieve_values_to_calculate_attack(call.from_user.id, weapon, target_id)
        # Do calculations
        damage = calculate_damage(attacker_strength, attacker_team_role, weapon_damage)
        mode = calculate_loudness_mode(attacker_luck, weapon_loudness)
        outcome = calculate_attack_outcome(damage, target_hp)
        already_dead = False if retrieve_user_hp(target_id) > 0 else True
        # Apply
        apply_attack(call.from_user.id, target_id, damage, weapon, outcome, already_dead)
        # Send messages and log
        if already_dead:
            text_to_shooter = "Hai sparato un cadavere! Bello spreco di munizioni... la prossima volta usa lo /spionaggio per assicurarti che i tuoi bersagli siano vivi"
            telegram_logger.info(f"User {get_user_link(call.from_user.id)} - fine /attacco — testo al carnefice: \n'{text_to_shooter}'")
            return outcome
        text_to_shooter, text_to_target = attack_send_messages(call, call.from_user.id, target_id, weapon, damage, mode, outcome)
        telegram_logger.info(f"User {get_user_link(call.from_user.id)} - fine /attacco — testo al carnefice: \n'{text_to_shooter}' \n\ntesto alla vittima: \n'{text_to_target}'")
        # The return is useful for the is_golpe_happening decorator
        return outcome




















##############
# SPIONAGGIO #
##############
# (segue la falsa riga di ATTACCO)
'''
    Step 1: choose who you want to spy
    Step 2: calculate success and extent
    Step 3: send messages
'''

@bot.message_handler(commands=['spionaggio'])
@ignore_dead_users
@ignore_group_messages
def spy_starter(message):
    telegram_logger.info(f"User {get_user_link(message.from_user.id)} - inizio /spionaggio")
    # First you should check if 15mins have passed since last attempt
    last_time = retrieve_time_column(message.from_user.id, 'time_of_spy')
    time_check = has_enough_time_passed(last_time, minutes=minutes_between_spy)
    if time_check != True:      # if not enough time has passed
        minutes_left, seconds_left = time_check["minutes"], time_check["seconds"]
        text = f"Puoi tentare uno spionaggio solo una volta ogni {minutes_between_spy} minuti. \nRiprova tra {minutes_left} minuti e {seconds_left} secondi"
        bot.reply_to(message, text)
        telegram_logger.info(f"User {get_user_link(message.from_user.id)} - fine /spionaggio — non era passato abbastanza tempo")
        return
    elif time_check == True:
        # Display the first page only
        list_of_pages = create_keyboard_of_users('spy_choose_user')
        text = "<code>Procedura di spionaggio attivata.</code> \nScegli l'utente a cui vuoi frugare nel cassetto!"
        display_page_number(list_of_pages, 0, text, message, mode='send')

@bot.callback_query_handler(func=lambda message: message.data.startswith("spy_choose_user"))
def spy_choose_user(call):    #'spy_choose_user {page_number} {data}'
    # Possible situations: 1. changed page of keyboard 2. pressed on target user
    if has_changed_page(call):
        new_page_number = change_page_number(call)
        text = "Scegli l'utente che vuoi spiare!"
        display_page_number(create_keyboard_of_users('spy_choose_user'), new_page_number, text, call)
    else:
        spy_calculate_and_apply(call)

def spy_calculate_and_apply(call):
    target_id = retrieve_data(call)
    # Update the time_of_spy
    set_time_column_to_now(call.from_user.id, 'time_of_spy')
    # Retrieve modifiers needed to calculate success and extent
    spier_intelligence, spier_luck, spier_team_role, target_intelligence, target_luck = retrieve_values_to_calculate_spy(call.from_user.id, target_id)
    # Do calculations
    success = calculate_success(spier_luck, spier_team_role, target_luck)
    extent = calculate_extent(spier_intelligence, spier_team_role, target_intelligence)
    # Apply
    outcome = apply_spy(success, extent, target_id)
    # Send messages and log
    text_to_spier, text_to_target = spy_send_messages(outcome, call.from_user.id, target_id, call)
    telegram_logger.info(f"User {get_user_link(call.from_user.id)} - fine /spionaggio — testo alla spia: \n'{text_to_spier}' \n\ntesto allo spiato: \n'{text_to_target}'")


                    

















##########
# LAVORO #
##########

@bot.message_handler(commands=['trovalavoro'])
@ignore_dead_users
@ignore_group_messages
def find_job_starter(message):
    '''
    tu mandi /trovalavoro, lui manda una inline keyboard con tutti i lavori esistenti
    quando clicchi su uno, ti mostra descrizione e chiede conferma
    quando clicchi su conferma, checka se hai abbastanza intelligenza
    '''
    # First of all, check if user has a team role, bc then can't have a private job
    conn, c = prep_database()
    c.execute("SELECT team_role FROM users WHERE user_id = %s", (message.from_user.id,))
    team_role = c.fetchone()[0]
    if team_role != 'nullità':
        bot.reply_to(message, f"<i>Sei un {team_role}.</i> \n\nChi ha un ruolo nel team non può avere un impiego privato. \nPuoi comunque riscuotere il tuo salario statale mandando /lavora \n\nPuoi abbandonare il tuo ruolo mandando /milicenzio", parse_mode='HTML')
        return
    # Check if user is already under a contract
    c.execute("SELECT contract_expiry_date FROM job WHERE user_id = %s", (message.from_user.id,))
    fetched = c.fetchone()
    conn.close()
    if not fetched or fetched == (None,):    #This IF is needed bc contract_expiry_date might be None (if never had a job) or (None,) if just fired from team role
        # Then contract_expiry_date is None; so, assign some value just so it can work I mean man, you see the < statement below
        present = 1
        contract_expiry_date = 0
    else:                            # if contract_expiry_date is not None
        # Use the datetime module to 1. convert it from string to date
        contract_expiry_date = datetime.datetime.strptime(fetched[0], "%d/%m/%Y")
        # And 2. create present datetime object
        present = datetime.datetime.now()
    # Now check
    if present < contract_expiry_date:      # if has a contract and it's not expired yet
        days_left = (contract_expiry_date-present).days
        bot.reply_to(message, f"<i>Hai ancora un contratto in corso di validità</i>. \n\nRiprova tra {days_left} giorni", parse_mode='HTML')
        telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - ha provato /trovalavoro con contratto in corso")
    elif present >= contract_expiry_date:   # if no contract or expired contract
        # Update user state
        user_states[message.from_user.id] = "finding_job"
        # Create and send keyboard
        inline_keyboard = {job_name : {'callback_data': job_name} for job_name in jobs}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
        bot.send_message(chat_id=message.from_user.id, text="Alla buon'ora! \nEcco una lista di lavori disponibili", reply_markup=inline_keyboard)
        telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - inizio /trovalavoro")
        # Now it goes to inline handler and then to process_find_job

def process_find_job(call):
    # Possible situations: 1. pressed on a job 2. pressed "indietro" 3. pressed on confirmation
    
    # 1. pressed on a job
    if user_states[call.from_user.id] == "finding_job":
        # Update user states
        user_states[call.from_user.id] = "finding_job_confirmation"
        user_choosing_job[call.from_user.id] = call.data
        # Retrieve job info
        job_name = call.data
        job_intelligence = jobs[job_name]["required_intelligence"]
        job_salary = jobs[job_name]["salary"]
        job_frequency = jobs[job_name]["frequency_hours"]
        job_contract_duration = jobs[job_name]["contract_duration_days"]
        text = f'''<b><u>{job_name}</u></b> \n
Intelligenza richiesta: {job_intelligence} punti
Stipendio: {job_salary} soldi ogni {job_frequency} ore
(cioè al massimo {int(job_salary*(24/job_frequency))} soldi al giorno)
Durata del contratto: {job_contract_duration} giorni

Vuoi accettare l'offerta di lavoro?
        '''
        # Create and send keyboard
        inline_keyboard = {"$I $I $I" : {'callback_data' : 'sì'}, "<- indietro" : {'callback_data' : 'indietro'}}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text , parse_mode='HTML', reply_markup=inline_keyboard)
    # 2/3. pressed on confirmation/indietro
    elif user_states[call.from_user.id] == "finding_job_confirmation":
        if call.data == "sì":
            # Check intelligence requisite
            ## Retrieve user's intelligence
            conn, c = prep_database()
            c.execute("SELECT intelligenza FROM users WHERE user_id = %s", (call.from_user.id,))
            user_intelligence = c.fetchone()[0]
            ## Retrieve job's intelligence
            job_name = user_choosing_job[call.from_user.id]
            job_intelligence = jobs[job_name]["required_intelligence"]
            ## Do the math
            if user_intelligence >= job_intelligence:
                # Reset user states
                user_states.pop(call.from_user.id)
                user_choosing_job.pop(call.from_user.id)
                # Retrieve contract duration and calculate expiry date
                contract_duration = jobs[job_name]["contract_duration_days"]
                current_date = datetime.datetime.now().date()
                contract_expiry = current_date + datetime.timedelta(days=contract_duration)
                contract_expiry = contract_expiry.strftime("%d/%m/%Y")    # This formats it right
                # Apply to database
                c.execute('''INSERT INTO job (user_id, username, job_name, contract_expiry_date)
                                VALUES (%s,%s,%s,%s)
                                ON CONFLICT (user_id)
                                DO
                                UPDATE SET job_name = %s, contract_expiry_date = %s;''',
                          (call.from_user.id, call.from_user.username, job_name, contract_expiry, job_name, contract_expiry))
                conn.commit()
                # Create text recap
                job_salary = jobs[job_name]["salary"]
                job_frequency = jobs[job_name]["frequency_hours"]
                text_recap = f'''<b>Congratulazioni</b>, sei appena stato assunto come {job_name}! \n
Potrai riscuotere {job_salary} soldi ogni {job_frequency} ore. (Quindi un massimo di {int(job_salary*(24/job_frequency))} soldi al giorno).
Per riscuotere, manda /lavora \n
Il contratto scadrà il {contract_expiry}.
                '''
                # Send message
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_recap, parse_mode="HTML")
                telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - fine /trovalavoro - dialogo: \n\n{text_recap}")
            elif user_intelligence < job_intelligence:
                # Bring up a show-alert
                bot.answer_callback_query(call.id, "Ma sei scemo? Non hai abbastanza punti intelligenza per questo lavoro", show_alert=True)
            # Either way, close connection
            conn.close()
        elif call.data == "indietro":
            # Update user states
            user_states[call.from_user.id] = "finding_job"
            user_choosing_job.pop(call.from_user.id)
            # Recreate and resend jobs keyboard (minus the "alla buon'ora" in the text)
            inline_keyboard = {job_name : {'callback_data': job_name} for job_name in jobs}
            inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
            bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text="Ecco una lista di lavori disponibili", reply_markup=inline_keyboard)
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /trovalavoro - indietro")
            # And it goes back to inline handler and then to process_find_job

@bot.message_handler(commands=['lavora'])
@ignore_dead_users
def work(message):
    # First of all check if user has a team role
    conn, c = prep_database()
    c.execute("SELECT team_role FROM users WHERE user_id = %s", (message.from_user.id,))
    team_role = c.fetchone()[0]
    if team_role != 'nullità': #if user does have a team role
        work_role(message, team_role)     #refer to specialized function
        conn.close()
        return
    # Check if user has a valid contract
    c.execute("SELECT contract_expiry_date FROM job WHERE user_id = %s", (message.from_user.id,))
    try:        #This TRY is needed bc contract_expiry_date might be None
        # Use the datetime module to 1. convert it from string to date object
        contract_expiry_date = datetime.datetime.strptime(c.fetchone()[0], "%d/%m/%Y")
        # And 2. create present datetime object
        present = datetime.datetime.now()
    except TypeError:
        # Then contract_expiry_date is None
        # So, assign some value just so it can work I mean man, you see
        present = 1
        contract_expiry_date = 0
    # Now check
    if present < contract_expiry_date:      # if has a contract and it's not expired yet
        # Retrieve job's info
        c.execute("SELECT job_name FROM job WHERE user_id = %s", (message.from_user.id,))
        job_name = c.fetchone()[0]
        job_salary = jobs[job_name]["salary"]
        job_frequency = jobs[job_name]["frequency_hours"]
        job_description = jobs[job_name]["description"]
        # Retrieve taxation
        c.execute("SELECT taxation FROM teams WHERE status = 'regnante'")
        taxation = c.fetchone()[0]
        # Check if enough time has passed since last redeem
        c.execute("SELECT last_redeemed FROM job WHERE user_id = %s", (message.from_user.id,))
        try:    # for explanations of this TRY, just see the TRY above
            last_redeemed = datetime.datetime.strptime(c.fetchone()[0], "%d/%m/%Y %H:%M")
            next_redeem = last_redeemed + datetime.timedelta(hours=job_frequency)
            present = datetime.datetime.now()
        except TypeError:
            present = 1
            next_redeem = 0
        if present < next_redeem:    # if not enough time has passed since last redeemed salary
            hours_left, remainder = divmod((next_redeem-present).seconds, 3600)
            minutes_left, _ = divmod(remainder, 60)
            bot.send_message(chat_id=message.from_user.id, text=f"<i>Non è passato abbastanza tempo dall'ultima riscossione.</i> \n\nRiprova tra {hours_left} ore e {minutes_left} minuti", parse_mode='HTML')
            telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /lavora - ma non era passato abbastanza tempo")
        elif present > next_redeem:  # if enough time has passed since last redeem
            # Calculate salary after taxation
            tax = round(job_salary * (taxation/100))
            net_salary = job_salary - tax
            # Give salary
            c.execute("UPDATE users SET bank = bank+%s WHERE user_id = %s", (net_salary, message.from_user.id))
            # Give tax to government
            c.execute("UPDATE teams SET bank = bank+%s WHERE status = 'regnante'", (tax,))
            conn.commit()
            # Update last_redeemed
            c.execute("UPDATE job SET last_redeemed = TO_CHAR(NOW(), 'DD/MM/YYYY HH24:MI') WHERE user_id = %s", (message.from_user.id,))
            conn.commit()
            #Send message
            text_redeemed_salary = f"<i>{job_description}</i> \n\nHai riscosso {net_salary} soldi. \n<i>(Salario lordo: {job_salary}\nTassazione: {taxation}%)</i> \n\nPotrai riscuotere di nuovo fra {job_frequency} ore."
            bot.send_message(chat_id=message.from_user.id, text=text_redeemed_salary, parse_mode='HTML')
            telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /lavora - ha riscosso stipendio; dialogo: \n\n{text_redeemed_salary}")
        # Regardless:
        conn.close()
    elif present >= contract_expiry_date:   # if no contract or expired contract
        bot.send_message(chat_id=message.from_user.id, text="Sei un disoccupato! \n\n<i>Per trovare un lavoro manda /trovalavoro</i>", parse_mode='HTML')
        telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /lavora - ma era disoccupato")

# This gets called if they send /lavora but they have a team role
def work_role(message, team_role):
    # Check that enough time has passed since last redeem (for all roles, time is 24h)
    last_time = retrieve_time_column(message.from_user.id, 'last_redeemed', 'job')
    time_check = has_enough_time_passed(last_time, hours=24)
    if time_check != True:
        hours_left = time_check['hours']
        minutes_left = time_check['minutes']
        bot.reply_to(message, f"<i>Non è passato abbastanza tempo dall'ultima riscossione.</i> \nPer i ruoli del team, puoi riscuotere il salario ogni 24h. \n\nRiprova tra {hours_left} ore e {minutes_left} minuti", parse_mode='HTML')
        return
    conn, c = prep_database()
    # Handle the case where they never had a job before and were not in the job table
    if not last_time:
        c.execute("INSERT INTO job (user_id, username, job_name, last_redeemed) VALUES (%s, %s, 'TEAMROLE', TO_CHAR(NOW(), 'DD/MM/YYYY HH24:MI'))", (message.from_user.id, message.from_user.username))
        conn.commit()
    # Update last_redeemed
    c.execute("UPDATE job SET last_redeemed = TO_CHAR(NOW(), 'DD/MM/YYYY HH24:MI') WHERE user_id = %s", (message.from_user.id,))
    # Retrieve team
    c.execute("SELECT team FROM users WHERE user_id = %s", (message.from_user.id,))
    team = c.fetchone()[0]
    # Retrieve role salary and team's bank
    c.execute("SELECT salaries->%s, bank FROM teams WHERE team = %s", (team_role, team))
    role_salary, team_bank = c.fetchone()
    # Try to take money from team bank
    new_team_bank = team_bank - role_salary
    if new_team_bank < 0:
        # Not enough money in the team bank
        text = "Il tuo team non ha abbastanza soldi per pagare gli stipendi! Prova a parlarne con un politico. \n\n...Altrimenti puoi usare /milicenzio per abbandonare il ruolo e poi /trovalavoro per trovare un lavoro privato!"
        bot.reply_to(message, text)
        conn.close()
        telegram_logger.info(text)
        return
    # If there's enough money, give it
    c.execute("UPDATE teams SET bank = %s WHERE team = %s", (new_team_bank, team))
    c.execute("UPDATE users SET bank = users.bank + %s WHERE user_id = %s", (role_salary, message.from_user.id))
    conn.commit()
    conn.close()
    text_salary = f"Hai riscosso il tuo salario di {team_role}: <i>{role_salary} soldi</i> \n\nPotrai riscuotere di nuovo fra 24h"
    bot.reply_to(message, text_salary, parse_mode='HTML')
    telegram_logger.info(text_salary)
    return

@bot.message_handler(commands=['milicenzio'])
@ignore_dead_users
@ignore_group_messages
def i_quit(message):
    # Check that user has a team role (except leader, bc teams must have a leader at all times)
    conn, c = prep_database()
    c.execute("SELECT team_role, team FROM users WHERE user_id = %s", (message.from_user.id,))
    team_role, team = c.fetchone()
    conn.close()
    if team_role == 'nullità':
        text = "Non hai un ruolo nel team. Puoi licenziarti solo da un ruolo, non da un lavoro privato."
        bot.reply_to(message, text)
        return text
    elif team_role == 'leader':
        text = "Il leader non può licenziarsi. Se sei un dittatore e vuoi abdicare, converti la forma di governo in una democrazia e indici delle elezioni tramite /ufficio"
        bot.reply_to(message, text)
        return text
    # Ok, go on
    # Ask confirmation
    inline_keyboard = {
        '$I, VOGLIO I $OLDI' : {'callback_data' : f'milicenzio__sì__{team}__{team_role}'},    #including the team is to notify the team's leader
        'NO, LO STATO PRIMA DI TUTTO' : {'callback_data' : 'milicenzio__no'}
    }
    inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
    bot.send_message(message.from_user.id, f"Sei sicuro di voler rinunciare al ruolo di {team_role}?", reply_markup=inline_keyboard)
    telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /milicenzio")

@bot.callback_query_handler(func=lambda message: message.data.startswith("milicenzio"))
def i_quit_confirmation(call):
    answer = call.data.split('__')[1]
    if answer == 'no':
        text = "Ti piace il posto fisso, eh?"
        bot.edit_message_text(text, call.from_user.id, call.message.message_id)
        return text
    elif answer == 'sì':
        team, team_role = call.data.split('__')[2:]
        # Apply
        conn, c = prep_database()
        c.execute("UPDATE users SET team_role = 'nullità' WHERE user_id = %s", (call.from_user.id,))
        # Retrieve team leader's ID, to send him a message
        c.execute("SELECT user_id FROM users WHERE team_role = 'leader' AND team = %s", (team,))
        leader_id = c.fetchone()[0]
        conn.commit()
        conn.close()
        # Send messages
        text_to_quitter = f"<code>Operazione completata</code> \n\nHai abbandonato il tuo ruolo di {team_role} nel team {team}. \nAdesso sei libero di cercare un impiego privato, con /trovalavoro"
        bot.edit_message_text(text_to_quitter, call.from_user.id, call.message.message_id, parse_mode='HTML')
        bot.send_message(leader_id, f"Un {team_role} del tuo team si è appena licenziato: @{call.from_user.username}")
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - fine /milicenzio - \n\n{text_to_quitter}")




















###########
# RESPAWN #
###########
@bot.message_handler(commands=['respawn'])
def respawn(message):
    # Check if they're alive or dead
    conn, c = prep_database()
    c.execute("SELECT is_alive FROM users WHERE user_id = %s", (message.from_user.id,))
    is_alive = c.fetchone()[0]
    if is_alive:    # if still alive
        # Send message
        bot.send_message(chat_id=message.from_user.id, text="Cosa vuoi respawnare, che sei ancora vivo", parse_mode='HTML')
        telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /respawn - ma era vivo")
        return
    # If dead, check if enough time has passed
    time_of_death = retrieve_time_column(message.from_user.id, 'time_of_death')
    time_check = has_enough_time_passed(time_of_death, hours_to_respawn)
    if time_check != True:      # if not enough time has passed
        hours_left, minutes_left = time_check["hours"], time_check["minutes"]
        text = f"<i>Non puoi ancora respawnare, mancano {hours_left} ore e {minutes_left} minuti</i>"
        bot.reply_to(message, text, parse_mode='HTML')
        telegram_logger.info(f"User {get_user_link(message.from_user.id)} - /respawn — ma non era passato abbastanza tempo")
        return
    elif time_check == True:
        # Apply (revive and restore hp)
        c.execute("UPDATE users SET is_alive = TRUE, hp = 1000 WHERE user_id = %s", (message.from_user.id,))
        conn.commit()
        # Unmute on group chat
        unmute_chat_member(message.from_user.id)
        # Send message
        bot.send_message(chat_id=message.from_user.id, text=f"<code>Operazione completata</code> \n\nSei come nuovo, fai invidia a gesù!", parse_mode='HTML')
        telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /respawn (successo)")
    conn.close()




















############
# MERCANTE #
############
@bot.message_handler(commands=['mercante'])
@ignore_dead_users
@ignore_group_messages
def merchant_starter(message):
    # All'inizio il mercante è sempre aperto, poi introdurrò dei periodi di ON e OFF
    inline_keyboard = merchant_start_keyboard
    inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
    bot.send_message(chat_id=message.from_user.id, text=f"<b>Benvenuto!</b> \nChe cosa vuoi comprare?", parse_mode='HTML', reply_markup=inline_keyboard)
    telegram_logger.info(f"User {get_user_link(message.from_user.id)} - inizio /mercante")

@bot.callback_query_handler(func=lambda message: message.data.startswith("mer0"))
def merchant_restarter(call):
    # Called when "<- indietro" while showing goods
    inline_keyboard = merchant_start_keyboard
    inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
    bot.edit_message_text(f"<b>Va bene, ricominciamo!</b> \nChe cosa vuoi comprare?", call.from_user.id, call.message.message_id, parse_mode='HTML', reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda message: message.data.startswith("mer1"))
def merchant_show_goods(call):
    # they either selected "compra oggetti" or "compra armi" or "compra munizioni"

    category = retrieve_data(call)
    goods = retrieve_merchant_goods(category)

    if not goods:               # if merchant has finished goods of that category
        text_empty = texts_if_empty[category]       #this refers to a dictionary in merchant_functions
        inline_keyboard = {"<- indietro" : {'callback_data' : 'mer0 indietro'}}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard)
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_empty, parse_mode='HTML', reply_markup=inline_keyboard)
        return

    inline_keyboard = {}        # otherwise, create the keyboard
    for item_name, quantity in goods:
        inline_keyboard[f"{item_name} ({quantity})"] = {'callback_data' : f'mer2 {category} {item_name}'}
    inline_keyboard["<- indietro"] = {'callback_data' : 'mer0 indietro'}
    inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
    bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text="Che vuoi comprare?", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda message: message.data.startswith("mer2"))
def merchant_dispatcher(call):
    # they either pressed on an oggetto, or on an arma, or on a munizioni; or on indietro
    # depending on what, we call the right function
    category, item_name = call.data.split(' ')[1:]

    call.data = f"mer3 {category} {item_name} 1"

    if category == 'item' or category == 'ammo':    #then ask how many they want to buy
        merchant_choose_quantity(call)
        telegram_logger.info(f"User {get_user_link(call.from_user.id)} - in /mercante - ha visualizzato oggetto: {item_name}")
    
    elif category == 'arm':                         #then go straight to confirmation (can only have 1 weapon)
        merchant_confirmation(call)
        
    

@bot.callback_query_handler(func=lambda message: message.data.startswith("mer3"))
def merchant_choose_quantity(call):
    category, item_name, current_quantity = call.data.split(' ')[1:4]
    current_quantity = int(current_quantity)

    max_quantity = retrieve_merchant_quantity(item_name)
    keyboard_buttons = [1, 5, 10]
    range_valid_quantity = [1, max_quantity]

    price = retrieve_merchant_price(item_name)
    description = merchant_create_description(item_name, category, price)

    text_pt1 = description
    text_pt2 = "unità"

    done = amount_keyboard_message_sender(call, keyboard_buttons, range_valid_quantity, current_quantity, text_pt1, text_pt2)
    if done:    #i.e. if pressed 'fatto'
        new_call = call.data.replace('mer3', 'mer9', 1)
        call.data = new_call
        merchant_confirmation(call)

def merchant_confirmation(call):
    category, item_name, quantity = call.data.split(' ')[1:4]
    quantity = int(quantity)

    text = merchant_confirmation_text(item_name, category, quantity)
    inline_keyboard = merchant_confirmation_keyboards(item_name, category, quantity)

    bot.edit_message_text(text, call.from_user.id, call.message.message_id, parse_mode='HTML', reply_markup=inline_keyboard)
    telegram_logger.info(f"User {get_user_link(call.from_user.id)} - in /mercante - chiedo conferma: {text}")

@bot.callback_query_handler(func=lambda message: message.data.startswith("mer9"))
def merchant_apply(call):
    answer = call.data.split(' ')[1]
    if answer == 'no':
        merchant_show_goods(call)
        return
    item_name, category, quantity = call.data.split(' ')[2:5]
    quantity = int(quantity)

    #Check they got the money
    price = retrieve_merchant_price(item_name) * quantity
    buyer_id = call.from_user.id
    if not check_if_enough_money(buyer_id, price):
        bot.answer_callback_query(call.id, 'Non hai abbastanza soldi, straccione!', show_alert=True)
        return
    
    #Depends on category
    if category == 'item':
        transfer_item_from_merchant(buyer_id, item_name, quantity, call.from_user.username)
    
    elif category == 'arm':
        try:        # must check they don't already have that weapon
            transfer_weapon_from_merchant(buyer_id, item_name, call.from_user.username)
        except ValueError:
            bot.answer_callback_query(call.id, "Hai già quest'arma! Puoi avere solo un esemplare di ogni arma.", show_alert=True)
            return
    
    elif category == 'ammo':
        # the syntax switch is handled by the merchant function (i.e. from "Munizioni arma" to "arma")
        try:        # must check they do already have that weapon
            transfer_ammo_from_merchant(buyer_id, item_name, quantity)
        except ValueError:
            bot.answer_callback_query(call.id, "Non puoi comprare queste munizioni perchè non possiedi l'arma corrispondente!", show_alert=True)
            return

    #Regardless of category:
    pay_merchant(buyer_id, price)

    #Send messages and Log
    text_to_buyer = merchant_recap_message(item_name, quantity, price)
    bot.edit_message_text(text_to_buyer, call.from_user.id, call.message.message_id, parse_mode='HTML')
    telegram_logger.info(f"User {get_user_link(buyer_id)} - fine /mercante: - \n\ntesto al compratore: \n{text_to_buyer}")




















#########
# VENDI #
#########
@bot.message_handler(commands=['vendi'])
@ignore_group_messages
@ignore_dead_users
def sell_starter(message):
    # 1. Select item/arm/ammo
    inline_keyboard = {
            "Vendi oggetti" : {'callback_data' : 'ven0 oggetti'},
            "Vendi armi" : {'callback_data' : 'ven0 armi'},
            "Vendi munizioni" : {'callback_data' : 'ven0 munizioni'}
        }
    inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
    text_sell = "Per vendere un oggetto o un arma, ti consigliamo di accordarti prima con l'acquirente a parole, e poi usare questa funzione a contrattazione conclusa. \n\nCosa vuoi vendere?"
    bot.send_message(chat_id=message.from_user.id, text=text_sell, parse_mode='HTML', reply_markup=inline_keyboard)
    telegram_logger.info(f"User {get_user_link(message.from_user.id)} - inizio /vendi")

@bot.callback_query_handler(func=lambda message: message.data.startswith("ven0"))    # This is what allows it to be stateless
def sell_select_category_starter(call):
    # 2. Select specific thing
    # they pressed on one of: vendi oggetti, vendi armi, vendi munizioni
    data = retrieve_data(call)

    if data == 'oggetti':
        # Check user has at least one
        list_of_items = get_list_of_items(call.from_user.id)
        if list_of_items:
            # Display the first page only
            list_of_pages = create_keyboard_of_items('ven1_item', list_of_items)
            text = "Quale sostanza vuoi spacciare?"
            display_page_number(list_of_pages, 0, text, call, row_width=1)
        else:
            bot.answer_callback_query(call.id, 'Non hai oggetti!')
    
    elif data == 'armi':
        # Check user has at least one
        list_of_weapons = get_list_of_weapons(call)
        if list_of_weapons:
            # Display the first page only
            list_of_pages = create_keyboard_of_weapons('ven1_weapon', list_of_weapons, omit_ammo=True)
            text = "Quale ferro vuoi vendere?"
            display_page_number(list_of_pages, 0, text, call, row_width=1)
        else:
            bot.answer_callback_query(call.id, 'Non hai armi!')

    elif data == 'munizioni':
        # Check user has at least one
        list_of_weapons = get_list_of_weapons(call)
        if list_of_weapons:
            # Display the first page only
            list_of_pages = create_keyboard_of_weapons('ven1_ammo', list_of_weapons, ammo_mode=True)
            text = "Quale tipo di munizione vuoi vendere?"
            display_page_number(list_of_pages, 0, text, call, row_width=1)
        else:
            bot.answer_callback_query(call.id, 'Non hai munizioni!')

@bot.callback_query_handler(func=lambda message: message.data.startswith("ven1"))
def sell_select_category(call): # 'sell_choose_thing_X page_number thing'
    # Possible situations: 1. changed page of keyboard 2. pressed on target user
    category = call.data.split(' ')[0].split('_')[1]
    if has_changed_page(call):
        new_page_number = change_page_number(call)
        text = "Che vuoi vendere?"
        if category == 'item':
            display_page_number(create_keyboard_of_items('ven1_item', get_list_of_items(call.from_user.id)), new_page_number, text, call, 1)
        elif category == 'weapon':
            display_page_number(create_keyboard_of_weapons('ven1_weapon', get_list_of_weapons(call), omit_ammo=True), new_page_number, text, call, 1)
        elif category == 'ammo':
            display_page_number(create_keyboard_of_weapons('ven1_ammo', get_list_of_weapons(call), ammo_mode=True), new_page_number, text, call, 1)
    else:
        call.data += " 0"           #attach price tag
        new_call = call.data.replace('ven1', 'ven2', 1)
        call.data = new_call
        sell_choose_price(call)

@bot.callback_query_handler(func=lambda message: message.data.startswith("ven2"))
def sell_choose_price(call):
    current_price = int(retrieve_data(call))
    keyboard_buttons = [1, 10, 100, 1000]
    range_valid_price = [0, 10000]
    text_pt1 = "A quanto lo vuoi vendere? \n\nPrezzo:"
    text_pt2 = "soldi"
    done = amount_keyboard_message_sender(call, keyboard_buttons, range_valid_price, current_price, text_pt1, text_pt2)
    if done:    #i.e. if pressed 'fatto'
        new_call = call.data.replace('ven2', 'ven3', 1)
        call.data = new_call
        sell_choose_recipient(call)

@bot.callback_query_handler(func=lambda message: message.data.startswith("ven3"))
def sell_choose_recipient(call):
    if retrieve_data(call) == 'fatto':    #i.e. the first time when it comes directly from sell_choose_price
        # Display the first page only
        list_of_pages = create_keyboard_of_users(call.data, get_list_of_users(exclude_self=call))
        text = "Ultimo passo: seleziona l'acquirente!"
        display_page_number(list_of_pages, 0, text, call)
    else:
        # Possible situations: 1. changed page of keyboard 2. pressed on target user
        if has_changed_page(call):
            new_page_number = change_page_number(call)
            text = "A chi lo vuoi vendere!?"
            display_page_number(create_keyboard_of_users(call.data), new_page_number, text, call)
        else:
            sell_ask_confirmation(call)

def sell_ask_confirmation(call):
    recipient_id = call.data.split(' ')[-1]
    price = call.data.split(' ')[-4]
    thing = call.data.split(' ')[-5]
    category = call.data.split(' ')[0].split('_')[-1]
    if category == 'ammo': thing = f"Munizione {thing}"     #this adjustment is needed
    # Give a recap to seller
    recipient_link = get_user_link(recipient_id)
    text_to_seller = f"Riassunto operazione: \n\nStai vendendo {thing} a {recipient_link} per {price} soldi. \n\nL'operazione verrà conclusa quando {recipient_link} darà la sua conferma al messaggio che gli ho mandato in privato"
    bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_to_seller)
    telegram_logger.info(f"User {get_user_link(call.from_user.id)} - fine /vendi: - \n\n{text_to_seller}")
    # Ask confirmation from recipient
    seller_id = call.from_user.id
    seller_link = get_user_link(call.from_user.id)
    text_to_recipient = f"Proposta d'acquisto: \n\n{seller_link} vuole venderti {thing} per {price} soldi. \n\nAccetti?"
    inline_keyboard_recipient = {
        "Okk" : {'callback_data' : f'ven4 sì {category} {thing} {price} {seller_id}'},
        "No, non erano questi i patti" : {'callback_data' : 'ven4 no'}
    }
    inline_keyboard_recipient = telebot.util.quick_markup(inline_keyboard_recipient, row_width=1)
    bot.send_message(chat_id=recipient_id, text=text_to_recipient, reply_markup=inline_keyboard_recipient)

@bot.callback_query_handler(func=lambda message: message.data.startswith("ven4"))
def sell_apply(call):   # 'sell_confirmation sì item quadrifoglio 10 213495775'
    data = call.data.split(' ')
    answer = data[1]
    if answer == 'no':
        bot.edit_message_text('Offerta rifiutata.', call.from_user.id, call.message.message_id, parse_mode='HTML')
        telegram_logger.info(f"User {get_user_link(call.from_user.id)} - fine /vendi: - ha rifiutato l'offerta")
        return
    elif answer == 'sì':
        category = data[2]
        if category == 'ammo':  #then must remove "Munizioni "
            thing, price, seller_id = data[4:]
        else:
            thing, price, seller_id = data[3:]
        price = int(price)
        buyer_id = call.from_user.id
        # Check if they have enough money
        if not check_if_enough_money(buyer_id, price):
            bot.answer_callback_query(call.id, 'Non hai abbastanza soldi!', show_alert=True)
            return
        # Depends on category
        if category == 'item':
            transfer_item(seller_id, buyer_id, thing, call.from_user.username)
        elif category == 'weapon':
            try:        # must check they don't already have that weapon
                transfer_weapon(seller_id, buyer_id, thing, call.from_user.username)
            except ValueError:
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text="Hai già quest'arma! Puoi avere solo un esemplare di ogni arma. \n\n<code>Operazione annullata</code>", parse_mode='HTML')
                return
        elif category == 'ammo':
            try:        # must check they do already have that weapon
                transfer_ammo(seller_id, buyer_id, thing)
            except ValueError:
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=f"Non puoi comprare queste munizioni perchè non possiedi l'arma ({thing}). \n\n<code>Operazione annullata</code>", parse_mode='HTML')
                return
            
        # Regardless of category
        transfer_money(seller_id, buyer_id, price)

        # Send messages and log
        text_to_seller, text_to_buyer =  sell_send_messages(call, seller_id, buyer_id, category, thing, price)
        telegram_logger.info(f"User {get_user_link(buyer_id)} - fine /vendi: - \n\ntesto al compratore: \n{text_to_buyer} \n\ntesto al venditore: \n{text_to_seller}")




















##############
# GUARIGIONE #
##############
@bot.message_handler(commands=['guarisci'])
@ignore_dead_users
@ignore_group_messages
def heal_starter(message):
    telegram_logger.info(f"User {get_user_link(message.from_user.id)} - inizio /guarigione")
    # First you should check if 30mins have passed since last attempt
    last_time = retrieve_time_column(message.from_user.id, 'time_of_heal')
    time_check = has_enough_time_passed(last_time, minutes=minutes_between_spy)
    if time_check != True:      # if not enough time has passed
        minutes_left, seconds_left = time_check["minutes"], time_check["seconds"]
        text = f"Puoi effettuare una guarigione solo una volta ogni {minutes_between_heal} minuti. \nRiprova tra {minutes_left} minuti e {seconds_left} secondi"
        bot.reply_to(message, text)
        telegram_logger.info(f"User {get_user_link(message.from_user.id)} - fine /guarigione — non era passato abbastanza tempo")
        return
    elif time_check == True:
        # Display the first page only
        healable_users = get_list_of_users(exclude_self=message)
        list_of_pages = create_keyboard_of_users('heal_choose_user', healable_users)
        text = f"<code>Procedura di guarigione attivata.</code> \nScegli l'utente che vuoi imbottire di aspirina!"
        display_page_number(list_of_pages, 0, text, message, mode='send')

@bot.callback_query_handler(func=lambda message: message.data.startswith("heal_choose_user"))
def heal_choose_user(call):    #'heal_choose_user {page_number} {data}'
    # Possible situations: 1. changed page of keyboard 2. pressed on target user
    if has_changed_page(call):
        new_page_number = change_page_number(call)
        text = "Scegli l'utente che vuoi guarire!"
        display_page_number(create_keyboard_of_users('heal_choose_user'), new_page_number, text, call)
    else:
        heal_calculate_and_apply(call)

def heal_calculate_and_apply(call):
    target_id = retrieve_data(call)
    # Update the time_of_heal
    set_time_column_to_now(call.from_user.id, 'time_of_heal')
    # Retrieve modifiers needed to calculate healing/respawn
    healer_intelligence, healer_team_role, is_alive = retrieve_values_to_calculate_heal(call.from_user.id, target_id)
    # Do calculations and Apply
    if is_alive:
        healing = calculate_heal_hp(healer_intelligence, healer_team_role)
        apply_heal_hp(target_id, healing)
    else:
        healing = calculate_shorten_respawn(healer_intelligence, healer_team_role)
        apply_shorten_respawn(target_id, healing)
    # Send messages and log
    text_to_healer, text_to_healed = heal_send_messages(call.from_user.id, target_id, is_alive, healing, call)
    telegram_logger.info(f"User {get_user_link(call.from_user.id)} - fine /guarigione — testo al guaritore: \n'{text_to_healer}' \n\ntesto al guarito: \n'{text_to_healed}'")




















#################
# MENU DEL TEAM #
#################
@bot.message_handler(commands=['ufficio'])
@ignore_dead_users
@ignore_group_messages
@check_team_admin
def team_menu_starter(message, team_role, team):
    inline_keyboard = {
        "Promuovi a politico" : {'callback_data' : f'tm1__promuovi'},
        "Destituisci un politico" : {'callback_data' : f'tm1__destituisci'},
        "Assumi come s/s/m" : {'callback_data' : f'tm1__assumi'},
        "Licenzia da s/s/m" : {'callback_data' : f'tm1__licenzia'},
        "Elezioni" : {'callback_data' : f'tm1__elezioni'},
        "Proponi votazione" : {'callback_data' : f'tm1__votazione'},
        "Cambia forma di governo" : {'callback_data' : f'tm1__formadigoverno'},
        "Lista membri" : {'callback_data' : f'tm1__listamembri'},
        "Imposta tassazione" : {'callback_data' : f'tm1__tassazione'},
        "Finanze" : {'callback_data' : f'tm1__finanze'},
        "GOLPE" : {'callback_data' : f'tm1__GOLPE'}
    }
    inline_keyboard = telebot.util.quick_markup(inline_keyboard)
    text = f"<code>Accesso eseguito correttamente. \nCredenziali: {team_role}</code> \n\nBenvenuto nell'area riservata del team {team}"
    bot.send_message(message.from_user.id, text=text, parse_mode="HTML", reply_markup=inline_keyboard)
    telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /ufficio")

#Questo serve quando viene premuto "<- indietro"
@bot.callback_query_handler(func=lambda message: message.data.startswith("tm0"))    # This is what allows it to be stateless
def team_menu_restarter(call):
    inline_keyboard = {
        "Promuovi a politico" : {'callback_data' : f'tm1__promuovi'},
        "Destituisci un politico" : {'callback_data' : f'tm1__destituisci'},
        "Assumi come s/s/m" : {'callback_data' : f'tm1__assumi'},
        "Licenzia da s/s/m" : {'callback_data' : f'tm1__licenzia'},
        "Elezioni" : {'callback_data' : f'tm1__elezioni'},
        "Proponi votazione" : {'callback_data' : f'tm1__votazione'},
        "Cambia forma di governo" : {'callback_data' : f'tm1__formadigoverno'},
        "Lista membri" : {'callback_data' : f'tm1__listamembri'},
        "Imposta tassazione" : {'callback_data' : f'tm1__tassazione'},
        "Finanze" : {'callback_data' : f'tm1__finanze'},
        "GOLPE" : {'callback_data' : f'tm1__GOLPE'}
    }
    inline_keyboard = telebot.util.quick_markup(inline_keyboard)
    team = call.data.split('__')[1]
    text = f"<i>Area riservata del team {team}</i>"
    bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)


@bot.callback_query_handler(func=lambda message: message.data.startswith("tm1"))    # This is what allows it to be stateless
def team_menu_1(call):
    data = call.data.split('__')[1]

    if data == "promuovi":
        # Retrieve user's team and team role
        conn, c = prep_database()
        c.execute("SELECT team, team_role FROM users WHERE user_id = %s", (call.from_user.id,))
        team, team_role = c.fetchone()
        # Only the leader can promote/demote politicians
        if team_role != 'leader':
            bot.answer_callback_query(call.id, "Solo il leader può promuovere a politico!", show_alert=True)
            return
        # Retrieve list of team members that are not already politicians
        c.execute("SELECT username FROM users WHERE team = %s AND team_role != 'politico' AND team_role != 'leader'", (team,))
        users = c.fetchall()                # returns a list of tuples
        # Check that list is not empty
        if not users:
            bot.answer_callback_query(call.id, "Non puoi perchè il tuo team non ha membri promuovibili a politico!", show_alert=True)
            return
        users = [tup[0] for tup in users]   # converts it to a list of strings
        inline_keyboard = {}
        for user in users:
            inline_keyboard[f"@{user}"] = {'callback_data' : f'tm2__promuovi__{user}'}
        inline_keyboard["<- indietro"] = {'callback_data' : f'tm0__{team}'}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=2)
        text = "Scegli chi promuovere a politico"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        conn.close()
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")

    elif data == "destituisci":
        # Retrieve user's team
        conn, c = prep_database()
        c.execute("SELECT team, team_role FROM users WHERE user_id = %s", (call.from_user.id,))
        team, team_role = c.fetchone()
        # Only the leader can promote/demote politicians
        if team_role != 'leader':
            bot.answer_callback_query(call.id, "Solo il leader può destituire un politico!", show_alert=True)
            return
        # Retrieve list of team members that are already politicians
        c.execute("SELECT username FROM users WHERE team = %s AND team_role = 'politico'", (team,))
        users = c.fetchall()                # returns a list of tuples
        if not users:
            bot.answer_callback_query(call.id, "Non puoi perchè il tuo team non ha politici!", show_alert=True)
            return
        users = [tup[0] for tup in users]   # converts it to a list of strings
        inline_keyboard = {}
        for user in users:
            inline_keyboard[f"@{user}"] = {'callback_data' : f'tm2__destituisci__{user}'}
        inline_keyboard["<- indietro"] = {'callback_data' : f'tm0__{team}'}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=2)
        text = "Scegli chi destituire"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        conn.close()
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
    
    elif data == "assumi":
        # Retrieve user's team
        conn, c = prep_database()
        c.execute("SELECT team FROM users WHERE user_id = %s", (call.from_user.id,))
        team = c.fetchone()[0]
        # Retrieve list of team members that are not already soldato/spia/medico, nor politico/leader
        c.execute("SELECT username FROM users WHERE team = %s AND team_role = 'nullità'", (team,))
        users = c.fetchall()                # returns a list of tuples
        # Check that list is not empty
        if not users:
            bot.answer_callback_query(call.id, "Non puoi perchè il tuo team non ha membri assumibili come soldato/spia/medico!", show_alert=True)
            return
        users = [tup[0] for tup in users]   # converts it to a list of strings
        inline_keyboard = {}
        for user in users:
            inline_keyboard[f"@{user}"] = {'callback_data' : f'tm2__assumi__{user}'}
        inline_keyboard["<- indietro"] = {'callback_data' : f'tm0__{team}'}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=2)
        text = "Scegli chi assumere come soldato/spia/medico"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        conn.close()
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
    
    elif data == "licenzia":
        # Retrieve user's team
        conn, c = prep_database()
        c.execute("SELECT team FROM users WHERE user_id = %s", (call.from_user.id,))
        team = c.fetchone()[0]
        # Retrieve list of team members that are already soldato/spia/medico
        c.execute("SELECT username FROM users WHERE team = %s AND (team_role = 'soldato' OR team_role = 'spia' OR team_role = 'medico')", (team,))
        users = c.fetchall()                # returns a list of tuples
        # Check that list is not empty
        if not users:
            bot.answer_callback_query(call.id, "Non puoi perchè il tuo team non ha soldati/spie/medici!", show_alert=True)
            return
        users = [tup[0] for tup in users]   # converts it to a list of strings
        inline_keyboard = {}
        for user in users:
            inline_keyboard[f"@{user}"] = {'callback_data' : f'tm2__licenzia__{user}'}
        inline_keyboard["<- indietro"] = {'callback_data' : f'tm0__{team}'}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=2)
        text = "Scegli chi licenziare dal ruolo di soldato/spia/medico"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        conn.close()
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
    
    elif data == "elezioni":
        # Check that 1. it's the leader (and not a politician), 2. no elections are already ongoing, 3. system is democrazia
        conn, c = prep_database()
        c.execute("SELECT team_role, team FROM users WHERE user_id = %s", (call.from_user.id,))
        team_role, team = c.fetchone()
        if team_role != "leader":
            bot.answer_callback_query(call.id, "Solo il Leader può indire le elezioni!", show_alert=True)
            return
        c.execute("SELECT elections, system FROM teams WHERE team = %s", (team,))
        elections_happening, system = c.fetchone()
        conn.close()
        if elections_happening:
            bot.answer_callback_query(call.id, "Sono già in corso delle elezioni!", show_alert=True)
            return
        if system != "democrazia":
            bot.answer_callback_query(call.id, "Solo in democrazia si possono indire le elezioni! Prova a cambiare forma di governo", show_alert=True)
            return
        # Ask confirmation
        inline_keyboard = {
            "SI SI SI" : {'callback_data' : f'tm2__elezioni__{team}'},
            "No ho paura delle urne" : {'callback_data' : f'tm0__{team}'}
        }
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
        text = "Sei sicuro di voler indire le elezioni?"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
    
    elif data == "votazione":
        bot.answer_callback_query(call.id, "Questa funzione non è ancora disponibile", show_alert=True)

    elif data == "formadigoverno":
        conn, c = prep_database()
        # Check that it's the leader; Retrieve team and current type of government
        c.execute("SELECT team, team_role FROM users WHERE user_id = %s", (call.from_user.id,))
        team, team_role = c.fetchone()
        if team_role != "leader":
            bot.answer_callback_query(call.id, "Solo il Leader può cambiare la forma di governo!", show_alert=True)
            return
        c.execute("SELECT system FROM teams WHERE team = %s", (team,))
        system = c.fetchone()[0]
        conn.close()
        # Ask confirmation
        if system == 'democrazia':
            opposite_system = 'dittatura'
        elif system == 'dittatura':
            opposite_system = 'democrazia'
        inline_keyboard = {
            "SI VOGLIO UN NUOVO ORDINE MONDIALE" : {'callback_data' : f'tm2__formadigoverno__{team}__{opposite_system}'},
            "No, rimanga tutto com'è" : {'callback_data' : f'tm0__{team}'}
        }
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
        text = f"Forma di governo attuale: <i>{system}</i>. \n\n<u>Sei sicuro di voler cambiare la forma di governo in una {opposite_system}?</u>"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
    
    elif data == "listamembri":
        conn, c = prep_database()
        # Retrieve team
        c.execute("SELECT team FROM users WHERE user_id = %s", (call.from_user.id,))
        team = c.fetchone()[0]
        # Retrieve leader
        c.execute("SELECT user_id FROM users WHERE team = %s AND team_role = 'leader'", (team,))
        leader = c.fetchone()[0]
        leader = "<b>Leader:</b> " + get_user_link(leader)
        # Retrieve politici
        c.execute("SELECT user_id FROM users WHERE team = %s AND team_role = 'politico'", (team,))
        politici = c.fetchall()
        if len(politici) == 0:
            politici = "<b>Politici:</b> \n/"
        else:
            politici = "<b>Politici:</b>" + "\n  - " + "\n  - ".join(get_user_link(tup[0]) for tup in politici)
        # Retrieve soldati
        c.execute("SELECT user_id FROM users WHERE team = %s AND team_role = 'soldato'", (team,))
        soldati = c.fetchall()
        if len(soldati) == 0:
            soldati = "<b>Soldati:</b> \n/"
        else:
            soldati = "<b>Soldati:</b>" + "\n  - " + "\n  - ".join(get_user_link(tup[0]) for tup in soldati)
        # Retrieve spie
        c.execute("SELECT user_id FROM users WHERE team = %s AND team_role = 'spia'", (team,))
        spie = c.fetchall()
        if len(spie) == 0:
            spie = "<b>Spie:</b> \n/"
        else:
            spie = "<b>Spie:</b>" + "\n  - " + "\n  - ".join(get_user_link(tup[0]) for tup in spie)
        # Retrieve medici
        c.execute("SELECT user_id FROM users WHERE team = %s AND team_role = 'medico'", (team,))
        medici = c.fetchall()
        if len(medici) == 0:
            medici = "<b>Medici:</b> \n/"
        else:
            medici = "<b>Medici:</b>" + "\n  - " + "\n  - ".join(get_user_link(tup[0]) for tup in medici)
        # Retrieve nullitàs
        c.execute("SELECT user_id FROM users WHERE team = %s AND team_role = 'nullità'", (team,))
        nullita = c.fetchall()
        if len(nullita) == 0:
            nullita = "<b>Nullità:</b> \n/"
        else:
            nullita = "<b>Nullità:</b>" + "\n  - " + "\n  - ".join(get_user_link(tup[0]) for tup in nullita)
        inline_keyboard = {"<- indietro" : {'callback_data' : f'tm0__{team}'}}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard)
        text = f"<u>Lista dei membri del team {team}</u> \n\n{leader} \n\n{politici} \n\n{soldati} \n\n{spie} \n\n{medici} \n\n{nullita}"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
    
    elif data == "tassazione":
        # Check that it's the reigning team
        conn, c = prep_database()
        c.execute("SELECT team FROM users WHERE user_id = %s", (call.from_user.id,))
        team = c.fetchone()[0]
        c.execute("SELECT status FROM teams WHERE status = 'regnante' AND team = %s", (team,))
        regnante = c.fetchall()
        if not regnante:
            text = "Solo il team al potere può decidere la tassazione. Se non sei soddisfatto... hai mai pensato a GOLPARE!?"
            bot.answer_callback_query(call.id, text, show_alert=True)
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
        # Retrieve current taxation
        c.execute("SELECT taxation FROM teams WHERE status = 'regnante'")
        taxation = c.fetchone()[0]
        # Ask confirmation
        inline_keyboard = {
            "SI SI" : {'callback_data' : f'tm2__tassazione__{taxation}'},
            "No sennò Moody's mi cambia il rating" : {'callback_data' : f'tm0__{team}'}
        }
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
        text = f"<b>Aliquota attuale:</b> <code>{taxation}%</code>\n\n<i>Vuoi cambiare l'aliquota?</i>"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        conn.close()
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
    
    elif data == "finanze":
        # Retrieve team
        conn, c = prep_database()
        c.execute("SELECT team FROM users WHERE user_id = %s", (call.from_user.id,))
        team = c.fetchone()[0]
        conn.close()
        inline_keyboard = {
            'Cassa del team' : {'callback_data' : f'tm2__finanze__cassa__{team}'},
            'Imposta salari' : {'callback_data' : f'tm2__finanze__salari__{team}'},
            'Preleva dalla cassa' : {'callback_data' : f'tm2__finanze__preleva__{team}__1'},
            '<- indietro' : {'callback_data' : f'tm0__{team}'}
        }
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
        text = "Menu finanze"
        bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=inline_keyboard)
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")

    elif data == "GOLPE":
        # Check that 1. it's the leader (and not a politician), 2. no golpe is already ongoing, 3. team isn't already reigning
        conn, c = prep_database()
        c.execute("SELECT team_role, team FROM users WHERE user_id = %s", (call.from_user.id,))
        team_role, team = c.fetchone()
        if team_role != "leader":
            bot.answer_callback_query(call.id, "Solo il Leader può indire un GOLPE!", show_alert=True)
            return
        c.execute("SELECT status FROM teams WHERE status = 'golpante'")
        golpante = c.fetchall()
        if golpante:
            text = "C'è già un GOLPE in corso!"
            bot.answer_callback_query(call.id, text, show_alert=True)
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
        c.execute("SELECT status FROM teams WHERE status = 'regnante' AND team = %s", (team,))
        regnante = c.fetchall()
        if regnante:
            text = "Il tuo team è già al potere, cosa vuoi GOLPARE!?"
            bot.answer_callback_query(call.id, text, show_alert=True)
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")
        # Ask confirmation
        inline_keyboard = {
            "SI SI SI SI SI SI SI" : {'callback_data' : f'tm2__GOLPE__{team}'},
            "No la mamma non vuole" : {'callback_data' : f'tm0__{team}'}
        }
        inline_keyboard = telebot.util.quick_markup(inline_keyboard)
        text = "Sei sicuro di voler proclamare un GOLPE?"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        conn.close()
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")




@bot.callback_query_handler(func=lambda message: message.data.startswith("tm2"))    # This is what allows it to be stateless
def team_menu_2(call):
    data = call.data.split('__')[1]

    if data == "promuovi":
        subject = call.from_user.username
        object = call.data.split('__')[2]
        # Apply
        conn, c = prep_database()
        c.execute("UPDATE users SET team_role = 'politico' WHERE username = %s", (object,))
        conn.commit()
        # Retrieve object's ID before sending messages
        c.execute("SELECT user_id FROM users WHERE username = %s", (object,))
        object_id = c.fetchone()[0]
        subject_id = call.from_user.id
        conn.close()
        # Send messages
        subject_link = get_user_link(subject_id)
        object_link = get_user_link(object_id)
        text_to_subject = f"<b>Hai promosso {object_link} a Politico</b>"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=subject_id, text=text_to_subject, parse_mode='HTML')
        text_to_object = f"<b>{subject_link} ti ha appena promosso a Politico!</b>"
        bot.send_message(object_id, text_to_object, 'HTML')
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text_to_subject}")
    
    elif data == "destituisci":
        subject = call.from_user.username
        object = call.data.split('__')[2]
        # Apply
        conn, c = prep_database()
        c.execute("UPDATE users SET team_role = 'nullità' WHERE username = %s", (object,))
        conn.commit()
        # Retrieve object's ID before sending messages
        c.execute("SELECT user_id FROM users WHERE username = %s", (object,))
        object_id = c.fetchone()[0]
        subject_id = call.from_user.id
        conn.close()
        # Send messages
        subject_link = get_user_link(subject_id)
        object_link = get_user_link(object_id)
        text_to_subject = f"<b>Hai destituito {object_link} dal ruolo di Politico! Adesso è una nullità!</b>"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=subject_id, text=text_to_subject, parse_mode='HTML')
        text_to_object = f"<b>{subject_link} ti ha appena destituito dal ruolo di Politico! Adesso sei una nullità!</b>"
        bot.send_message(object_id, text_to_object, 'HTML')
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text_to_subject}")
    
    if data == "assumi":
        # Understand if have already asked role or not
        if len(call.data.split('__')) == 3:
        # Ask which role
            inline_keyboard = {
                'Soldato' : {'callback_data' : f'{call.data}__soldato'},
                'Spia' : {'callback_data' : f'{call.data}__spia'},
                'Medico' : {'callback_data' : f'{call.data}__medico'},
                '<- indietro' : {'callback_data' : f'tm1__assumi'}
            }
            inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
            text = "Con quale ruolo lo vuoi assumere?"
            bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text, parse_mode='HTML', reply_markup=inline_keyboard)
        elif len(call.data.split('__')) == 4:
            subject = call.from_user.username
            object = call.data.split('__')[2]
            role = call.data.split('__')[3]
            # Apply
            conn, c = prep_database()
            c.execute("UPDATE users SET team_role = %s WHERE username = %s", (role, object))
            conn.commit()
            # Retrieve object's ID before sending messages
            c.execute("SELECT user_id FROM users WHERE username = %s", (object,))
            object_id = c.fetchone()[0]
            subject_id = call.from_user.id
            conn.close()
            # Send messages
            subject_link = get_user_link(subject_id)
            object_link = get_user_link(object_id)
            text_to_subject = f"<b>Hai assunto {object_link} come {role}</b>"
            bot.edit_message_text(message_id=call.message.message_id, chat_id=subject_id, text=text_to_subject, parse_mode='HTML')
            text_to_object = f"<b>{subject_link} ti ha appena assunto come {role}!</b>"
            bot.send_message(object_id, text_to_object, 'HTML')
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text_to_subject}")
    
    elif data == "licenzia":
        subject = call.from_user.username
        object = call.data.split('__')[2]
        # Retrieve object's ID and team_role before sending messages
        conn, c = prep_database()
        c.execute("SELECT user_id, team_role FROM users WHERE username = %s", (object,))
        object_id, team_role = c.fetchone()
        subject_id = call.from_user.id
        # Apply
        c.execute("UPDATE users SET team_role = 'nullità' WHERE username = %s", (object,))
        conn.commit()
        conn.close()
        # Send messages
        subject_link = get_user_link(subject_id)
        object_link = get_user_link(object_id)
        text_to_subject = f"<b>Hai licenziato {object_link} dal ruolo di {team_role}! Adesso è una nullità!</b>"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=subject_id, text=text_to_subject, parse_mode='HTML')
        text_to_object = f"<b>{subject_link} ti ha appena destituito dal ruolo di {team_role}! Adesso sei una nullità!</b>"
        bot.send_message(object_id, text_to_object, 'HTML')
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text_to_subject}")
    
    
    elif data == "elezioni":
        team = call.data.split('__')[2]
        # Apply
        conn, c = prep_database()
        c.execute("UPDATE teams SET elections = TRUE WHERE team = %s", (team,))
        c.execute("UPDATE users SET has_voted = 'astenuto' WHERE team = %s", (team,))
        conn.commit()
        conn.close()
        # Send messages
        text = "a" if hours_elections==1 else "e"
        text_to_leader = f"<b>Hai dato il via alle elezioni!</b> \n\nIl tuo team ha <u>{hours_elections} or{text} di tempo</u> per votare. \nPer farlo basta mandare /vota"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_to_leader, parse_mode='HTML')
        text = "a" if hours_elections==1 else "e"
        user_link = get_user_link(call.from_user.id)
        text_to_group = f"<b>{user_link} ha dato il via alle elezioni nel team {team}!</b> \n\nAvete <u>{hours_elections} or{text} di tempo</u> per votare. \nPer farlo basta mandare /vota"
        bot.send_message(group_id, text_to_group, 'HTML')
        election_scheduler(team)    #here it calls the function that checks conditions and sends updates every 15mins
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text_to_leader}")
    
    elif data == "formadigoverno":   # 'tm2__formadigoverno__{team}__{opposite_system}'
        team, opposite_system = call.data.split('__')[2:4]
        # Apply
        conn, c = prep_database()
        c.execute("UPDATE teams SET system = %s WHERE team = %s", (opposite_system, team))
        conn.commit()
        conn.close()
        # Send messages
        user_link = get_user_link(call.from_user.id)
        text_to_leader = f"<b><u>Ora sei il leader di una {opposite_system}.</u></b>"
        text_to_group = f"<b><u>Breaking News!</u></b> \n\n{user_link} ha reso il team {team} una {opposite_system}!"
        bot.edit_message_text(text_to_leader, call.from_user.id, call.message.message_id, parse_mode='HTML')
        bot.send_message(group_id, text_to_group, 'HTML')
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text_to_leader}")

    elif data == "tassazione":
        # Create keyboard and send message
        # Copypasted from Dona, which is copypasted from Vendi
        current_price = int(call.data.split('__')[2])
        # Check if they pressed "Fatto!"
        if len(call.data.split('__')) < 4:    #i.e. if I've not yet added "__fatto" to the callback data
            keyboard_buttons = [1, 5, 10, 50]
            range_valid_price = [0, 100]
            inline_keyboard = {}
            for button in keyboard_buttons:    #first the + row
                if (current_price + button) <= range_valid_price[1]: # Only add the button if it wouldn't make the price go out of range
                    inline_keyboard[f"+{button}%"] = {'callback_data' : f'tm2__tassazione__{current_price + button}'}
            for button in keyboard_buttons:    #and then the - row
                if (current_price - button) >= range_valid_price[0]: # Only add the button if it wouldn't make the price go out of range
                    inline_keyboard[f"-{button}%"] = {'callback_data' : f'tm2__tassazione__{current_price - button}'}
            inline_keyboard["Fatto!"] = {'callback_data' : f'tm2__tassazione__{current_price}__"fatto"'}
            inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=4)
            text_price = f"Scegli la nuova aliquota \n\nAliquota: {current_price}%"
            bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_price, reply_markup=inline_keyboard)
        elif len(call.data.split('__')) == 4:    #i.e. if I've added "__fatto" to the callback data
            taxation = call.data.split('__')[2]    # this excludes "fatto"
            taxation = int(taxation)
            # Apply
            conn, c = prep_database()
            c.execute("SELECT team FROM users WHERE user_id = %s", (call.from_user.id,))
            team = c.fetchone()[0]
            c.execute("UPDATE teams SET taxation = %s WHERE team = %s", (taxation, team))
            conn.commit()
            conn.close()
            # Send message
            text_feedback = f"<code>Operazione eseguita correttamente</code> \n\n<b><u>Nuova aliquota:</u></b> <code>{taxation}% </code>"
            bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_feedback, parse_mode='HTML')
            # Notify the main group
            text_to_main_group = f"<u>Breaking News!</u> \n\nIl governo {team} ha appena <b>cambiato la tassazione al {taxation}%</b>"
            bot.send_message(group_id, text_to_main_group, 'HTML')
            # Log
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text_feedback}")
    
    elif data == "finanze":
        submenu, team = call.data.split('__')[2:4]

        if submenu == 'cassa':
            conn, c = prep_database()
            # Show current amount
            c.execute("SELECT bank, taxation, status FROM teams WHERE team = %s", (team,))
            bank, taxation, status = c.fetchone()
            # Show expected daily revenue from taxation, but only if team is regnante
            if status == 'regnante':
                c.execute("SELECT user_id FROM users WHERE team_role = 'nullità'")
                private_workers = c.fetchall()
                jobs_list = []
                for private_worker_tuple in private_workers:
                    private_worker = private_worker_tuple[0]
                    c.execute("SELECT job_name FROM job WHERE user_id = %s AND job_name != 'TEAMROLE'", (private_worker,))
                    job = c.fetchone()
                    if job:
                        jobs_list.append(job[0])
                revenue = 0
                for job in jobs_list:
                        daily_salary = jobs[job]["salary"] * (24 / jobs[job]["frequency_hours"])
                        daily_tax = daily_salary * (taxation/100)
                        revenue += daily_tax
                revenue = round(revenue)
                revenue_string = f"{revenue} soldi"
            elif status != 'regnante':
                revenue = 0
                revenue_string = "0 (il  tuo team non è al governo, quindi non può riscuotere tasse)"
            # Show expected daily expenses through role salaries
            c.execute("SELECT team_role FROM users WHERE team = %s AND team_role != 'nullità'", (team,))    #Retrieve all statal workers' roles
            roles_list = c.fetchall()
            expenses = 0
            for role_name_tuple in roles_list:
                role_name = role_name_tuple[0]
                c.execute("SELECT salaries->%s FROM teams WHERE team = %s", (role_name, team))
                daily_salary = c.fetchone()[0]
                expenses += daily_salary
            # Show balance; if negative balance, show days until bankrupt
            balance = revenue - expenses
            balance_sign = "+" if balance >=0 else "-"
            if balance < 0:
                days_until_bankrupt = round(bank / abs(balance))
            # Send message
            conn.close()
            text = f'''<b>Cassa del team:</b> <code>{bank} soldi</code>

<i>Aliquota:</i> {taxation}%
<b>Incassi</b> stimati giornalieri dalla tassazione: <code>{revenue_string}</code>
<b>Spese</b> stimate giornaliere per i salari dei ruoli statali: <code>{expenses} soldi</code>

<u>Bilancio:</u> {balance_sign}{abs(balance)} soldi/giorno
'''
            if balance < 0:
                text += f"<b><u>Attenzione! Il bilancio del team è in negativo! Di questo passo, fra circa {days_until_bankrupt} giorni finirete come l'Argentina!</u></b>"
            inline_keyboard = {'<- indietro' : {'callback_data' : 'tm1__finanze'}}
            inline_keyboard = telebot.util.quick_markup(inline_keyboard)
            bot.edit_message_text(text, call.from_user.id, call.message.message_id, parse_mode='HTML', reply_markup=inline_keyboard)
            telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")

        elif submenu == 'salari':
            # First understand which sublevel we're at

            if len(call.data.split('__')) == 4:    # 'tm2__finanze__salari__{team}'
                # Retrieve current salaries
                conn, c = prep_database()
                c.execute("SELECT salaries FROM teams WHERE team = %s", (team,))
                salaries_dict = c.fetchone()[0]
                conn.close()
                # Create text
                text = "Ecco i salari attuali: "
                for key, value in salaries_dict.items():
                    text += f"\n- <b>{key}</b>: <i>{value} soldi/giorno</i>"
                text += "\n\nQuale di questi salari vuoi modificare?"
                # Create keyboard
                inline_keyboard = {role : {'callback_data' : f'tm2__finanze__salari__{team}__{role}__{current_salary}'} for role, current_salary in salaries_dict.items()}
                inline_keyboard["<- indietro"] = {'callback_data' : 'tm1__finanze'}
                inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
                bot.edit_message_text(text, call.from_user.id, call.message.message_id, parse_mode='HTML', reply_markup=inline_keyboard)
                telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")

            elif len(call.data.split('__')) == 6:    # 'tm2__finanze__salari__{team}__{role}__{current_salary}'
                team, role, current_salary = call.data.split('__')[3:]
                current_salary = int(current_salary)
                # copypasted from tassazione, which is copypasted from dona, which is copypasted from vendi
                keyboard_buttons = [1, 10, 50, 100]
                range_valid_salary = [0, 10000]
                inline_keyboard = {}
                for button in keyboard_buttons:    #first the + row
                    if (current_salary + button) <= range_valid_salary[1]: # Only add the button if it wouldn't make the price go out of range
                        inline_keyboard[f"+{button}"] = {'callback_data' : f'tm2__finanze__salari__{team}__{role}__{current_salary + button}'}
                for button in keyboard_buttons:    #and then the - row
                    if (current_salary - button) >= range_valid_salary[0]: # Only add the button if it wouldn't make the price go out of range
                        inline_keyboard[f"-{button}"] = {'callback_data' : f'tm2__finanze__salari__{team}__{role}__{current_salary - button}'}
                inline_keyboard["Fatto!"] = {'callback_data' : f'tm2__finanze__salari__{team}__{role}__{current_salary}__"fatto"'}
                inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=4)
                text_salary = f"Modifica il salario per il ruolo {role} \n\nSalario: {current_salary} soldi/giorno"
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_salary, reply_markup=inline_keyboard)

            elif len(call.data.split('__')) == 7:    # 'tm2__finanze__salari__{team}__{role}__{current_salary}__"fatto"'
                team, role, new_salary = call.data.split('__')[3:6]
                new_salary = int(new_salary)
                # Apply
                conn, c = prep_database()
                json_object = json.dumps({role: new_salary})    #this step is needed bc I fucking hate pgsql
                c.execute('''UPDATE teams SET salaries = salaries || %s::jsonb WHERE team = %s''', (json_object, team))
                conn.commit()
                # Send message
                text_feedback = f"<code>Operazione eseguita correttamente</code> \n\n<b>Nuovo salario per il ruolo {role}:</b> <code>{new_salary} soldi/giorno </code>"
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_feedback, parse_mode='HTML')
                # Notify those with the affected role
                c.execute("SELECT user_id FROM users WHERE team_role = %s AND team = %s", (role, team))
                those_affected = c.fetchall()
                conn.close()
                user_link = get_user_link(call.from_user.id)
                text_to_those_affected = f"<u>Breaking News!</u> \n\n{user_link} ha appena <b>cambiato il salario del ruolo {role} a {new_salary} soldi/giorno</b>"
                for user_id_tuple in those_affected:
                    user_id = user_id_tuple[0]
                    try:
                        bot.send_message(user_id, text_to_those_affected, parse_mode='HTML')
                    except:
                        pass
                # Log
                telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text_to_those_affected}")
                

        elif submenu == 'preleva':
            # First understand which sublevel we're at

            if len(call.data.split('__')) == 5:    # 'tm2__finanze__preleva__{team}__{amount}'
                team, current_amount = call.data.split('__')[3:]
                current_amount = int(current_amount)
                # copypasted from modificasalari, which is copypasted from tassazione, which is copypasted from dona, which is copypasted from vendi
                keyboard_buttons = [1, 10, 50, 100]
                range_valid_amount = [1, 1000]
                inline_keyboard = {}
                for button in keyboard_buttons:    #first the + row
                    if (current_amount + button) <= range_valid_amount[1]: # Only add the button if it wouldn't make the price go out of range
                        inline_keyboard[f"+{button}"] = {'callback_data' : f'tm2__finanze__preleva__{team}__{current_amount + button}'}
                for button in keyboard_buttons:    #and then the - row
                    if (current_amount - button) >= range_valid_amount[0]: # Only add the button if it wouldn't make the price go out of range
                        inline_keyboard[f"-{button}"] = {'callback_data' : f'tm2__finanze__preleva__{team}__{current_amount - button}'}
                inline_keyboard["Fatto!"] = {'callback_data' : f'tm2__finanze__preleva__{team}__{current_amount}__"fatto"'}
                inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=4)
                text_amount = f"Inserisci l'importo da prelevare \n\nImporto: {current_amount} soldi"
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_amount, reply_markup=inline_keyboard)

            elif len(call.data.split('__')) == 6:    # 'tm2__finanze__preleva__{team}__{amount}__"fatto"'
                team, amount = call.data.split('__')[3:5]
                amount = int(amount)
                # Check that the team's bank does have that amount
                conn, c = prep_database()
                c.execute("SELECT bank FROM teams WHERE team = %s", (team,))
                team_bank = c.fetchone()[0]
                if team_bank - amount < 0:
                    bot.answer_callback_query(call.id, "La cassa del tuo team non ha tutti quei soldi!", show_alert=True)
                    return
                # Apply
                c.execute("UPDATE teams SET bank = teams.bank - %s WHERE team = %s", (amount, team))
                c.execute("UPDATE users SET bank = users.bank + %s WHERE user_id = %s", (amount, call.from_user.id))
                conn.commit()
                # Send message
                text = f"<b>Hai prelevato {amount} soldi dalla cassa del team.</b> \nTutti i politici sono stati avvisati. È buona regola informarli della causale del tuo prelievo."
                bot.edit_message_text(text, call.from_user.id, call.message.message_id, parse_mode='HTML')
                # Notify leader and politicians of the team
                c.execute("SELECT user_id FROM users WHERE team = %s AND (team_role = 'leader' OR team_role = 'politico')", (team,))
                user_id_list = c.fetchall()
                conn.close()
                user_link = get_user_link(call.from_user.id)
                text_to_politicians = f"<b>{user_link} ha appena prelevato {amount} soldi dalla cassa del team</b>"
                for user_id_tuple in user_id_list:
                    user_id = user_id_tuple[0]
                    try:
                        bot.send_message(user_id, text_to_politicians, 'HTML')
                    except:
                        pass
                # Log
                telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text}")

    elif data == "GOLPE":
        team = call.data.split('__')[2]
        # Apply
        conn, c = prep_database()
        c.execute("UPDATE teams SET status = 'golpante' WHERE team = %s", (team,))
        conn.commit()
        conn.close()
        # Send messages
        text = "a" if hours_elections==1 else "e"
        text_to_leader = f"<b><u>Hai dato il via al GOLPE!</u></b> \n\nIl tuo team ha <u>{hours_golpe} or{text} di tempo</u> a partire da adesso per rovesciare il team al potere. \nPuoi farlo in due modi: \n1. Uccidendo il leader \n2. Uccidendo il 50%+1 dei politici"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_to_leader, parse_mode='HTML')
        user_link = get_user_link(call.from_user.id)
        text_to_group = f"<b><u>{user_link} ha dato il via al GOLPE!</u></b> \n\nPreparate le armi o mettetevi al riparo!"
        bot.send_message(group_id, text_to_group, 'HTML')
        golpe_scheduler()    #here it calls the function that checks conditions and sends updates every 15mins
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /ufficio - \n\n{text_to_leader}")





def election_scheduler(team):
    bot.send_message(admin_id, "elezioni iniziate")    #test#
    # Start by waiting
    number_of_updates = 2
    seconds_to_wait = hours_elections*3600/number_of_updates    # converts to seconds and divides into 2 time intervals; if total golpe time is 1h, it waits 30min
    for i in range(number_of_updates):
        time.sleep(seconds_to_wait)
        # Retrieve number of votes over total team members
        conn, c = prep_database()
        c.execute("SELECT * FROM users WHERE team = %s AND has_voted != 'astenuto'", (team,))
        number_of_votes = len(c.fetchall())
        c.execute("SELECT * FROM users WHERE team = %s", (team,))
        number_of_voters = len(c.fetchall())
        percentage_of_votes = round(number_of_votes/number_of_voters *100)
        # If there's still time, only send the message
        if i < (number_of_updates-1):
            text = f"<b>UPDATE SULLE ELEZIONI</b> \n\nSono passati {round((seconds_to_wait/60) * (i+1))} minuti \nRimangono {round((seconds_to_wait/60) * ((number_of_updates-1)-i))} minuti per votare.\nBasta mandare /vota \n\nNumero attuale di voti: {number_of_votes}/{number_of_voters} ({percentage_of_votes}%)"
            bot.send_message(group_id, text, 'HTML')
        # If time's up, apply changes
        elif i == (number_of_updates-1):
            # First, check there's at least 1 vote; if not, cancel everything
            if number_of_votes == 0:
                c.execute("UPDATE teams SET elections = FALSE WHERE team = %s", (team,))
                conn.commit()
                conn.close()
                text = f"Il tempo delle elezioni è finito. E nessuno ha votato... \nResta tutto com'è."
                bot.send_message(group_id, text, 'HTML')
                return
            # Count the votes
            number_of_abstainees = number_of_voters - number_of_votes
            c.execute("SELECT has_voted FROM users WHERE team = %s AND has_voted != 'astenuto'", (team,))
            votes = c.fetchall()
            votes = [tup[0] for tup in votes]    # converts from list of tuples to list of strings
            votes_dict = {}
            for vote in votes:
                if vote in votes_dict:  #bc calling +=1 on an a key that is not there would raise an error
                    votes_dict[vote] +=1
                else:
                    votes_dict[vote] = 1
            max_votes = max(votes_dict.values())
            # The following ensures ties are considered
            most_voted_users = [key for key, value in votes_dict.items() if value == max_votes]
            if len(most_voted_users) == 1:
                winner = most_voted_users[0]
            else:
                winner = random.choice(most_voted_users)
                #and for the recap message, just check len(most_voted_users)
            # Check if the winner was already leader (i.e. if it's a re-election)
            c.execute("SELECT team_role FROM users WHERE username = %s", (winner,))
            team_role = c.fetchone()[0]
            if team_role == 'leader':
                re_election = True  #will use this in the recap message
            else:
                re_election = False
                # Retrieve the old leader (for the purpose of the recap messages)
                c.execute("SELECT username FROM users WHERE team_role = 'leader' AND team = %s", (team,))
                old_leader = c.fetchone()[0]
                # If it's not a re-election, fire the old leader and appoint the new one
                c.execute("UPDATE users SET team_role = 'nullità' WHERE team_role = 'leader' AND team = %s", (team,))
                c.execute("UPDATE users SET team_role = 'leader' WHERE username = %s", (winner,))
            # Reset team status
            c.execute("UPDATE teams SET elections = FALSE WHERE team = %s", (team,))
            conn.commit()
            conn.close()
        # And send messages
            text_part1 = f"<b>I SEGGI SONO CHIUSI</b> \n\nNumero totale di voti: {number_of_votes}/{number_of_voters} ({percentage_of_votes})% \n\nProcedo allo spoglio..."
            bot.send_message(group_id, text_part1, 'HTML')
            time.sleep(10)  # just for the suspence
            if len(most_voted_users) == 1:
                text_part2 = f"Il vincitore è <span class='tg-spoiler'>@{winner}</span>!!! \n\n\nLista totale dei voti: \n"
            elif len(most_voted_users) > 1:
                text_part2 = f"È un pareggio! Il vincitore è stato estratto a sorte tra i più votati. \nIl vincitore è <span class='tg-spoiler'>@{winner}</span>!!! \n\n\nLista totale dei voti: \n"
            for user, nvotes in votes_dict.items():
                text_part2 += ("@" + user + ": " + str(nvotes) + "\n")  #adds the full list of votes
            bot.send_message(group_id, text_part2, 'HTML')
            time.sleep(5) # just to space a bit the messages in time
            if re_election:
                text_part3 = f"@{winner} viene quindi confermato come leader del team {team}!"
                text_part4 = "ri-eletto"
            else:
                text_part3 = f"@{winner} prende quindi il posto di @{old_leader}!"
                text_part4 = "eletto"
            bot.send_message(group_id, text_part3, 'HTML')
            bot.send_message(admin_id, f"<b>Sei stato {text_part4} leader!</b>", 'HTML')    #test#    va sostituito con l'ID del vincitore (che va retrievato)
            telegram_logger.info(text_part1)
            telegram_logger.info(text_part2)
            telegram_logger.info(text_part3)


def golpe_scheduler():
    # Retrieve golpante and regnante
    conn, c = prep_database()
    c.execute("SELECT team FROM teams WHERE status = 'golpante'")
    golping_team = c.fetchone()[0]
    c.execute("SELECT team FROM teams WHERE status = 'regnante'")
    reigning_team = c.fetchone()[0]
    conn.close()
    number_of_updates = 4
    for i in range(number_of_updates):    # Sends updates 4 times
        # start by waiting
        seconds_to_wait = hours_golpe*3600/number_of_updates   # converts to seconds and divides into 4 time intervals; if total golpe time is 1h, it waits 15min
        time.sleep(seconds_to_wait)
        # first, check that golpe isn't already over
        conn, c = prep_database()
        c.execute("SELECT status FROM teams WHERE team = %s", (golping_team,))
        status = c.fetchone()[0]
        if status != "golpante":
            bot.send_message(admin_id, "golpe già finito capo") #test#
            return
        # if golpe still ongoing, go on
        # Check the 2 conditions: 1. leader is dead 2. 50%+1 of politici is dead
        # Condition #1
        c.execute("SELECT is_alive FROM users WHERE team = %s AND team_role = 'leader'", (reigning_team,))
        leader_is_alive = c.fetchone()[0]
        if not leader_is_alive:
            # Golpe successful. Apply
            c.execute("UPDATE teams SET status = 'regnante' WHERE team = %s", (golping_team,))
            c.execute("UPDATE teams SET status = 'neutrale' WHERE team = %s", (reigning_team,))
            # Winning team steals the defeated team's bank
            c.execute("SELECT bank FROM teams WHERE team = %s", (reigning_team,))
            bank = c.fetchone()[0]
            c.execute("UPDATE teams SET bank = bank + %s WHERE team = %s", (bank, golping_team))
            c.execute("UPDATE teams SET bank = 0 WHERE team = %s", (reigning_team,))
            ### Here they should take the armory too
            # Commit and close
            conn.commit()
            conn.close()
            # Send messages
            # Send messages
            text_to_leader_killer = "<b><u>IL LEADER È MORTO. \nIL GOLPE HA AVUTO SUCCESSO.</u></b> \n\nOra siete voi a comandare."
            # for now I decided not to send message to winners specifically, and just send the message on the global group
            text_to_loser_leader = "<b><u>IL LEADER È MORTO. \nIL GOLPE HA AVUTO SUCCESSO.<u><b> \n\nAvete perso tutto."
            # for now I decided not to send message to losers specifically, and just send the message on the global group
            text_to_group = f"<b><u>IL GOLPE HA AVUTO SUCCESSO. \n\nIL TEAM {golping_team} HA ROVESCIATO IL TEAM {reigning_team}</b></u>"
            bot.send_message(group_id, text_to_group, 'HTML')
            telegram_logger.info(text_to_group)
            return #otherwise it'd check condition 2 even if the leader is dead
        # Condition #2
        c.execute("SELECT is_alive FROM users WHERE team = %s AND team_role = 'politico'", (reigning_team,))
        politicians_alive = c.fetchall()                            #returns a list of tuples
        politicians_alive = [tup[0] for tup in politicians_alive]   #converts to a list of integers
        number_to_kill = int((len(politicians_alive) / 2) +1)
        if politicians_alive.count(0) >= number_to_kill:
            # Golpe successful. Apply
            c.execute("UPDATE teams SET status = 'regnante' WHERE team = %s", (golping_team,))
            c.execute("UPDATE teams SET status = 'neutrale' WHERE team = %s", (reigning_team,))
            # Winning team steals the defeated team's bank
            c.execute("SELECT bank FROM teams WHERE team = %s", (reigning_team,))
            bank = c.fetchone()[0]
            c.execute("UPDATE teams SET bank = bank + %s WHERE team = %s", (bank, golping_team))
            c.execute("UPDATE teams SET bank = 0 WHERE team = %s", (reigning_team,))
            ### Here they should take the armory too
            # Commit and close
            conn.commit()
            conn.close()
            # Send messages
            text_to_final_killer = "<b><u>IL 50%+1 DEI POLITICI È MORTO. \nIL GOLPE HA AVUTO SUCCESSO.</u></b> \n\nOra siete voi a comandare."
            # for now I decided not to send message to losers specifically, and just send the message on the global group
            text_to_loser = "<b><u>IL 50%+1 DEI POLITICI È MORTO. \nIL GOLPE HA AVUTO SUCCESSO.<u><b> \n\nAvete perso tutto."
            # for now I decided not to send message to losers specifically, and just send the message on the global group
            text_to_group = f"<b><u>IL GOLPE HA AVUTO SUCCESSO. \n\nIL TEAM {golping_team} HA ROVESCIATO IL TEAM {reigning_team}</b></u>"
            bot.send_message(group_id, text_to_group, 'HTML')
            telegram_logger.info(text_to_group)
        else:
            # Send update on golpe status
            # But first check if it's a midway update or the final one
            if i < (number_of_updates-1):
                text_to_all = f"<i>Update sul GOLPE</i> \n\nSono passati {round((seconds_to_wait/60) * (i+1))} minuti. \nRimangono {round((seconds_to_wait/60) * ((number_of_updates-1)-i))} minuti \n\n<span class='tg-spoiler'>Il leader è ancora in vita. \n\nNumero totale di politici da uccidere: {number_to_kill} \nNumero di politici uccisi: {politicians_alive.count(0)}</span>"
                bot.send_message(group_id, text_to_all, 'HTML')
                telegram_logger.info(text_to_all)
            elif i == (number_of_updates-1):
                text_to_all = f"<i>Update sul GOLPE</i> \n\nSono passati {round((seconds_to_wait/60) * (i+1))} minuti. \nRimangono {round((seconds_to_wait/60) * ((number_of_updates-1)-i))} minuti \n\n<span class='tg-spoiler'><b><u>IL TEMPO È FINITO. \nIL GOLPE È FALLITO.</u></b> \n\nIl conto bancario del team golpante viene confiscato dal team regnante.</span>"
                bot.send_message(group_id, text_to_all, 'HTML')
                # Apply the money steal
                c.execute("SELECT bank FROM teams WHERE team = %s", (golping_team,))
                bank = c.fetchone()[0]
                c.execute("UPDATE teams SET bank = bank + %s WHERE team = %s", (bank, reigning_team))
                c.execute("UPDATE teams SET bank = 0 WHERE team = %s", (golping_team,))
                ### here should take the armory too
                # Reset status from "golpante" to "neutrale"
                c.execute("UPDATE teams SET status = 'neutrale' WHERE status = 'golpante'")
                conn.commit()
                conn.close()
                telegram_logger.info(text_to_all)



########
# VOTA #
########
@bot.message_handler(commands=['vota'])
@ignore_group_messages
@ignore_dead_users
def vote_starter(message):
    # Check that an election is taking place in the user's team
    conn, c = prep_database()
    c.execute("SELECT team FROM users WHERE user_id = %s", (message.from_user.id,))
    team = c.fetchone()[0]
    c.execute("SELECT elections FROM teams WHERE team = %s", (team,))
    elections_happening = c.fetchone()[0]
    if not elections_happening:
        bot.reply_to(message, "Non ci sono elezioni in corso nel tuo team")
        return
    # Check that user hasn't already voted
    c.execute("SELECT has_voted FROM users WHERE user_id = %s", (message.from_user.id,))
    has_voted = c.fetchone()[0]
    if has_voted != 'astenuto':
        bot.reply_to(message, "Hai già votato!")
        return
    # Ok, go on
    inline_keyboards = create_vote_keyboard(team)
    first_page = inline_keyboards[0]
    first_page = telebot.util.quick_markup(first_page, row_width=2)
    bot.send_message(message.from_user.id, f"Scegli chi votare \n\nPagina 1 di {len(inline_keyboards)}", reply_markup=first_page)
    conn.close()
    telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /vota")


@bot.callback_query_handler(func=lambda message: message.data.startswith("v1"))    # This is what allows it to be stateless
def vote_select_user(call):
    # Possible situations: 1. changed page of keyboard 2. pressed on target user
    # Retrieve it from the codified call.data
    data = call.data.split("__")[2]
    team = call.data.split("__")[3]
    # And also retrieve the current page number
    old_page_number = int(call.data.split("__")[1])
    # 1. changed page of keyboard
    if data in ("<", ">"):
        # If it's to be stateless, than must re-call the keyboard creator function
        inline_keyboards = create_vote_keyboard(team)
        number_of_pages = len(inline_keyboards)
        # Basically update keyboard, resend the message, and back to square one
        # Creo un dizionario che snellisce ed evita futuri if < o >
        direction = {"<" : -1, ">" : +1}
        if number_of_pages == 1:
            bot.answer_callback_query(call.id, "C'è solo una pagina! Quelli che vedi sono tutti gli utenti!")
        else:
            # Turn page; -1 if <, +1 if >
            new_page_number = old_page_number + direction[data]
            # Now check that it's not asking for a page_index out of range
            if new_page_number in range(0,number_of_pages):
                # Aggiorna il testo
                choose_target_text = f"Scegli chi votare! \n\nPagina {new_page_number + 1} di {number_of_pages}"
                # Now select the correct page only
                current_page = inline_keyboards[new_page_number]
                # And convert it into an inline keyboard quick_markup
                current_page = telebot.util.quick_markup(current_page, row_width=2)
                # Edit the message
                bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=choose_target_text, parse_mode='HTML', reply_markup=current_page)
            else:
                bot.answer_callback_query(call.id, "Bro son finite le pagine, inutile che premi")
    # 2. Selected user
    else:
        username = data
        # Apply
        conn, c = prep_database()
        c.execute("UPDATE users SET has_voted = %s WHERE user_id = %s", (username, call.from_user.id))
        conn.commit()
        conn.close()
        # Send message
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text="<code>Il tuo voto è stato registrato</code>", parse_mode='HTML')
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - fine /vota — ha votato")



def create_vote_keyboard(team):
    # (copied and modified from create_heal_keyboard)
    ### Read all users of the team from database
    all_users = get_list_of_users(only_team=team)
    # Establish the max number of users per page
    max_users_per_page = 10
    # Separate users into sub-lists of at most 10 users
    ## Explanation (sorta copypasted from chatGPT):
    ## 'range(start, stop, step)': creates a range of indices, starting from 0 and incrementing by max_users_per_page at each step. It ensures that you get the starting index of each sub-list.
    ## 'all_users[i:i + max_users_per_page]: this is list slicing. For each index i obtained from the range, it creates a sub-list starting from index i and ending at i + max_users_per_page. This sub-list represents a chunk of at most max_users_per_page users from the original list.
    ## the entire one-liner: this is list comprehension (that's why it's in brackets). It iterates over the range of indices obtained in step 1 and creates a new list (keyboard_pages) 
    user_pages = [all_users[i:i + max_users_per_page] for i in range(0, len(all_users), max_users_per_page)]
    # user_pages is a list of lists. Each list contains strings of usernames
    # now we want to turn it into a list of lists where each list contains a button
    inline_keyboard_pages = []
    for page_number, page in enumerate(user_pages):
        # Here I'm using the telebot.util.quick_markup syntax; bc otherwise, row_width is broken (whereas I want 2 users per row)
        # The whole keyboard is a dictionary, and each button is just a dictionary entry. No lists no stuff
        keyboard = {}
        for user in page:
            keyboard[f"@{user}"] = {"callback_data": f"v1__{page_number}__{user}__{team}"}    #the callback_data has an h1__ that makes it stateless
        # And at the bottom of the page, add the two buttons to navigate pages (using some fancy syntax)
        keyboard.update({f"{button}" : {"callback_data": f"v1__{page_number}__{button}__{team}"} for button in ["<", ">"]})
        # This page is done, can add it to the list of all pages!
        inline_keyboard_pages.append(keyboard)
    # Done! Return now (note that unlike some other keyboard-creator functions, this one does not return the text as well; indeed, it doesn't even return the actual keyboard, just a list of possible keyboards)
    return inline_keyboard_pages




















##############
# DONAZIONE #
##############
@bot.message_handler(commands=['dona'])
@ignore_dead_users
@ignore_group_messages
def donate_starter(message):
    text = "Vuoi donare denaro a un cittadino o alla cassa di un team?"
    inline_keyboard = {
        'A un cittadino' : {'callback_data' : 'don1 utente'},
        'A un team' : {'callback_data' : 'don1 team'}
        }
    inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
    bot.send_message(message.from_user.id, text, reply_markup=inline_keyboard)
    telegram_logger.info(f"User {get_user_link(message.from_user.id)} - inizio /dona")

@bot.callback_query_handler(func=lambda message: message.data.startswith("don1 utente"))
def donate_to_user_select_user(call):
    if call.data == 'don1 utente':    #i.e. the first time when it comes directly from donate_starter
        # Display the first page only
        list_of_pages = create_keyboard_of_users(call.data, get_list_of_users(only_alive=True, exclude_self=call))
        text_select_user = "A chi è destinata questa tangente?"
        display_page_number(list_of_pages, 0, text_select_user, call)
    else:
        # Possible situations: 1. changed page of keyboard 2. pressed on target user
        if has_changed_page(call):
            new_page_number = change_page_number(call)
            text = "A chi vuoi donare!?"
            display_page_number(create_keyboard_of_users(call.data), new_page_number, text, call)
        else:
            call.data += " 1"
            new_call = call.data.replace('don1', 'don2', 1)
            call.data = new_call
            donate_choose_amount(call)

@bot.callback_query_handler(func=lambda message: message.data.startswith("don1 team"))
def donate_to_team_select_team(call):
    if call.data == 'don1 team':         #i.e. the first time when it comes directly from donate_starter
        teams = ['BLU', 'ROSSO', 'NERO']
        inline_keyboard = {}
        for team in teams:
            inline_keyboard[f"Team {team}"] = {'callback_data' : f'don1 team {team}'}
        inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
        text_select_user = "A quale team vuoi donare?"
        bot.edit_message_text(text_select_user, call.from_user.id, call.message.message_id, parse_mode='HTML', reply_markup=inline_keyboard)
    else:       #i.e. after they have clicked on a team
        call.data += " 1"
        new_call = call.data.replace('don1', 'don2', 1)
        call.data = new_call
        donate_choose_amount(call)



@bot.callback_query_handler(func=lambda message: message.data.startswith("don2"))
def donate_choose_amount(call):
    target_category = call.data.split(' ')[1]
    if target_category == 'team':       # 'don2 team NERO 1'
        current_amount = int(call.data.split(' ')[3])
    elif target_category == 'utente':     # 'don2 utente 0 181449747 1'
        current_amount = int(call.data.split(' ')[4])
    keyboard_buttons = [1, 10, 100, 1000]
    range_valid_amount = [1, 10000]
    text_pt1 = "Quanto vuoi donare? \n\nDonazione:"
    text_pt2 = "soldi"
    done = amount_keyboard_message_sender(call, keyboard_buttons, range_valid_amount, current_amount, text_pt1, text_pt2)
    if done:    #i.e. if pressed 'fatto'
        donate_apply(call)

def donate_apply(call):
    # First, check they do have the money
    amount = int(call.data.split(' ')[-2])
    if not check_if_enough_money(call.from_user.id, amount):
        bot.answer_callback_query(call.id, "Non hai tutti quei soldi! Sei un poveraccio!", show_alert=True)
        return
    # Apply
    category = call.data.split(' ')[1]
    donator_id = call.from_user.id
    if category == 'team':
        target = call.data.split(' ')[2]
        transfer_money_to_team(donator_id, target, amount)
    elif category == 'utente':
        target = call.data.split(' ')[3]
        transfer_money(donator_id, target, amount)
    # Send messages and Log
    donator_link = get_user_link(donator_id)
    if category == 'team':
        text_to_donator = f"<b>Riassunto operazione:</b> \n\nHai donato <i>{amount} soldi</i> alla cassa del team {target}!"
        text_to_recipient = f"<b>{donator_link} ha appena donato {amount} soldi alla cassa del team!!</b>"
        # Retrieve ID of leader of recipient team
        leader_id = retrieve_team_leader(target)
        # Send
        bot.edit_message_text(text_to_donator, call.from_user.id, call.message.message_id, parse_mode='HTML')
        bot.send_message(leader_id, text_to_recipient, 'HTML')
    elif category == 'utente':
        recipient_link = get_user_link(target)
        text_to_donator = f"<b>Riassunto operazione:</b> \n\nHai donato <i>{amount} soldi</i> a {recipient_link}!"
        text_to_recipient = f"<b>{donator_link} ti ha appena donato {amount} soldi!!</b>"
        # Send the messages
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_to_donator, parse_mode='HTML')
        bot.send_message(chat_id=target, text=text_to_recipient, parse_mode='HTML')
    telegram_logger.info(f"User {donator_link} - fine /dona: - \n\ntesto al donatore: \n{text_to_donator} \n\ntesto al donato: \n{text_to_recipient}")




















###############
# CAMBIA TEAM #
###############
@bot.message_handler(commands=['cambiateam'])
@ignore_dead_users
@ignore_group_messages
def change_team(message):
    teams = ['ROSSO', 'BLU', 'NERO']
    # Check that user is not the leader, and retrieve team
    conn, c = prep_database()
    c.execute("SELECT team_role, team FROM users WHERE user_id = %s", (message.from_user.id,))
    team_role, team = c.fetchone()
    if team_role == 'leader':
        bot.reply_to(message, "Sei il leader! Non puoi cambiare team!")
        return
    conn.close()
    teams.remove(team)
    inline_keyboard = {team : {'callback_data' : f'cambiateam__{message.from_user.username}__{team}'} for team in teams}
    inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
    bot.send_message(message.from_user.id, "A quale team vuoi passare?", reply_markup=inline_keyboard)
    telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /cambiateam")

@bot.callback_query_handler(func=lambda message: message.data.startswith("cambiateam"))
def change_team_selected_team(call):
    username, team = call.data.split('__')[1:3]
    # Retrieve ID of the leader of that team
    conn, c = prep_database()
    c.execute("SELECT user_id FROM users WHERE team = %s AND team_role = 'leader'", (team,))
    leader_id = c.fetchone()[0]
    conn.close()
    # Send messages
    text_to_requester = f"<b>La richiesta è stata inviata al leader del team {team}!</b> \nQuando la accetterà, avrai cambiato ufficialmente team."
    bot.edit_message_text(text_to_requester, call.from_user.id, call.message.message_id, parse_mode='HTML')
    inline_keyboard = {
        "SI PIÙ POPOLO PIÙ POTERE" : {'callback_data' : f'confermacambiateam__sì__{username}__{team}__{call.from_user.id}'},
        "No, niente snitch" : {'callback_data' : f'confermacambiateam__no'}
    }
    inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=1)
    user_link = get_user_link(call.from_user.id)
    text_to_accepter = f"<u>{user_link} ha mandato una richiesta per unirsi al tuo team!</u> \nAccetti?"
    bot.send_message(leader_id, text_to_accepter, 'HTML', reply_markup=inline_keyboard)
    telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - in /cambiateam - \n\n{text_to_accepter}")

@bot.callback_query_handler(func=lambda message: message.data.startswith("confermacambiateam"))
def change_team_gave_confirmation(call):
    response = call.data.split('__')[1]
    if response == 'sì':
        username, team, user_id = call.data.split('__')[2:5]
        # Apply
        conn, c = prep_database()
        c.execute("UPDATE users SET team = %s WHERE user_id = %s", (team, user_id))
        c.execute("UPDATE users SET team_role = 'nullità' WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()
        # Send messages
        text_to_requester = f"<b>La tua richiesta di passare al team {team} è stata accettata!</b>"
        text_to_accepter = f"Ora @{username} fa parte del team!"
        bot.send_message(user_id, text_to_requester, 'HTML')
        bot.edit_message_text(text_to_accepter, call.from_user.id, call.message.message_id, parse_mode='HTML')
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - fine /cambiateam - \n\n{text_to_requester}")
    elif response == 'no':
        bot.edit_message_text("Ok bro.", call.from_user.id, call.message.message_id)
        telegram_logger.info(f"Utente {get_user_link(call.from_user.id)} - fine /cambiateam - richiesta rifiutata")




    




#########################
# CANCELLAZIONE PROFILO #
#########################
# Percorso: delete -> confirm_deletion
@bot.message_handler(commands=['delete'])
def delete(message):
    # Ask for confirmation
    bot.reply_to(message, "Are you sure you want to delete your profile? You will be erased from the database and all information will be lost. Press /yes to proceed.")
    # Register a new message handler to handle the confirmation
    # Second argument is a callback, i.e. the function that will be elicited when the next message arrives
    bot.register_next_step_handler(message, confirm_deletion)
    telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - /delete")

def confirm_deletion(message):
    if message.text.lower() == '/yes':
        # Get the user's telegram ID
        user_telegram_id = message.from_user.id
        # Delete the user's profile from the database
        conn, c = prep_database()
        c.execute('DELETE FROM users WHERE user_id = %s', (user_telegram_id,))
        c.execute('DELETE FROM teams WHERE user_id = %s', (user_telegram_id,))
        c.execute('DELETE FROM armory WHERE user_id = %s', (user_telegram_id,))
        c.execute('DELETE FROM inventory WHERE user_id = %s', (user_telegram_id,))
        c.execute('DELETE FROM job WHERE user_id = %s', (user_telegram_id,))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        # Send a confirmation message
        bot.reply_to(message, "Your profile has been deleted. Wait a second... who are you?")
        telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - fine /delete - profilo cancellato")
    else:
        bot.reply_to(message, "Deletion canceled. Your profile is safe.")


# Instructions to handle every non-command message
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Bruh")
        telegram_logger.info(f"Utente {get_user_link(message.from_user.id)} - messaggio di testo: {message.text}")
    if message.text.lower().startswith("send"):
        admin_send_message(message)
    if message.forward_from:
        user_id = message.forward_from.id
        first_name = message.forward_from.first_name
        telegram_logger.info(f"ID: {user_id} \nFirst name: {first_name}")


# questo è parte del vecchio paradigma. non usare per le nuove funzioni
############################
# INLINE CALLBACK HANDLING #
############################
@bot.callback_query_handler(func=lambda message: True)
def handle_inline_callback(call):
    # This function is a general dispatcher for all inline buttons, that sends to the correct function depending on the situation
    user_id = call.from_user.id
    # Checks if the user is in the middle of team choice
    if user_states.get(user_id) == "waiting_for_team_choice":
        process_team_selection(call)
    # Checks if the user is in the middle of skill points allocation
    elif user_states.get(user_id) == "waiting_for_skill_points_allocation":
        process_skill_points_allocation(call)
    # Checks if the user is browsing the menu
    elif user_states.get(user_id) == "browsing_menu":
        process_personal_menu(call)
    elif user_states.get(user_id) in ["browsing_menu_zaino", "browsing_menu_zaino_usaoggetti"]:
        process_personal_menu_zaino(call)
    elif user_states.get(user_id) == "browsing_menu_armeria":
        process_personal_menu_armeria(call)
    # Checks if the user is finding a job
    elif user_states.get(user_id) in ["finding_job", "finding_job_confirmation"]:
        process_find_job(call)

########
# Misc #
########

def luck_modifier(base_bonus, luck_points, var_range):
    """
    Modify the value of a bonus based on luck points.

    Parameters:
    - base_bonus (int): The original bonus value.
    - luck_points (int): The current luck points of the player.
    - var_range (list): The range of accepted variation from base. e.g. [0.8, 1.2] means bonus can range from 80% to 120% of its base

    Returns:
    - int: The modified bonus value.
    """
    #First of all, make sure that base_bonus is INT and not STR
    base_bonus = int(base_bonus)
    # Now we compare the user's luck to the good luck
    luck_factor = luck_points / good_luck
    # Based on this, we decide on what point of the range will the actual bonus fall (closer to the minimum or to the maximum)
    position_in_range = ((var_range[1]-var_range[0])*luck_factor) + var_range[0]
    # Modify the bonus using the position in the range
    modified_bonus = round(base_bonus * position_in_range)
    return modified_bonus


def admin_send_message(message):
    '''
    così io posso mandare messaggi a un utente specifico tramite il bot
    il messaggio dovrebbe essere così: send @username @testo
    così uso la chiocciola come split
    send @all @testo per mandare a tutti gli utenti
    '''
    # Controlla che sono stato io a usare il comando
    if message.from_user.id == admin_id:
        # Estrai lo username o l'ID del gruppo (o all)
        target = message.text.split('@')[1]
        # Rimuovi lo spazio finale
        target = target[:-1]
        # Estrai il messaggio
        text = message.text.split('@')[2]
        # Capisci se è all -> manda a tutti gli utenti registrati
        if target == 'all':
            conn, c = prep_database()
            c.execute("SELECT user_id FROM users")
            ids = c.fetchall()
            conn.close()
            for id_tuple in ids:
                id = id_tuple[0]
                bot.send_message(id, text, 'HTML')
            # Give me feedback
            bot.send_message(admin_id, "Fatto, capo.")
            return
        # Capisci se è uno username o un ID del gruppo
        try:
            target_id = int(target)
        except:
            target_username = target
            # Trova l'ID
            conn, c = prep_database()
            c.execute("SELECT user_id FROM users WHERE username = %s", (target_username,))
            # Controlla che abbia trovato qualcosa
            try:
                target_id = int(c.fetchone()[0])
                conn.close()
            except TypeError:
                bot.send_message(admin_id, "Username non trovato, capo.")
        # Invia
        bot.send_message(target_id, text, parse_mode='HTML')
        # Dammi un feedback
        bot.send_message(admin_id, "Fatto, capo.")
    else:
        bot.reply_to(message, "So dove abiti, vivo nei tuoi muri")



















# per chi sta leggendo: qui sotto ci sono un paio di robe che servono solo a bypassare alcune limitazioni del sito dove hosto
# se runnate in locale potete ignorarle (o cancellarle se danno problemi) e conservare solo il if __name__ == __main__
##########################
# This makes the bot run #
##########################

# the following line is just for convenience; it tells me launch was successful and it pops up the telegram chat
#bot.send_message(admin_id, "Running!")

# Now some stuff for the health check that Render wants
def health_check_handler(request_handler_class=http.server.SimpleHTTPRequestHandler):
    class HealthCheckHandler(request_handler_class):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')

    return HealthCheckHandler

def run_health_check_server(port=5432):
    handler = health_check_handler()
    httpd = socketserver.TCPServer(("", port), handler)

    telegram_logger.info(f"Health check server started on port {port}")
    httpd.serve_forever()

# Send an HTTP request to the health check endpoint; I'll use this to keep the bot awake
def send_health_check_request():
    while True:
        url = "https://golpebot2023.onrender.com/health"
        response = requests.get(url)

        if response.status_code == 200:
            telegram_logger.info("Ho svegliato il bot!")
        else:
            telegram_logger.info(f"Wakeup failed with status code {response.status_code}")
        time.sleep(60*14)    #repeat every 14 minutes

# this is the actual run-maker
if __name__ == '__main__':
    # Start the health check server in a separate thread
    health_check_thread = threading.Thread(target=run_health_check_server, args=(5432,))
    health_check_thread.start()
    # Run the scheduled jobs in a separate thread
    schedule_thread = threading.Thread(target=send_health_check_request)
    schedule_thread.start()
    while True:
        try:
            # Start the telegram bot
            bot.infinity_polling()
        except:
            telegram_logger.warning("Bot rotto x1")
            time.sleep(1)
            try:
                bot.infinity_polling()
            except:
                telegram_logger.warning("Bot rotto x2")
                time.sleep(1)
                try:
                    bot.infinity_polling()
                except:
                    telegram_logger.warning("Bot rotto x3. Ri-deploya")
                    time.sleep(1)