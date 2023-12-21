def mute_chat_member(user_id):
    from Utils.telebot_init import bot
    from golpebot_2023_main import group_id
    bot.restrict_chat_member(group_id, user_id)

def unmute_chat_member(user_id):
    from Utils.telebot_init import bot
    from golpebot_2023_main import group_id
    bot.restrict_chat_member(group_id, user_id, permissions=bot.get_chat(group_id).permissions)

def pin_message():
    pass