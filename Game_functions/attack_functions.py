import random
from Utils.database_functions import prep_database
from Utils.database_functions import get_user_link
from Utils.database_functions import retrieve_user_hp
from Utils.telebot_init import bot

def weapon_has_ammo(weapon : str, user_id : int):
    conn, c = prep_database()
    c.execute("SELECT ammo FROM armory WHERE arm_name = %s AND user_id = %s", (weapon, user_id))
    ammo = c.fetchone()
    conn.close()
    if ammo:
        return ammo[0]

def user_meets_strength_requirement(call, arm_name : str):
    from golpebot_2023_main import arms    #import here to avoid circular imports
    # Retrieve user strength
    user_id = call.from_user.id
    conn, c = prep_database()
    c.execute("SELECT forza FROM users WHERE user_id = %s", (user_id,))
    user_strength = c.fetchone()[0]
    conn.close()
    # Retrieve arm strength
    arm_strength = arms[arm_name]["required_strength"]
    # Do the math
    if user_strength >= arm_strength:
        return True
    else:
        return False

def retrieve_arm_damage_loudness_strength(weapon):
    from golpebot_2023_main import arms
    damage = arms[weapon]["damage"]
    loudness = arms[weapon]["loudness"]
    strength = arms[weapon]["required_strength"]
    return [damage, loudness, strength]

def retrieve_values_to_calculate_attack(attacker_id : int, weapon : str, target_id : int):
    from golpebot_2023_main import arms    #import here to avoid circular imports
    conn, c = prep_database()
    # For the attacker: forza, fortuna, team_role
    c.execute("SELECT forza, fortuna, team_role FROM users WHERE user_id = %s", (attacker_id,))
    attacker_strength, attacker_luck, attacker_team_role = c.fetchone()
    # For the target: hp
    c.execute("SELECT hp FROM users WHERE user_id = %s", (target_id,))
    target_hp = c.fetchone()[0]
    conn.close()
    # For the weapon: damage, loudness
    damage = arms[weapon]["damage"]
    loudness = arms[weapon]["loudness"]
    return [attacker_strength, attacker_luck, attacker_team_role, damage, loudness, target_hp]

def calculate_damage(attacker_strength : int, attacker_team_role : str, weapon_damage : int):
    # Calculate damage applying modifiers
    damage = weapon_damage + attacker_strength*3       #questo è l'algoritmo che mi sento sia migliore al momento. ovviamente si può cambiare se è squilibrato
    if attacker_team_role == 'soldato':    #give a big bonus if role is soldato
        damage = round(damage * 3)
    return damage

def calculate_loudness_mode(attacker_luck, weapon_loudness):
    # Calculate loudness applying modifiers
    loudness = weapon_loudness - attacker_luck          #questo è l'algoritmo che mi sento sia migliore al momento. ovviamente si può cambiare se è squilibrato
    # Determine if attack is stealth or seen
    if random.randint(1,100) > loudness:
        mode = "stealth"
    else:
        mode = "seen"
    return mode

def calculate_attack_outcome(damage : int, target_hp : int):
    new_hp = target_hp - damage
    if new_hp > 0:
        outcome = "survived"
    else:
        outcome = "killed"
    return outcome

def apply_attack(attacker_id :int, target_id :int, damage :int, weapon :str):
    conn, c = prep_database()
    ## Use one ammo
    c.execute('''UPDATE armory
                    SET ammo = ammo -1
                    WHERE user_id = %s AND arm_name = %s''',
                    (attacker_id, weapon)
                    )
    ## Deal damage (a trigger automatically sets is_alive to FALSE (dead) and time_of_death to current time if hp drops to or below 0)
    c.execute('''UPDATE users
                    SET hp = users.hp - %s
                    WHERE user_id = %s''',
                    (damage, target_id)
                    )
    # Commit
    conn.commit()
    return

def attack_send_messages(call, attacker_id, target_id, weapon, damage, mode, outcome):
    from golpebot_2023_main import hours_to_respawn    #import here to avoid circular imports
    from golpebot_2023_main import group_id

    shooter_link = get_user_link(attacker_id)
    target_link = get_user_link(target_id)
    new_hp = retrieve_user_hp(target_id)
    ## These dicts worsen readability but sensibily reduce IF bifurcations and number of lines
    traduzioni_shooter = {
                "stealth" : "non sa che sei stato tu a spararlo",
                "seen" : "ti ha visto mentre lo sparavi",
                "survived" : "<b>è ancora vivo</b>",
                "killed" : "<b>è morto</b> ammazzato"
                }
    traduzioni_target = {
                "stealth" : "Non sei riuscito a vedere chi è stato",
                "seen" : f"L'hai visto in faccia! <b>È stato {shooter_link}</b>",
                "survived" : f"<b>Sei ancora vivo</b>, hai {new_hp} punti salute",
                "killed" : f"<b><u>Sei schiattato!</u></b> <i>(potrai respawnare fra {hours_to_respawn} ore)</i>"
    }
    text_to_shooter = f"<code>Procedura di attacco terminata</code> \n\nHai inflitto {damage} danni a {target_link} con {weapon}. \n\n{target_link} {traduzioni_shooter[outcome]}. \n\n{target_link} {traduzioni_shooter[mode]}."
    text_to_target = f"<b><u>Sei stato sparato!!</u></b> \n\n{traduzioni_target[outcome]} \n\n{traduzioni_target[mode]}"
    ## To shooter
    bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_to_shooter, parse_mode='HTML')
    ## To target
    try:    # this allows me to do testing with strawmen
        bot.send_message(chat_id=target_id, text=text_to_target, parse_mode='HTML')
    except:
        pass
    # To global group
    if mode == 'stealth':
        bot.send_message(group_id, f'<i>Qualcuno</i> ha sparato {target_link}!', 'HTML')
    elif mode == 'seen':
        bot.send_message(group_id, f'{shooter_link} ha sparato {target_link}!', 'HTML')
    return [text_to_shooter, text_to_target]
