from Utils.database_functions import *
from Utils.telebot_init import bot

def golpe_check():
    # Check 2 conditions of reigning team: 1. Leader is dead 2. 50%+1 of politicians are dead
        # First retrieve which team is reigning
        reigning_team = retrieve_reigning_team()
        # Now check condition #1 (Leader is dead)
        if not is_team_leader_alive(reigning_team):
            return 'Leader'
        # Now check condition #2 (50%+1 of politicians is dead)
        if not is_50percent_politicians_alive(reigning_team):
            return 'Politici'
        else:
            return False


def golpe_messages_after_attack(successful, message_or_call):
    '''
    Successful is the result of golpe_check(); can be 'Leader', 'Politici', or False
    Situation is either 'after_attack' or 'at_update' or 'at_times_up'
    '''
    from golpebot_2023_main import group_id    #I moved this import here bc otherwise circular imports!

    user_id = message_or_call.from_user.id
    reigning_team = retrieve_reigning_team()
    golping_team = retrieve_golping_team()
    if successful:
        if successful == 'Leader':
            text_to_final_killer = "<b><u>HAI UCCISO IL LEADER. \nIL GOLPE HA AVUTO SUCCESSO.</u></b> \n\nOra siete voi a comandare."
            bot.send_message(user_id, text_to_final_killer, 'HTML')
        elif successful == 'Politici':
            text_to_final_killer = "<b><u>HAI UCCISO L'ULTIMO POLITICO. \nIL GOLPE HA AVUTO SUCCESSO.</u></b> \n\nOra siete voi a comandare."
            bot.send_message(user_id, text_to_final_killer, 'HTML')
        text_to_group = f"<b><u>IL GOLPE HA AVUTO SUCCESSO. \n\nIL TEAM {golping_team} HA ROVESCIATO IL TEAM {reigning_team}</u></b>"
        bot.send_message(group_id, text_to_group, 'HTML')
    else:
        # Send update on golpe status
        number_to_kill, dead_politicians = is_50percent_politicians_alive(reigning_team)['number_to_kill'], is_50percent_politicians_alive(reigning_team)['dead_politicians']
        text_to_killer = f"<i>Update sul GOLPE</i> \n\nIl leader è ancora in vita. \n\nNumero totale di politici da uccidere: {number_to_kill} \nNumero di politici uccisi: {dead_politicians}"
        bot.send_message(user_id, text_to_killer, 'HTML')


def golpe_consequences(successful : bool):
    '''
    if golpanti won, assign successful=True
    if golpanti lost, assign successful=False
    '''
    # Retrieve which is which
    if successful:
        winning_team = retrieve_golping_team()
        losing_team = retrieve_reigning_team()
    elif not successful:
         winning_team = retrieve_reigning_team()
         losing_team = retrieve_golping_team()
    # Update statuses
    conn, c = prep_database()
    c.execute("UPDATE teams SET status = 'regnante' WHERE team = %s", (winning_team,))
    c.execute("UPDATE teams SET status = 'neutrale' WHERE team = %s", (losing_team,))
    # Steal the bank
    c.execute("SELECT bank FROM teams WHERE team = %s", (losing_team,))
    bank = c.fetchone()[0]
    c.execute("UPDATE teams SET bank = bank + %s WHERE team = %s", (bank, winning_team))
    c.execute("UPDATE teams SET bank = 0 WHERE team = %s", (losing_team,))
    ####################
    # Steal the armory #
    ####################
    # Commit and close
    conn.commit()
    conn.close()
    return 'Success'