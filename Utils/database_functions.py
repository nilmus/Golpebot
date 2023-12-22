import psycopg2

import os
from dotenv import load_dotenv
load_dotenv()

def prep_database():
    conn = psycopg2.connect(
        dbname = os.getenv('DBNAME'),
        user = os.getenv('USER'),
        password = os.getenv('PASSWORD'),
        host = os.getenv('HOST'),
        port = os.getenv('PORT'))
    c = conn.cursor()
    return (conn, c)




def get_list_of_users(only_alive=False, exclude_self=False, only_team=False, only_team_roles=False):
    '''A function to get all users (for inline keyboards, e.g. in attack, sell, etc.)
    Can optionally only retrieve alive users
    Can optionally exclude the user using the function (pass message/call as argument)
    Can optionally only retrieve users of a certain team (pass a string like 'BLU' or use retrieve_team on the message/call)
    Can optionally only retrieve users of certain team roles (pass a list of strings)

    Returns a list of tuples of (first_name, user_id)
    '''
    query = "SELECT tg_name, user_id FROM users"
    conditions = []
    values = []
    if only_alive:
        conditions.append("is_alive = TRUE")
    if exclude_self:
        user_id = exclude_self.from_user.id
        conditions.append("user_id != %s")
        values.append(user_id)
    if only_team:
        conditions.append("team = %s")
        values.append(only_team)

    if conditions:
        query += ' WHERE '
        query += ' AND '.join(conditions)

    if only_team_roles:
        if not conditions:
            query += ' WHERE ('
        elif conditions:
            query += ' AND ('
        team_role_conditions = []
        for team_role in only_team_roles:
            team_role_conditions.append(f"team_role = '{team_role}'")
        query += ' OR '.join(team_role_conditions)
        query += ')'

    query += " ORDER by tg_name"
    conn, c = prep_database()
    c.execute(query, values)
    users = c.fetchall()
    conn.close()
    return users





def get_user_link(user_id):
    '''
    Returns @username if user has a username
    Returns first name with link to profile if user does not have a username
    '''
    def check_has_username(user_id):
        conn, c = prep_database()
        c.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
        username = c.fetchone()
        conn.close()
        if username:
            return username[0]
    
    def create_username_link(username):
        return f"@{username}"

    def create_name_id_link(user_id):
        conn, c = prep_database()
        c.execute("SELECT tg_name FROM users WHERE user_id = %s", (user_id,))
        name = c.fetchone()[0]
        conn.close()
        return f"<a href='tg://user?id={user_id}'>{name}</a>"

    username = check_has_username(user_id)
    if username:
        return create_username_link(username)
    else:
        return create_name_id_link(user_id)
    



def retrieve_team(message_or_call):
    user_id = message_or_call.from_user.id
    conn, c = prep_database()
    c.execute("SELECT team FROM users WHERE user_id = %s", (user_id,))
    team = c.fetchone()[0]
    conn.close()
    return team

def retrieve_team_role(message_or_call):
    user_id =  message_or_call.from_user.id
    conn, c = prep_database()
    c.execute("SELECT team_role FROM users WHERE user_id = %s", (user_id,))
    team_role = c.fetchone()[0]
    conn.close()
    return team_role

def retrieve_time_column(user_id, column : str, table='users'):
    '''Used e.g. for spy, heal, respawn, last_redeemed
        Column is e.g. time_of_spy
        Table defaults to users
        
        Returns the time as a string'''
    conn, c = prep_database()
    c.execute(f"SELECT {column} FROM {table} WHERE user_id = %s", (user_id,))
    last_time = c.fetchone()[0]
    conn.close()
    return last_time

def retrieve_team_status(message_or_call):
    team = retrieve_team(message_or_call)
    conn, c = prep_database()
    c.execute("SELECT status FROM teams WHERE team = %s", (team,))
    team_status = c.fetchone()[0]
    conn.close()
    return team_status

def retrieve_reigning_team():
    conn, c = prep_database()
    c.execute("SELECT team FROM teams WHERE status = 'regnante'")
    reigning_team = c.fetchone()[0]
    conn.close()
    return reigning_team

def retrieve_golping_team():
    conn, c = prep_database()
    c.execute("SELECT team FROM teams WHERE status = 'golpante'")
    golping_team = c.fetchone()[0]
    conn.close()
    return golping_team

def is_team_leader_alive(team : str):
    conn, c = prep_database()
    c.execute("SELECT is_alive FROM users WHERE team_role = 'leader' AND team = %s", (team,))
    reigning_team = c.fetchone()[0]
    conn.close()
    return reigning_team

def is_50percent_politicians_alive(team : str):
    conn, c = prep_database()
    c.execute("SELECT is_alive FROM users WHERE team_role = 'politico' AND team = %s", (team,))
    politicians = c.fetchall()                             #returns a list of tuples
    politicians = [tup[0] for tup in politicians]          #converts to a list of booleans
    number_to_kill = round((len(politicians) / 2) +1)
    dead_politicians = politicians.count(False)
    if dead_politicians >= number_to_kill:
        return False
    else:
        return {'dead_politicians' : dead_politicians, 'number_to_kill' : number_to_kill}

def is_user_registered(message_or_call):
    user_id = message_or_call.from_user.id
    conn, c = prep_database()
    c.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    user_exists = c.fetchone()
    return user_exists

def retrieve_team_leader(team):
    conn, c = prep_database()
    c.execute("SELECT user_id FROM users WHERE team_role = 'leader' AND team = %s", (team,))
    leader_id = c.fetchone()[0]
    return leader_id



def get_list_of_items(user_id):
    conn, c = prep_database()
    c.execute("SELECT item_name, quantity FROM inventory WHERE user_id = %s", (user_id,))
    user_armory = c.fetchall()
    conn.close()
    return user_armory



def get_list_of_weapons(message_or_call):
    user_id = message_or_call.from_user.id
    conn, c = prep_database()
    c.execute("SELECT arm_name, ammo FROM armory WHERE user_id = %s", (user_id,))
    user_armory = c.fetchall()
    conn.close()
    return user_armory


def retrieve_user_hp(user_id):
    conn, c = prep_database()
    c.execute("SELECT hp FROM users WHERE user_id = %s", (user_id,))
    user_hp = c.fetchone()[0]
    conn.close()
    return user_hp



def set_time_column_to_now(user_id : int, column : str, table='users'):
    '''Used e.g. for spy, heal, respawn, last_redeemed
        Column is e.g. time_of_spy
        Table defaults to users
        
        Returns the time as a string'''
    conn, c = prep_database()
    c.execute(f"UPDATE {table} SET {column} = TO_CHAR(NOW(), 'DD/MM/YYYY HH24:MI') WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()
    return