from Utils.database_functions import prep_database, get_user_link
from Utils.telebot_init import bot

def check_if_enough_money(user_id, price):
    conn, c = prep_database()
    c.execute("SELECT bank FROM users WHERE user_id = %s", (user_id,))
    bank = c.fetchone()[0]
    conn.close()
    if bank >= price:
        return True
    else:
        return False

def transfer_money(giver_id, taker_id, amount):
    conn, c = prep_database()
    # Give to taker
    c.execute("UPDATE users SET bank = users.bank + %s WHERE user_id = %s", (amount, taker_id))
    # Take from giver
    c.execute("UPDATE users SET bank = users.bank - %s WHERE user_id = %s", (amount, giver_id))
    conn.commit()
    conn.close()

def transfer_money_to_team(giver_id, team : str, amount):
    conn, c = prep_database()
    # Give to team
    c.execute("UPDATE teams SET bank = teams.bank + %s WHERE team = %s", (amount, team))
    # Take from giver
    c.execute("UPDATE users SET bank = users.bank - %s WHERE user_id = %s", (amount, giver_id))
    conn.commit()
    conn.close()


def transfer_item(giver_id, taker_id, item, taker_username=None):
    conn, c = prep_database()
    # this execute is chatGPT's work
    # this way, if user had 0 of the bought item, it adds a new row, but if user already had some, it just ups the quantity
    c.execute('''
        INSERT INTO inventory (user_id, username, item_name, quantity)
        VALUES (%s, %s, %s, 1)
        ON CONFLICT(user_id, item_name) DO UPDATE SET quantity = inventory.quantity + 1
    ''',
    (taker_id, taker_username, item)
    )
    # And now take from the giver
    c.execute("UPDATE inventory SET quantity = inventory.quantity - 1 WHERE user_id = %s AND item_name = %s", (giver_id, item))
    conn.commit()
    conn.close()

def transfer_weapon(giver_id, taker_id, weapon, taker_username=None):
    conn, c = prep_database()
    # Unlike items, you can only have one arm. So, first I check you don't already have it.
    c.execute("SELECT * FROM armory WHERE user_id = %s AND arm_name = %s", (taker_id, weapon))
    if c.fetchall():        #if user already had that weapon
        raise ValueError
    c.execute('''
        INSERT INTO armory (user_id, username, arm_name)
        VALUES (%s, %s, %s)
    ''',
    (taker_id, taker_username, weapon)
    )
    # And now take from the giver
    c.execute("DELETE FROM armory WHERE user_id = %s AND arm_name = %s", (giver_id, weapon))
    conn.commit()
    conn.close()

def transfer_ammo(giver_id, taker_id, ammo):
    conn, c = prep_database()
    # You can only have ammo for weapons you own
    c.execute("SELECT * FROM armory WHERE user_id = %s AND arm_name = %s", (taker_id, ammo))
    if not c.fetchall():        #if user didn't already have that weapon
        raise ValueError
    c.execute("UPDATE armory SET ammo = armory.ammo + 1 WHERE user_id = %s AND arm_name = %s", (taker_id, ammo))
    c.execute("UPDATE armory SET ammo = armory.ammo - 1 WHERE user_id = %s AND arm_name = %s", (giver_id, ammo))
    conn.commit()
    conn.close()



def sell_send_messages(call, seller_id, buyer_id, category, thing, price):
    seller_link = get_user_link(seller_id)
    buyer_link = get_user_link(buyer_id)
    if category == 'ammo':
        thing = f"Munizioni {thing}"
    text_to_buyer = f"<b>Hai comprato {thing} da {seller_link} per {price} soldi!</b> 💸💸💸 \n\nPuoi trovarlo nel /menu"
    text_to_seller = f"<b>{buyer_link} ha accettato la tua offerta di {price} soldi per {thing}!</b> 🤑🤑🤑"
    # To buyer
    bot.edit_message_text(text_to_buyer, buyer_id, call.message.message_id, parse_mode='HTML')
    # To seller
    bot.send_message(seller_id, text_to_seller, 'HTML')
    return [text_to_seller, text_to_buyer]