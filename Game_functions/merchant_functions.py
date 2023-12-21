from Utils.database_functions import prep_database

merchant_start_keyboard = {
        "Compra oggetti" : {'callback_data' : 'mer1 item'},
        "Compra armi" : {'callback_data' : 'mer1 arm'},
        "Compra munizioni" : {'callback_data' : 'mer1 ammo'}
    }

texts_if_empty = {
    'item' : "<i>Il mercante ha esaurito tutti gli oggetti!</i> \nProva con le armi o con le munizioni.",
    'arm' : "<i>Il mercante ha esaurito tutte le armi!</i> \nProva con gli oggetti o con le munizioni.",
    'ammo' : "<i>Il mercante ha esaurito tutte le munizioni!</i> \nProva con gli oggetti o con le armi."
}

def retrieve_merchant_goods(category):
    conn, c = prep_database()
    c.execute("SELECT item_name, quantity FROM merchant WHERE quantity > 0 AND type = %s ", (category,))
    goods = c.fetchall()
    conn.close()
    return goods

def retrieve_merchant_quantity(item):
    conn, c = prep_database()
    c.execute("SELECT quantity FROM merchant WHERE item_name = %s", (item,))
    quantity = c.fetchone()
    conn.close()
    if not quantity:   #item might not be present in merchant database, for some reason
        return None
    return quantity[0]

def retrieve_merchant_price(item):
    conn, c = prep_database()
    c.execute("SELECT price FROM merchant WHERE item_name = %s", (item,))
    price = c.fetchone()
    conn.close()
    if not price:   #item might not be available at the merchant
        return None
    return price[0]

def retrieve_list_price(item, category):
    if category == 'item':
        from golpebot_2023_main import items
        list_price = items[item]["list_price"]
    elif category == 'arm':
        from golpebot_2023_main import arms
        list_price = arms[item]["list_price"]
    elif category == 'ammo':
        from golpebot_2023_main import arms
        arm_name = item.split('-')[1]   #bc "Munizioni-arma" syntax
        arm_price = arms[arm_name]["list_price"]
        list_price = arm_price / 10
    return list_price

def retrieve_list_description(item, category):
    if category == 'item':
        from golpebot_2023_main import items
        list_description = items[item]["description"]
    elif category == 'arm':
        from golpebot_2023_main import arms
        list_description = arms[item]["description"]
    elif category == 'ammo':
        list_description = f"Munizioni per {item}"
    return list_description

def merchant_create_description(item, category, price):
    
    list_price = retrieve_list_price(item, category)
    price_difference = price - list_price
    if price_difference < 0: 
        discount_text = f"(Sconto di {price_difference} soldi!!🤑🤑📉)"
    elif price_difference == 0:
        discount_text = "(Nessuno sconto)"
    elif price_difference > 0:
        discount_text = f"(Sovrapprezzo di {price_difference} soldi!!💸💸📈)"
    
    list_description = retrieve_list_description(item, category)

    if category == 'arm':       #then must also retrieve damage and loudness; another difference: should NOT ask how many!
        from Game_functions.attack_functions import retrieve_arm_damage_loudness_strength
        damage, loudness, required_strength = retrieve_arm_damage_loudness_strength(item)
        merchant_text = f"<b>Arma: {item}</b> \n\n{list_description} \n\nDanno: {damage} \nRumore: {loudness}/100 \nForza richiesta: {required_strength} \n\nPrezzo: {price} soldi \n{discount_text} \n\n<u><i>Vuoi comprarla?</i></u>"
    elif category == 'item' or category == 'ammo':
        merchant_text = f"<b>Oggetto: {item}</b> \n\n{list_description} \n\nPrezzo: {price} soldi \n{discount_text} \n\n<u><i>Quanti ne vuoi?</i></u> \n"
    
    return merchant_text






def merchant_confirmation_text(item, category, quantity=1):
    
    unit_price = retrieve_merchant_price(item)
    total_price = unit_price * quantity

    if category == 'item' or category == 'ammo':
        confirmation_text = f"Quindi vuoi comprare {quantity} {item}? \nViene {total_price} soldi, va bene?"
    elif category == 'arm':
        confirmation_text = merchant_create_description(item, category, unit_price)
    
    return confirmation_text


def merchant_confirmation_keyboards(item, category, quantity=1):
    '''Can omit quantity if buying an arm'''
    from Utils.telebot_init import telebot
    
    if category == 'item':
        confirmation_keyboard = {
                "SI SI SI" : {'callback_data' : f'mer9 sì {item} {category} {quantity}'},
                "No, ho perso la corsa della vita a causa di quella robaccia" : {'callback_data' : f'mer9 no {category}'}
            }
    elif category == 'arm':
        confirmation_keyboard = {
                "SI SI SI" : {'callback_data' : f'mer9 sì {item} {category} {quantity}'},
                "No, la penna ferisce più della spada" : {'callback_data' : f'mer9 no {category}'}
            }
    elif category == 'ammo':
        confirmation_keyboard = {
                "SI SI SI" : {'callback_data' : f'mer9 sì {item} {category} {quantity}'},
                "No, sparo solo a salve" : {'callback_data' : f'mer9 no {category}'}
            }
        
    confirmation_keyboard = telebot.util.quick_markup(confirmation_keyboard, row_width=1)
    return confirmation_keyboard



def pay_merchant(buyer_id, price):      #might modify in the future. for now, the money disappears
    conn, c = prep_database()
    # Take from buyer
    c.execute("UPDATE users SET bank = users.bank - %s WHERE user_id = %s", (price, buyer_id))
    conn.commit()
    conn.close()

def transfer_item_from_merchant(buyer_id, item, quantity, buyer_username=None):
    conn, c = prep_database()
    # Give to buyer
    c.execute('''
        INSERT INTO inventory (user_id, username, item_name, quantity)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(user_id, item_name) DO UPDATE SET quantity = inventory.quantity + %s
    ''',
    (buyer_id, buyer_username, item, quantity, quantity)
    )
    # And now take from the merchant
    c.execute("UPDATE merchant SET quantity = merchant.quantity - %s WHERE item_name = %s", (quantity, item))
    conn.commit()
    conn.close()

def transfer_weapon_from_merchant(buyer_id, weapon, buyer_username=None):
    conn, c = prep_database()
    # Unlike items, you can only have one arm. So, first I check you don't already have it.
    c.execute("SELECT * FROM armory WHERE user_id = %s AND arm_name = %s", (buyer_id, weapon))
    if c.fetchall():        #if user already had that weapon
        raise ValueError
    c.execute('''
        INSERT INTO armory (user_id, username, arm_name)
        VALUES (%s, %s, %s)
    ''',
    (buyer_id, buyer_username, weapon)
    )
    # And now take from the merchant
    c.execute("UPDATE merchant SET quantity = merchant.quantity - 1 WHERE item_name = %s", (weapon,))
    conn.commit()
    conn.close()

def transfer_ammo_from_merchant(buyer_id, ammo, quantity):
    # Retrieve arm name from ammo name (e.g. "pistola" from "Munizioni-pistola")
    arm_name = ammo.split('-')[1]

    conn, c = prep_database()
    # You can only have ammo for weapons you own
    c.execute("SELECT * FROM armory WHERE user_id = %s AND arm_name = %s", (buyer_id, arm_name))
    if not c.fetchall():        #if user didn't already have that weapon
        raise ValueError
    c.execute("UPDATE armory SET ammo = armory.ammo + %s WHERE user_id = %s AND arm_name = %s", (quantity, buyer_id, arm_name))
    # And now take from the merchant
    c.execute("UPDATE merchant SET quantity = merchant.quantity - %s WHERE item_name = %s", (quantity, ammo))
    conn.commit()
    conn.close()



def merchant_recap_message(item, quantity, price):
    recap_text = f"{quantity} {item} a te! ...e {price} soldi a me! Buona giornata! \n\n<i>(Puoi trovare quello che hai comprato nel /menu)</i>"
    return recap_text