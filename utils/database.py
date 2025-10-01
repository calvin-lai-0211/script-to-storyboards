import psycopg2
from psycopg2 import sql
import uuid
import json

class Database:
    def __init__(self, db_config, auto_init=False):
        """
        Initialize Database instance.

        Args:
            db_config: Database configuration dict
            auto_init: If True, automatically create tables on initialization.
                      Default is False for better performance in production.
        """
        self.db_config = db_config
        if auto_init:
            self._initialize_database()

    def _initialize_database(self):
        """
        Initializes the database by ensuring all necessary tables are created.
        Only call this when setting up the database for the first time.
        """
        self.create_scripts_table()
        self.create_flat_storyboard_table()
        self.create_character_portraits_table()
        self.create_scene_definitions_table()
        self.create_key_prop_definitions_table()
        self.create_episode_memory_table()

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

    def get_episode_script(self, base_title: str, episode_number: int):
        """ Retrieve the script content for a specific episode. """
        if not base_title or episode_number is None:
            print("Please provide a base title and episode number.")
            return None

        conn = None
        script_content = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            query = "SELECT content FROM scripts WHERE title LIKE %s AND episode_num = %s;"
            
            cur.execute(query, (f"{base_title}%", episode_number))
            
            row = cur.fetchone()
            if row:
                script_content = row[0]
            else:
                print(f"No script found for base title: {base_title}, episode: {episode_number}")

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        
        return script_content

    def get_episode_numbers_for_drama(self, drama_name: str):
        """
        Retrieves a list of all unique episode numbers for a given drama.
        """
        conn = None
        episode_numbers = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            query = """
                SELECT DISTINCT episode_num FROM scripts
                WHERE title LIKE %s AND episode_num IS NOT NULL
                ORDER BY episode_num;
            """
            cur.execute(query, (f"{drama_name}%",))
            rows = cur.fetchall()
            episode_numbers = [row[0] for row in rows]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting episode numbers for drama: {error}")
        finally:
            if conn:
                conn.close()
        return episode_numbers

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
                scene_context TEXT [],
                key_props TEXT[],
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
                                characters, scene_context, key_props, image_prompt, video_prompt,
                                dialogue_sound, duration_seconds, notes, episode_number
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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
                            sub_shot.get('涉及关键道具'),
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

    def get_characters_for_episode(self, drama_name: str, episode_number: int):
        """
        Retrieves a list of unique character names for a specific episode of a drama.
        """
        conn = None
        characters = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT unnest(characters) AS single_character
                FROM flat_storyboards
                WHERE drama_name = %s AND episode_number = %s;
            """, (drama_name, episode_number))
            
            rows = cur.fetchall()
            characters = [row[0] for row in rows]
            print(f"Found characters for '{drama_name}' Episode {episode_number}: {characters}")

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting characters for episode: {error}")
        finally:
            if conn:
                conn.close()
        return characters

    def create_character_portraits_table(self):
        """
        Creates the character_portraits table to store generated character image prompts and URLs.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS character_portraits (
                id SERIAL PRIMARY KEY,
                drama_name VARCHAR(255) NOT NULL,
                episode_number INTEGER NOT NULL,
                character_name VARCHAR(255) NOT NULL,
                image_prompt TEXT,
                reflection TEXT,
                version VARCHAR(20) DEFAULT '0.1',
                image_url VARCHAR(255),
                shots_appeared TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(drama_name, episode_number, character_name)
            );
            """)
            conn.commit()
            # For backward compatibility, add the reflection column if it doesn't exist
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='character_portraits' AND column_name='reflection') THEN
                        ALTER TABLE character_portraits ADD COLUMN reflection TEXT;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='character_portraits' AND column_name='version') THEN
                        ALTER TABLE character_portraits ADD COLUMN version VARCHAR(20) DEFAULT '0.1';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='character_portraits' AND column_name='is_key_character') THEN
                        ALTER TABLE character_portraits ADD COLUMN is_key_character BOOLEAN;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='character_portraits' AND column_name='character_brief') THEN
                        ALTER TABLE character_portraits ADD COLUMN character_brief TEXT;
                    END IF;
                END $$;
            """)
            conn.commit()
            print("Successfully created/ensured the character_portraits table exists.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error creating character_portraits table: {error}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

    def get_shots_for_character_in_episode(self, drama_name: str, episode_number: int, character_name: str):
        """
        Retrieves a list of sub_shot_numbers where a character appears in a specific episode.
        """
        conn = None
        shots = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT sub_shot_number
                FROM flat_storyboards
                WHERE drama_name = %s AND episode_number = %s AND %s = ANY(characters);
            """, (drama_name, episode_number, character_name))
            rows = cur.fetchall()
            shots = [row[0] for row in rows]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting shots for character: {error}")
        finally:
            if conn: conn.close()
        return shots

    def get_sub_shots_for_character(self, drama_name: str, episode_number: int, character_name: str):
        """
        Retrieves details of all sub-shots where a character appears in a specific episode.
        """
        conn = None
        shots_details = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            query = """
                SELECT scene_description, shot_description, sub_shot_number, camera_angle, image_prompt, dialogue_sound, notes
                FROM flat_storyboards
                WHERE drama_name = %s AND episode_number = %s AND %s = ANY(characters)
                ORDER BY sub_shot_number;
            """
            cur.execute(query, (drama_name, episode_number, character_name))
            
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            for row in rows:
                shots_details.append(dict(zip(columns, row)))

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting sub-shot details for character: {error}")
        finally:
            if conn:
                conn.close()
        return shots_details

    def insert_character_portrait(self, drama_name: str, episode_number: int, character_name: str, image_prompt: str, shots_appeared: list, reflection: str = None, version: str = '0.1', is_key_character: bool = None, character_brief: str = None):
        """
        Inserts or updates a character portrait record.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO character_portraits (drama_name, episode_number, character_name, image_prompt, shots_appeared, reflection, version, is_key_character, character_brief)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (drama_name, episode_number, character_name)
                DO UPDATE SET image_prompt = EXCLUDED.image_prompt, shots_appeared = EXCLUDED.shots_appeared, reflection = EXCLUDED.reflection, version = EXCLUDED.version, is_key_character = EXCLUDED.is_key_character, character_brief = EXCLUDED.character_brief;
            """, (drama_name, episode_number, character_name, image_prompt, shots_appeared, reflection, version, is_key_character, character_brief))
            conn.commit()
            print(f"Successfully inserted/updated portrait for '{character_name}' in '{drama_name}' Ep {episode_number}.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error inserting character portrait: {error}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

    def fetch_query(self, query: str, params: tuple = None):
        """
        Executes a SELECT query and fetches all results.
        """
        conn = None
        results = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(query, params)
            
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            for row in rows:
                results.append(dict(zip(columns, row)))

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error executing fetch query: {error}")
        finally:
            if conn:
                conn.close()
        return results

    def create_scene_definitions_table(self):
        """
        Creates the scene_definitions table to store generated scene image prompts.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS scene_definitions (
                id SERIAL PRIMARY KEY,
                drama_name VARCHAR(255) NOT NULL,
                episode_number INTEGER NOT NULL,
                scene_name VARCHAR(255) NOT NULL,
                image_prompt TEXT,
                reflection TEXT,
                version VARCHAR(20) DEFAULT '0.1',
                image_url VARCHAR(255),
                shots_appeared TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(drama_name, episode_number, scene_name)
            );
            """)
            conn.commit()
            # For backward compatibility, add the reflection column if it doesn't exist
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='scene_definitions' AND column_name='reflection') THEN
                        ALTER TABLE scene_definitions ADD COLUMN reflection TEXT;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='scene_definitions' AND column_name='version') THEN
                        ALTER TABLE scene_definitions ADD COLUMN version VARCHAR(20) DEFAULT '0.1';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='scene_definitions' AND column_name='is_key_scene') THEN
                        ALTER TABLE scene_definitions ADD COLUMN is_key_scene BOOLEAN;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='scene_definitions' AND column_name='scene_brief') THEN
                        ALTER TABLE scene_definitions ADD COLUMN scene_brief TEXT;
                    END IF;
                END $$;
            """)
            conn.commit()
            print("Successfully created/ensured the scene_definitions table exists.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error creating scene_definitions table: {error}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

    def get_scenes_for_episode(self, drama_name: str, episode_number: int):
        """
        Retrieves a list of unique scene names for a specific episode of a drama.
        """
        conn = None
        scenes = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT unnest(scene_context) AS single_scene
                FROM flat_storyboards
                WHERE drama_name = %s AND episode_number = %s;
            """, (drama_name, episode_number))
            
            rows = cur.fetchall()
            scenes = [row[0] for row in rows]
            print(f"Found scenes for '{drama_name}' Episode {episode_number}: {scenes}")

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting scenes for episode: {error}")
        finally:
            if conn:
                conn.close()
        return scenes

    def get_shots_for_scene_in_episode(self, drama_name: str, episode_number: int, scene_name: str):
        """
        Retrieves a list of sub_shot_numbers where a scene appears in a specific episode.
        """
        conn = None
        shots = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT sub_shot_number
                FROM flat_storyboards
                WHERE drama_name = %s AND episode_number = %s AND %s = ANY(scene_context);
            """, (drama_name, episode_number, scene_name))
            rows = cur.fetchall()
            shots = [row[0] for row in rows]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting shots for scene: {error}")
        finally:
            if conn: conn.close()
        return shots

    def insert_scene_definition(self, drama_name: str, episode_number: int, scene_name: str, image_prompt: str, shots_appeared: list, reflection: str = None, version: str = '0.1', is_key_scene: bool = None, scene_brief: str = None):
        """
        Inserts or updates a scene definition record.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO scene_definitions (drama_name, episode_number, scene_name, image_prompt, shots_appeared, reflection, version, is_key_scene, scene_brief)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (drama_name, episode_number, scene_name)
                DO UPDATE SET image_prompt = EXCLUDED.image_prompt, shots_appeared = EXCLUDED.shots_appeared, reflection = EXCLUDED.reflection, version = EXCLUDED.version, is_key_scene = EXCLUDED.is_key_scene, scene_brief = EXCLUDED.scene_brief;
            """, (drama_name, episode_number, scene_name, image_prompt, shots_appeared, reflection, version, is_key_scene, scene_brief))
            conn.commit()
            print(f"Successfully inserted/updated definition for '{scene_name}' in '{drama_name}' Ep {episode_number}.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error inserting scene definition: {error}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

    def create_key_prop_definitions_table(self):
        """
        Creates the key_prop_definitions table to store generated key prop image prompts.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS key_prop_definitions (
                id SERIAL PRIMARY KEY,
                drama_name VARCHAR(255) NOT NULL,
                episode_number INTEGER NOT NULL,
                prop_name VARCHAR(255) NOT NULL,
                image_prompt TEXT,
                reflection TEXT,
                version VARCHAR(20) DEFAULT '0.1',
                image_url VARCHAR(255),
                shots_appeared TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(drama_name, episode_number, prop_name)
            );
            """)
            conn.commit()
            # For backward compatibility, add the reflection column if it doesn't exist
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='key_prop_definitions' AND column_name='reflection') THEN
                        ALTER TABLE key_prop_definitions ADD COLUMN reflection TEXT;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='key_prop_definitions' AND column_name='version') THEN
                        ALTER TABLE key_prop_definitions ADD COLUMN version VARCHAR(20) DEFAULT '0.1';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='key_prop_definitions' AND column_name='is_key_prop') THEN
                        ALTER TABLE key_prop_definitions ADD COLUMN is_key_prop BOOLEAN;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='key_prop_definitions' AND column_name='prop_brief') THEN
                        ALTER TABLE key_prop_definitions ADD COLUMN prop_brief TEXT;
                    END IF;
                END $$;
            """)
            conn.commit()
            print("Successfully created/ensured the key_prop_definitions table exists.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error creating key_prop_definitions table: {error}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

    def get_key_props_for_episode(self, drama_name: str, episode_number: int):
        """
        Retrieves a list of unique key prop names for a specific episode of a drama.
        """
        conn = None
        props = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT unnest(key_props) AS single_prop
                FROM flat_storyboards
                WHERE drama_name = %s AND episode_number = %s;
            """, (drama_name, episode_number))
            
            rows = cur.fetchall()
            props = [row[0] for row in rows if row[0] is not None] # Filter out None values
            print(f"Found key props for '{drama_name}' Episode {episode_number}: {props}")

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting key props for episode: {error}")
        finally:
            if conn:
                conn.close()
        return props

    def get_sub_shots_for_key_prop(self, drama_name: str, episode_number: int, prop_name: str):
        """
        Retrieves details of all sub-shots where a key prop appears in a specific episode.
        """
        conn = None
        shots_details = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            query = """
                SELECT scene_description, shot_description, sub_shot_number, image_prompt, dialogue_sound, notes
                FROM flat_storyboards
                WHERE drama_name = %s AND episode_number = %s AND %s = ANY(key_props)
                ORDER BY sub_shot_number;
            """
            cur.execute(query, (drama_name, episode_number, prop_name))
            
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            for row in rows:
                shots_details.append(dict(zip(columns, row)))

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting sub-shot details for key prop: {error}")
        finally:
            if conn:
                conn.close()
        return shots_details

    def insert_key_prop_definition(self, drama_name: str, episode_number: int, prop_name: str, image_prompt: str, shots_appeared: list, reflection: str = None, version: str = '0.1', is_key_prop: bool = None, prop_brief: str = None):
        """
        Inserts or updates a key prop definition record.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO key_prop_definitions (drama_name, episode_number, prop_name, image_prompt, shots_appeared, reflection, version, is_key_prop, prop_brief)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (drama_name, episode_number, prop_name)
                DO UPDATE SET image_prompt = EXCLUDED.image_prompt, shots_appeared = EXCLUDED.shots_appeared, reflection = EXCLUDED.reflection, version = EXCLUDED.version, is_key_prop = EXCLUDED.is_key_prop, prop_brief = EXCLUDED.prop_brief;
            """, (drama_name, episode_number, prop_name, image_prompt, shots_appeared, reflection, version, is_key_prop, prop_brief))
            conn.commit()
            print(f"Successfully inserted/updated definition for prop '{prop_name}' in '{drama_name}' Ep {episode_number}.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error inserting key prop definition: {error}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

    def create_episode_memory_table(self):
        """
        Creates the episode_memory table to store episode summaries.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS episode_memory (
                id SERIAL PRIMARY KEY,
                script_name VARCHAR(255) NOT NULL,
                episode_number INTEGER NOT NULL,
                plot_summary TEXT,
                options JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(script_name, episode_number)
            );
            """)
            conn.commit()
            print("Successfully created/ensured the episode_memory table exists.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error creating episode_memory table: {error}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

    def insert_episode_memory(self, script_name: str, episode_number: int, plot_summary: str, options: dict = None):
        """
        Inserts or updates an episode memory record.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            # Convert options dict to JSON string if it's not None
            options_json = json.dumps(options) if options is not None else None
            cur.execute("""
                INSERT INTO episode_memory (script_name, episode_number, plot_summary, options)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (script_name, episode_number)
                DO UPDATE SET plot_summary = EXCLUDED.plot_summary, options = EXCLUDED.options;
            """, (script_name, episode_number, plot_summary, options_json))
            conn.commit()
            print(f"Successfully inserted/updated memory for '{script_name}' Ep {episode_number}.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error inserting episode memory: {error}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

    def get_episode_memories(self, drama_name: str, episode_numbers: list):
        """
        Retrieves plot summaries for a list of episode numbers for a given drama.
        """
        if not episode_numbers:
            return []
        
        query = """
            SELECT episode_number, plot_summary FROM episode_memory
            WHERE script_name = %s AND episode_number = ANY(%s)
            ORDER BY episode_number;
        """
        # Note: script_name in episode_memory corresponds to drama_name
        return self.fetch_query(query, (drama_name, episode_numbers))

    def get_character_definitions(self, drama_name: str, episode_numbers: list):
        """
        Retrieves character definitions (name and brief) for a list of episode numbers.
        It fetches the most recent version of each character's definition based on episode number.
        """
        if not episode_numbers:
            return []
            
        query = """
            SELECT DISTINCT ON (character_name) character_name, character_brief, image_prompt, reflection
            FROM character_portraits
            WHERE drama_name = %s AND episode_number = ANY(%s) AND character_brief IS NOT NULL
            ORDER BY character_name, episode_number DESC;
        """
        return self.fetch_query(query, (drama_name, episode_numbers))

    def get_scene_definitions(self, drama_name: str, episode_numbers: list):
        """
        Retrieves scene definitions (name and brief) for a list of episode numbers.
        It fetches the most recent version of each scene's definition based on episode number.
        """
        if not episode_numbers:
            return []

        query = """
            SELECT DISTINCT ON (scene_name) scene_name, scene_brief, image_prompt, reflection
            FROM scene_definitions
            WHERE drama_name = %s AND episode_number = ANY(%s) AND scene_brief IS NOT NULL
            ORDER BY scene_name, episode_number DESC;
        """
        return self.fetch_query(query, (drama_name, episode_numbers))

    def get_key_prop_definitions(self, drama_name: str, episode_numbers: list):
        """
        Retrieves key prop definitions (name and brief) for a list of episode numbers.
        It fetches the most recent version of each prop's definition based on episode number.
        """
        if not episode_numbers:
            return []

        query = """
            SELECT DISTINCT ON (prop_name) prop_name, prop_brief, image_prompt, reflection
            FROM key_prop_definitions
            WHERE drama_name = %s AND episode_number = ANY(%s) AND prop_brief IS NOT NULL
            ORDER BY prop_name, episode_number DESC;
        """
        return self.fetch_query(query, (drama_name, episode_numbers))

    def check_script_exists_by_base_title(self, base_title: str) -> bool:
        """Checks if any script with the given base title exists."""
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            query = "SELECT 1 FROM scripts WHERE title LIKE %s LIMIT 1;"
            cur.execute(query, (f"{base_title}%",))
            return cur.fetchone() is not None
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error checking for script existence: {error}")
            return False
        finally:
            if conn:
                conn.close()

    def check_records_exist(self, table_name: str, drama_name: str, episode_number: int = None) -> bool:
        """
        Checks if any records exist for a given drama and optional episode in a specified table.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            if episode_number:
                query = sql.SQL("SELECT 1 FROM {} WHERE drama_name = %s AND episode_number = %s LIMIT 1;").format(sql.Identifier(table_name))
                params = (drama_name, episode_number)
            else:
                query = sql.SQL("SELECT 1 FROM {} WHERE drama_name = %s LIMIT 1;").format(sql.Identifier(table_name))
                params = (drama_name,)

            cur.execute(query, params)
            return cur.fetchone() is not None
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error checking records in {table_name}: {error}")
            return False
        finally:
            if conn:
                conn.close()

    def clear_records(self, table_name: str, drama_name: str, episode_number: int = None):
        """
        Deletes records for a given drama and optional episode from a specified table.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            if episode_number:
                print(f"Clearing records from {table_name} for {drama_name}, Episode {episode_number}...")
                query = sql.SQL("DELETE FROM {} WHERE drama_name = %s AND episode_number = %s;").format(sql.Identifier(table_name))
                params = (drama_name, episode_number)
            else:
                print(f"Clearing all records from {table_name} for {drama_name}...")
                query = sql.SQL("DELETE FROM {} WHERE drama_name = %s;").format(sql.Identifier(table_name))
                params = (drama_name,)

            cur.execute(query, params)
            conn.commit()
            print(f"Successfully cleared records from {table_name} for {drama_name}.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error clearing records from {table_name}: {error}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()


if __name__ == '__main__':
    from utils.config import DB_CONFIG
    # Initialize database with auto_init=True to create all tables
    db = Database(DB_CONFIG, auto_init=True)
    print("Database schema initialized successfully.")

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
