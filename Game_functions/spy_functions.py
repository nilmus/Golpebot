import random
from Utils.database_functions import prep_database
from Utils.database_functions import get_user_link
from Utils.telebot_init import bot

def retrieve_values_to_calculate_spy(spier_id : int, target_id : int):
    conn, c = prep_database()
    # For the attacker: intelligenza, fortuna, team_role
    c.execute("SELECT intelligenza, fortuna, team_role FROM users WHERE user_id = %s", (spier_id,))
    spier_intelligence, spier_luck, spier_team_role = c.fetchone()
    # For the target: intelligenza, fortuna
    c.execute("SELECT intelligenza, fortuna FROM users WHERE user_id = %s", (target_id,))
    target_intelligence, target_luck = c.fetchone()
    conn.close()
    return [spier_intelligence, spier_luck, spier_team_role, target_intelligence, target_luck]

def calculate_success(spier_luck : int, spier_team_role : str, target_luck : int):
    # Apply modifiers
    success_percent = spier_luck*2 - target_luck       #questo è l'algoritmo che mi sento sia migliore al momento. ovviamente si può cambiare se è squilibrato
    if spier_team_role == 'spia':    #give a big bonus if role is spia
        success_percent = round(success_percent * 3)
    # Calculate success
    success_percent = min(success_percent, 100)     # Cap to 100 (while there's no minimum cap, can be below 0 (in that case, % will be lower than 1 but still higher than 0))
    success_weights = [success_percent, 100]        # Use cum_weights and random.choices
    success = random.choices([True, False], cum_weights=success_weights, k=1)[0]    #the [0] is otherwise it holds a list, instead of a boolean
    return success

def calculate_extent(spier_intelligence : int, spier_team_role : str, target_intelligence : int):
    '''
    Returns a number from 1 to k
    where k is the number of spyable parameters; currently 10
    '''
    # Apply modifiers
    extent_percent = spier_intelligence*2 - target_intelligence
    if spier_team_role == 'spia':
        extent_percent = round(extent_percent * 3)
    # Calculate extent
    extent_percent = min(extent_percent, 100)       # Cap to 100 (while there's no minimum cap, can be below 0)
    extent_weights = [extent_percent, 100]          # Use cum_weights
    extent = random.choices([True, False], cum_weights=extent_weights, k=10)    # Here the K is the number of spyable parameters; might need to modify it
    extent = extent.count(True)        # I don't know how to explain it but I think you get it. If not, I'm sorry.
    extent = max(1, extent)            # Has to be at least 1
    return extent


def apply_spy(success, extent, target_id):
    '''
    Returns one of: 1. calderone (list) 2. 'simple failure' 3. 'catastrophic failure'
    '''
    if success:
        ## Funziona che prende tutto dalle varie tables, mette tutto in una lista-calderone, e pesca i valori da rilevare, tanti quanti l'extent
        calderone = []
        conn, c = prep_database()
        ## 1. da USERS
        c.execute('''SELECT team, bank, forza, intelligenza, fortuna, is_alive, hp, time_of_death, team_role
                    FROM users
                    WHERE user_id = %s''',
                    (target_id,)
                    )
        # Here a little IF is needed so that according to user being alive or dead, only HP or time_of_death is shown, respectively
        calderone.extend(c.fetchone())    #this step is needed bc tuples are immutable    (note that it's EXTEND, not APPEND, so that it unpacks the iterable)
        if calderone[5]:        #if user is alive
            calderone.pop(7)     #remove the t.o.d.
        elif not calderone[5]:  #if user is dead
            calderone.pop(6)     #remove the hp
        ## 2. da INVENTORY
        c.execute('''SELECT item_name, quantity
                    FROM inventory
                    WHERE user_id = %s''',
                    (target_id,)
                    )
        calderone.append({item_name : quantity for item_name, quantity in c.fetchall()})    # This handles empty inventories (adds an empty dict)
        ## 3. da ARMORY
        c.execute('''SELECT arm_name, ammo
                    FROM armory
                    WHERE user_id = %s''',
                    (target_id,)
                    )
        calderone.append({arm_name : ammo for arm_name, ammo in c.fetchall()})              # This handles empty armories (adds an empty dict)
        # Now based on the EXTENT, pick a certain number of things that will be revealed
        revealed_indices = [i for i in random.sample(range(len(calderone)), extent)]
        # And replace all the others with nonsense
        calderone = [calderone[index] if index in revealed_indices else "???" for index in range(len(calderone))]
        conn.close()
        return calderone
    elif not success:
        # Determine if it's a simple failure or a catastrophic failure
        if extent >= 3:
            return 'simple failure'
        else:
            return 'catastrophic failure'



def spy_send_messages(outcome, spier_id, target_id, call):
    spier_link = get_user_link(spier_id)
    spied_link = get_user_link(target_id)
    if type(outcome) == list:
        calderone = outcome
        
        ## The trickiest part is parsing zaino and armeria
        inventory = calderone[8]
        armory = calderone[9]
        
        if type(inventory) == dict:    # this checks whether it's been revealed or not (bc if not, it's that "???" string!)
            if len(inventory) > 0:
                text_inventory = ", ".join([f"{item_name} ({quantity})" for item_name, quantity in inventory.items()])
            else:
                text_inventory = "vuoto"
        elif type(inventory) == str:
            text_inventory = inventory    # i.e. assign to the "???" string
        
        if type(armory) == dict:
            if len(armory) > 0:            # same as above, checks whether it's been revealed or not
                text_armory = ", ".join([f"{arm_name} ({ammo})" for arm_name, ammo in armory.items()])
            else:
                text_armory = "vuota"
        elif type(armory) == str:
            text_armory = armory          # i.e. assign to "???"
        

        ## The second tricky part is is_alive, bc hp/tod depends on it
        is_alive = calderone[5]
        if type(is_alive) == bool:
            if is_alive:
                text_is_alive = "vivo"
                text_hp_or_tod = "Punti salute"
            elif not is_alive:
                text_is_alive = "morto"
                text_hp_or_tod = "Data del decesso"
        elif type(is_alive) == str:
            text_is_alive = is_alive    # i.e. keep the "???"
            text_hp_or_tod = "???"      # perchè sì
        
        
        # To spiante
        text_to_spiante = f'''<code>Procedura di spionaggio terminata</code> \n\nEcco cosa hai scoperto su {spied_link} \n\n\
Team: <span class="tg-spoiler">{calderone[0]}</span>
Ruolo nel team: <span class="tg-spoiler">{calderone[7]}</span>
Forza: <span class="tg-spoiler">{calderone[2]}</span>
Intelligenza: <span class="tg-spoiler">{calderone[3]}</span>
Fortuna: <span class="tg-spoiler">{calderone[4]}</span>
Soldi in banca: <span class="tg-spoiler">{calderone[1]}</span>
Attualmente: <span class="tg-spoiler">{text_is_alive}</span>
{text_hp_or_tod}: <span class="tg-spoiler">{calderone[6]}</span>
Zaino: <span class="tg-spoiler">{text_inventory}</span>
Armeria: <span class="tg-spoiler">{text_armory}</span>

(Se vuoi cogliere più informazioni dagli spionaggi, aumenta la tua <i>intelligenza</i>)
'''

        # To spiato: niente! Se uno spionaggio va bene, lo spiato non lo sa neanche
        text_to_spiato = ""

    elif outcome == 'simple failure':
        text_to_spiante = f"<code>Procedura di spionaggio terminata</code> \n\nNon sei riuscito a scoprire niente! \n\n<i>(Per migliorare il tuo spionaggio, aumenta la tua fortuna)</i>"
        text_to_spiato = "Hai la strana sensazione che qualcuno abbia appena provato a spiarti ma abbia fallito..."
    elif outcome == 'catastrophic failure':
        text_to_spiante = f'''Sei un fallito! \nNon solo non sei riuscito a scoprire niente, ma ti sei anche fatto beccare. \nOra {spied_link} sa che hai provato a spiarlo \n
<i>(Per migliorare il tuo spionaggio, aumenta la tua fortuna)</i>'''
        text_to_spiato = f'''Vedi un individuo in un impermeabile giallo alla tua finestra, che prova a scattarti una foto, ma teneva la fotocamera al contrario!
Scappa imbarazzato, ma l'hai visto, è {spier_link} \n\n<code>(Tentativo di /spionaggio fallito)</code>'''

    # Regardless of the outcome:
    bot.edit_message_text(message_id=call.message.message_id, chat_id=spier_id, text=text_to_spiante, parse_mode='HTML')
    if text_to_spiato:    #bc it might be None, in case of success
        bot.send_message(target_id, text_to_spiato, 'HTML')
    return text_to_spiante, text_to_spiato    #it goes into the logger