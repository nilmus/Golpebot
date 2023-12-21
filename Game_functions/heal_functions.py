from Utils.database_functions import prep_database, get_user_link, retrieve_time_column, retrieve_user_hp
from Utils.telebot_init import bot

def retrieve_values_to_calculate_heal(healer_id : int, healed_id : int):
    conn, c = prep_database()
    # For the attacker: intelligenza, team_role
    c.execute("SELECT intelligenza, team_role FROM users WHERE user_id = %s", (healer_id,))
    healer_intelligence, healer_team_role = c.fetchone()
    # For the target: is_alive
    c.execute("SELECT intelligenza, fortuna FROM users WHERE user_id = %s", (healed_id,))
    is_alive = c.fetchone()[0]
    conn.close()
    return [healer_intelligence, healer_team_role, is_alive]



def calculate_heal_hp(healer_intelligence, healer_team_role):
    from golpebot_2023_main import good_intelligence    #import here to avoid circular imports
    healing = round((healer_intelligence / good_intelligence) *1000)
    # Give big role bonus if medico
    if healer_team_role == 'medico':
        healing = round(healing * 3)
    return healing

def apply_heal_hp(healed_id, hps):      # it's willingly NOT capped to 1000; to encourage regular... medical checkups
    conn, c = prep_database()
    c.execute("UPDATE users SET hp = users.hp + %s WHERE user_id = %s", (hps, healed_id))
    conn.commit()
    conn.close()



def calculate_shorten_respawn(healer_intelligence, healer_team_role):
    from golpebot_2023_main import good_intelligence, hours_to_respawn    #import here to avoid circular imports
    # Can heal from 0 to 12h (i.e. the whole respawn time), based on ratio between user's intelligence and the good_intelligence (global variable)
    shortening_hours = round((healer_intelligence / good_intelligence) *hours_to_respawn)
    # Give big role bonus if medico
    if healer_team_role == 'medico':
        shortening_hours = round(shortening_hours * 3)
    return shortening_hours


def apply_shorten_respawn(healed_id, shortening_hours):
    import datetime
    time_of_death = retrieve_time_column(healed_id, 'time_of_death')
    time_of_death = datetime.datetime.strptime(time_of_death, "%d/%m/%Y %H:%M")
    conn, c = prep_database()
    time_of_death = time_of_death - datetime.timedelta(hours=shortening_hours)
    c.execute("UPDATE users SET time_of_death = %s WHERE user_id = %s", (time_of_death.strftime('%d/%m/%Y %H:%M'), healed_id))
    conn.commit()
    conn.close()





def heal_send_messages(healer_id, healed_id, is_alive, hp_or_hours, call):
    healer_link = get_user_link(healer_id)
    healed_link = get_user_link(healed_id)
    if is_alive:
        new_hp = retrieve_user_hp(healed_id)
        text_to_healer = f"Hai guarito {healed_link} di {hp_or_hours} punti salute. \n\n<i>Per migliorare la tua guarigione, potenzia la tua intelligenza</i>"
        text_to_healed = f"Sei stato guarito da {healer_link} di {hp_or_hours} punti salute. \nAdesso hai {new_hp} punti salute."
    else:
        text_to_healer = f"Hai accorciato il tempo di respawn di {healed_link} di {hp_or_hours} ore. \n\n<i>Per migliorare la tua guarigione, potenzia la tua intelligenza</i>"
        text_to_healed = f"Il tuo tempo di respawn è stato accorciato da {healer_link} di {hp_or_hours} ore."
    bot.edit_message_text(text_to_healer, healer_id, call.message.message_id, parse_mode='HTML')
    bot.send_message(healed_id, text_to_healed, 'HTML')
    return [text_to_healer, text_to_healed]