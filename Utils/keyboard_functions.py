import telebot
from Utils.telebot_init import bot
from Utils.database_functions import *

def create_keyboard_of_users(action : str, list_of_users=None):
    '''
    action is e.g. 'heal'. it's what the callback data will start with
    list_of_users defaults to all users; use get_list_of_users() with different arguments if needed
    '''
    # Establish which users to retrieve (e.g. exclude self for heal)
    if not list_of_users:    #if not provided, defaults to all users
        list_of_users = get_list_of_users()
    # Establish the max number of users per page
    max_users_per_page = 10
    # Separate users into sub-lists of at most 10 users
    ## Explanation (sorta copypasted from chatGPT):
    ## 'range(start, stop, step)': creates a range of indices, starting from 0 and incrementing by max_users_per_page at each step. It ensures that you get the starting index of each sub-list.
    ## 'all_users[i:i + max_users_per_page]: this is list slicing. For each index i obtained from the range, it creates a sub-list starting from index i and ending at i + max_users_per_page. This sub-list represents a chunk of at most max_users_per_page users from the original list.
    ## the entire one-liner: this is list comprehension (that's why it's in brackets). It iterates over the range of indices obtained in step 1 and creates a new list (keyboard_pages) 
    user_pages = [list_of_users[i:i + max_users_per_page] for i in range(0, len(list_of_users), max_users_per_page)]
    # user_pages is a list of lists. Each list contains tuple of first name - id
    # now we want to turn it into a list of lists where each list contains a button
    inline_keyboard_pages = []
    for page_number, page in enumerate(user_pages):
        # Here I'm using the telebot.util.quick_markup syntax; bc otherwise, row_width is broken (whereas I want 2 users per row)
        # The whole keyboard is a dictionary, and each button is just a dictionary entry. No lists no stuff
        keyboard = {}
        for first_name, user_id in page:    #tuple[0] is the first name; tuple[1] is the id
            keyboard[f"{first_name}"] = {"callback_data": f"{action} {page_number} {user_id}"}    #the callback_data has an "action" that makes it stateless
        # And at the bottom of the page, add the two buttons to navigate pages (using some fancy syntax)
        keyboard.update({f"{button}" : {"callback_data": f"{action} {page_number} {button}"} for button in ["<-", "->"]})
        # This page is done, can add it to the list of all pages!
        inline_keyboard_pages.append(keyboard)
    # Done! Return now (note that unlike some other keyboard-creator functions, this one does not return the text as well; indeed, it doesn't even return the actual keyboard, just a list of possible keyboards)
    return inline_keyboard_pages



def create_keyboard_of_weapons(action : str, list_of_weapons, target_id=0, omit_ammo=False, ammo_mode=False):
    '''
    action is e.g. 'heal'. it's what the callback data will start with

    if using this within attack, specify the target_id (to pass it along)
    if during menu->armeria, or mercante-> armi, omit target_id

    ammo should be shown during attack or menu, but omitted during vendi bc you're selling the weapon, not the ammo
    ammo_mode is used during Vendi to add "Munizioni " before the arm's name
    '''
    max_weapons_per_page = 5
    weapon_pages = [list_of_weapons[i:i + max_weapons_per_page] for i in range(0, len(list_of_weapons), max_weapons_per_page)]
    inline_keyboard_pages = []
    for page_number, page in enumerate(weapon_pages):
        keyboard = {}
        for weapon, ammo in page:    #tuple[0] is the weapon; tuple[1] is the ammo
            if omit_ammo:
                keyboard[f"{weapon}"] = {"callback_data": f"{action} {page_number} {weapon}"}
            if ammo_mode:
                keyboard[f"Munizioni {weapon} ({ammo})"] = {"callback_data": f"{action} {page_number} {weapon}"}
            elif not omit_ammo and not ammo_mode:
                keyboard[f"{weapon} ({ammo})"] = {"callback_data": f"{action} {target_id} {page_number} {weapon}"}    #the callback_data has an "action" that makes it stateless
        # And at the bottom of the page, add the two buttons to navigate pages (using some fancy syntax)
        keyboard.update({f"{button}" : {"callback_data": f"{action} {target_id} {page_number} {button}"} for button in ["<-", "->"]})
        # This page is done, can add it to the list of all pages!
        inline_keyboard_pages.append(keyboard)
    # Done! Return now (note that unlike some other keyboard-creator functions, this one does not return the text as well; indeed, it doesn't even return the actual keyboard, just a list of possible keyboards)
    return inline_keyboard_pages



def create_keyboard_of_items(action : str, list_of_items):
    '''
    action is e.g. 'heal'. it's what the callback data will start with
'''
    max_items_per_page = 5
    item_pages = [list_of_items[i:i + max_items_per_page] for i in range(0, len(list_of_items), max_items_per_page)]
    inline_keyboard_pages = []
    for page_number, page in enumerate(item_pages):
        keyboard = {}
        for item, quantity in page:    #tuple[0] is the item; tuple[1] is the quantity
            keyboard[f"{item} ({quantity})"] = {"callback_data": f"{action} {page_number} {item}"}    #the callback_data has an "action" that makes it stateless
        # And at the bottom of the page, add the two buttons to navigate pages (using some fancy syntax)
        keyboard.update({f"{button}" : {"callback_data": f"{action} {page_number} {button}"} for button in ["<-", "->"]})
        # This page is done, can add it to the list of all pages!
        inline_keyboard_pages.append(keyboard)
    # Done! Return now (note that unlike some other keyboard-creator functions, this one does not return the text as well; indeed, it doesn't even return the actual keyboard, just a list of possible keyboards)
    return inline_keyboard_pages



def display_page_number(list_of_pages, page_index, text, message_or_call, row_width=2, mode='edit'):
    '''
    mode can be "send" or "edit"
    send if first message, edit if in the chain
    defaults to edit
    '''
    if page_index >= 0 and  page_index < len(list_of_pages):
        current_page = list_of_pages[page_index]
        current_page = telebot.util.quick_markup(current_page, row_width=row_width)
        text += f'\n\n Pagina {page_index+1} di {len(list_of_pages)}'
        user_id = message_or_call.from_user.id
        if mode == 'send':
            bot.send_message(user_id, text, 'HTML', reply_markup=current_page)
        elif mode == 'edit':
            bot.edit_message_text(text, message_or_call.from_user.id, message_or_call.message.message_id, parse_mode='HTML', reply_markup=current_page)
    else:
        bot.answer_callback_query(message_or_call.id, 'Non ci sono altre pagine')

def retrieve_page_number(call):
    return int(call.data.split(' ')[-2])

def retrieve_data(call):
    return call.data.split(' ')[-1]

def has_changed_page(call):
    if retrieve_data(call) in ['<-', '->']:
        return True

def change_page_number(call):
    old_page_number = retrieve_page_number(call)
    if retrieve_data(call) == '<-':
        new_page_number = old_page_number - 1
    elif retrieve_data(call) == '->':
        new_page_number = old_page_number + 1
    return new_page_number



def amount_keyboard_creator(call, keyboard_buttons, range_valid_amount, current_amount):
    new_callback = call.data.split(' '); new_callback.pop(); new_callback = ' '.join(new_callback)
    inline_keyboard = {}
    for button in keyboard_buttons:    #first the + row
        new_amount = current_amount + button
        if new_amount <= range_valid_amount[1]: # Only add the button if it wouldn't make the price go out of range
            inline_keyboard[f"+{button}"] = {'callback_data' : f'{new_callback} {new_amount}'}
    for button in keyboard_buttons:    #and then the - row
        new_amount = current_amount - button
        if new_amount >= range_valid_amount[0]: # Only add the button if it wouldn't make the price go out of range
            inline_keyboard[f"-{button}"] = {'callback_data' : f'{new_callback} {new_amount}'}
    inline_keyboard["Fatto!"] = {'callback_data' : f'{new_callback} {current_amount} fatto'}
    inline_keyboard = telebot.util.quick_markup(inline_keyboard, row_width=len(keyboard_buttons))
    return inline_keyboard

def amount_keyboard_message_sender(call, keyboard_buttons : list, range_valid_amount : list, current_price : int, text_pt1 : str, text_pt2 : str):
    '''
    text_pt1 is what comes before the price (e.g. "A quanto lo vuoi vendere? \n\nPrezzo: ")
    then comes the current price
    and then text_pt2 is the thing (e.g. soldi)
    '''
    data = retrieve_data(call)
    if data != 'fatto':          #i.e. if I've not yet added " fatto" to the callback data
        amount_keyboard = amount_keyboard_creator(call, keyboard_buttons, range_valid_amount, current_price)
        text_price = f"{text_pt1} {current_price} {text_pt2}"
        bot.edit_message_text(message_id=call.message.message_id, chat_id=call.from_user.id, text=text_price, reply_markup=amount_keyboard, parse_mode='HTML')
    elif data == 'fatto':    #i.e. if I've added " fatto" to the callback data
        return True