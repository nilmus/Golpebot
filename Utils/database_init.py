from Utils.database_functions import *


###########################
# Database initialization #
###########################
# Open a connection to the database
conn, c = prep_database()
# Create table if it doesn't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS "users" (
	"user_id"	INTEGER,
	"username"	TEXT UNIQUE,
	"team"	TEXT,
	"team_role"	TEXT DEFAULT 'nullità',
	"bank"	INTEGER DEFAULT 0,
	"playing_since"	TEXT,
	"forza"	INTEGER,
	"intelligenza"	INTEGER,
	"fortuna"	INTEGER,
	"is_alive"	BOOLEAN DEFAULT TRUE,
	"hp"	INTEGER DEFAULT 1000,
	"time_of_death"	TEXT DEFAULT '01/01/1970 00:00',
	"time_of_spy"	TEXT DEFAULT '01/01/1970 00:00',
	"time_of_heal"	TEXT DEFAULT '01/01/1970 00:00',
	"has_voted"	TEXT DEFAULT 'astenuto',
    "tg_name" TEXT,
	PRIMARY KEY("user_id")
    )
''')
# Create a trigger to auto-set user as dead if hp drop to 0, and set time_of_death to now (syntax is to omit seconds)
# In pgsql, you first need to create a function, and then the trigger
c.execute('''
    CREATE OR REPLACE FUNCTION unalive_user_if_zero_hp_function()
    RETURNS TRIGGER AS $$
BEGIN
    IF NEW.hp <= 0 AND OLD.hp != 0 THEN
        NEW.is_alive := FALSE;
        NEW.hp := 0;
        NEW.time_of_death := TO_CHAR(NOW(), 'DD/MM/YYYY HH24:MI');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
          ''')
c.execute('''
    CREATE OR REPLACE TRIGGER unalive_user_if_zero_hp
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION unalive_user_if_zero_hp_function();
''')

# And now a table for inventories
# This uses a composite primary key; so, if a user has 5 items, there will be 5 rows for that user
c.execute('''
    CREATE TABLE IF NOT EXISTS inventory(
        user_id INTEGER,
        username TEXT,
        item_name TEXT,
        quantity INTEGER,
        PRIMARY KEY (user_id, item_name)
    )
''')
# Create a trigger to auto-delete an item from inventory when quantity becomes zero
# But create the function first
c.execute('''
    CREATE OR REPLACE FUNCTION delete_item_if_zero_function()
    RETURNS TRIGGER AS $$
BEGIN
    IF NEW.quantity = 0 THEN
        DELETE FROM inventory WHERE user_id = NEW.user_id AND item_name = NEW.item_name;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
          ''')
c.execute('''
    CREATE OR REPLACE TRIGGER delete_item_if_zero
    AFTER UPDATE ON inventory
    FOR EACH ROW
    EXECUTE FUNCTION delete_item_if_zero_function();
''')

# And now a table for arms inventories (armory)!
# This uses a composite primary key; so, if a user has 5 arms, there will be 5 rows for that user
c.execute('''
    CREATE TABLE IF NOT EXISTS "armory" (
	"user_id"	INTEGER,
	"username"	TEXT,
	"arm_name"	TEXT,
	"ammo"	INTEGER DEFAULT 0,
	PRIMARY KEY("user_id","arm_name")
)
''')

# And now a table for jobs
c.execute('''
    CREATE TABLE IF NOT EXISTS "job" (
	"user_id"	INTEGER,
	"username"	TEXT,
	"job_name"	TEXT,
	"contract_expiry_date"	DATE,
	"last_redeemed"	TEXT,
	PRIMARY KEY("user_id")
)'''
)

# And for teams
c.execute('''
    CREATE TABLE IF NOT EXISTS "teams" (
	"team"	TEXT,
	"status"	TEXT DEFAULT 'neutrale',
	"bank"	INTEGER DEFAULT 0,
	"system"	TEXT DEFAULT 'democrazia',
    "is_alive"	BOOLEAN DEFAULT FALSE,
    "taxation" INTEGER DEFAULT 0,
    "salaries" JSONB DEFAULT '{"leader":0, "politico":0, "soldato":0, "spia":0, "medico":0}'::json,
	PRIMARY KEY("team")
)'''
)

# And for merchant
c.execute('''
    CREATE TABLE IF NOT EXISTS "merchant" (
	"item_name"	TEXT,
	"type"	TEXT,
	"quantity"	INTEGER,
	"price"	INTEGER,
	PRIMARY KEY("item_name")
)'''
)

conn.commit()
conn.close()