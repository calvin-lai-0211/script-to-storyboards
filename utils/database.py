import psycopg2
from psycopg2 import sql
import uuid
import json

class Database:
    def __init__(self, db_config):
        self.db_config = db_config
        self._initialize_database()

    def _initialize_database(self):
        """
        Initializes the database by ensuring all necessary tables are created.
        """
        self.create_scripts_table()
        self.create_flat_storyboard_table()

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

    def get_episodes_by_base_title(self, base_title):
        """ Retrieve all episodes for a script by its base title, ordered by episode number. """
        if not base_title:
            print("Please provide a base title.")
            return []

        conn = None
        episodes = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Use LIKE pattern to find all episodes of a script
            query = "SELECT content FROM scripts WHERE title LIKE %s ORDER BY episode_num ASC;"
            
            cur.execute(query, (f"{base_title}%",))
            
            rows = cur.fetchall()
            if rows:
                episodes = [row[0] for row in rows]
            else:
                print(f"No episodes found for base title: {base_title}")

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        
        return episodes

    def create_flat_storyboard_table(self):
        """
        Creates a single, denormalized table for storyboards, dropping all previous normalized tables.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Drop the old normalized tables if they exist
            cur.execute("DROP TABLE IF EXISTS sub_shots, shots, scenes, dramas;")
            print("Dropped old normalized tables (if they existed).")

            # Create the new flat table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS flat_storyboards (
                id SERIAL PRIMARY KEY,
                drama_name VARCHAR(255) NOT NULL,
                episode_number INTEGER,
                director_style VARCHAR(255),
                scene_number VARCHAR(255),
                scene_description TEXT,
                shot_number VARCHAR(255),
                shot_description TEXT,
                sub_shot_number VARCHAR(255),
                camera_angle VARCHAR(255),
                characters TEXT[],
                scene_context TEXT,
                image_prompt TEXT,
                video_prompt TEXT,
                dialogue_sound TEXT,
                duration_seconds INTEGER,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            conn.commit()
            print("Successfully created the flat_storyboards table.")

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error creating flat storyboard table: {error}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def insert_flat_storyboard(self, drama_name: str, director_style: str, storyboard_data: dict, episode_number: int = None):
        """
        Inserts storyboard data into the single flat table.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Loop through all levels of the JSON to gather data for each row
            for scene in storyboard_data.get('storyboard', []):
                for shot in scene.get('shots', []):
                    for sub_shot in shot.get('sub_shots', []):
                        cur.execute("""
                            INSERT INTO flat_storyboards (
                                drama_name, director_style, scene_number, scene_description,
                                shot_number, shot_description, sub_shot_number, camera_angle,
                                characters, scene_context, image_prompt, video_prompt,
                                dialogue_sound, duration_seconds, notes, episode_number
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """, (
                            drama_name,
                            director_style,
                            scene.get('scene_number'),
                            scene.get('scene_description'),
                            shot.get('shot_number'),
                            shot.get('shot_description'),
                            sub_shot.get('sub_shot_number'),
                            sub_shot.get('景别/机位'),
                            sub_shot.get('涉及人物'),
                            sub_shot.get('涉及场景'),
                            sub_shot.get('布景/人物/动作（生成首帧的prompt）'),
                            sub_shot.get('wan2.5 生成视频的prompt'),
                            sub_shot.get('对白/音效'),
                            sub_shot.get('时长(秒)'),
                            sub_shot.get('备注'),
                            episode_number
                        ))
            
            conn.commit()
            print(f"Successfully inserted flat storyboard for '{drama_name}'.")

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error inserting flat storyboard: {error}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()


if __name__ == '__main__':
    from utils.config import DB_CONFIG
    # The Database class now initializes the schema upon instantiation.
    # Creating an instance is enough to ensure tables are set up.
    db = Database(DB_CONFIG)
    print("Database schema initialized upon Database object creation.")

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
