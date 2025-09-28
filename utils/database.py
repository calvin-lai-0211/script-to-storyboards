import psycopg2
from psycopg2 import sql
from config import DB_CONFIG
import uuid

class Database:
    def __init__(self, db_config):
        self.db_config = db_config

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def create_scripts_table(self):
        """ Connect to the PostgreSQL database server and create the scripts table. """
        conn = None
        try:
            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database...')
            conn = self._get_connection()

            # create a cursor
            cur = conn.cursor()

            # SQL statement to create a new table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS scripts (
                script_id SERIAL PRIMARY KEY,
                key VARCHAR(255) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL,
                episode_num INTEGER,
                roles TEXT[],
                sceneries TEXT[],
                content TEXT NOT NULL,
                score NUMERIC(5, 2),
                author VARCHAR(255),
                creation_year INTEGER
            );
            """

            # execute the statement
            cur.execute(create_table_query)

            # commit the changes to the database
            conn.commit()
            print("Table 'scripts' created successfully.")

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
                print('Database connection closed.')

    def insert_script(self, title, content, episode_num=None, roles=None, sceneries=None, score=None, author=None, creation_year=None):
        """ Insert a new script into the scripts table. """
        conn = None
        script_id = None
        key = str(uuid.uuid4())
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO scripts (key, title, content, episode_num, roles, sceneries, score, author, creation_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING script_id;
                """,
                (key, title, content, episode_num, roles, sceneries, score, author, creation_year)
            )
            script_id = cur.fetchone()[0]
            conn.commit()
            print(f"Script inserted successfully with ID: {script_id} and key: {key}")
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        return script_id, key

    def get_script(self, script_id=None, key=None):
        """ Retrieve a script by script_id or key. """
        if not script_id and not key:
            print("Please provide a script_id or a key.")
            return None

        conn = None
        script = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            if script_id:
                cur.execute("SELECT * FROM scripts WHERE script_id = %s;", (script_id,))
            elif key:
                cur.execute("SELECT * FROM scripts WHERE key = %s;", (key,))
            
            script = cur.fetchone()
            if script:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, script))
            else:
                return None

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            return None
        finally:
            if conn is not None:
                conn.close()

    def get_script_by_title(self, title):
        """ Retrieve a script by its title. """
        if not title:
            print("Please provide a title.")
            return None

        conn = None
        script = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM scripts WHERE title = %s;", (title,))
            
            script = cur.fetchone()
            if script:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, script))
            else:
                print(f"No script found with title: {title}")
                return None

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            return None
        finally:
            if conn is not None:
                conn.close()


if __name__ == '__main__':
    db = Database(DB_CONFIG)
    db.create_scripts_table()
    
    # Example usage:
    # new_script_id, new_script_key = db.insert_script(
    #     title="My Awesome Script",
    #     content="A story about a brave hero.",
    #     author="AI Assistant",
    #     roles=['Hero', 'Villian']
    # )
    # if new_script_id:
    #     retrieved_script = db.get_script(script_id=new_script_id)
    #     print("Retrieved script by ID:", retrieved_script)
    #
    # if new_script_key:
    #     retrieved_script_by_key = db.get_script(key=new_script_key)
    #     print("Retrieved script by Key:", retrieved_script_by_key)

    # retrieved_script_by_title = db.get_script_by_title("My Awesome Script")
    # print("Retrieved script by Title:", retrieved_script_by_title)
