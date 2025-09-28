import re
from utils.database import Database
from utils.config import DB_CONFIG

def parse_and_insert_script(filepath, author, creation_year):
    """
    Parses a script file, splits it into episodes, and inserts them into the database.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return

    # The title is derived from the filename, without the extension.
    base_title = filepath.split('/')[-1].replace('.txt', '')

    # Split the script by episodes using a regular expression.
    # The regex looks for "### Episode. " followed by digits.
    episodes = re.split(r'### Episode\. \d+', content)
    
    # The first split part is usually empty or contains introductory text before the first episode.
    # We are interested in the content after the episode markers.
    episode_contents = episodes[1:] 

    if not episode_contents:
        print("No episodes found in the script.")
        return

    db = Database(DB_CONFIG)
    
    # Ensure the table exists before trying to insert data.
    db.create_scripts_table()

    for i, episode_content in enumerate(episode_contents, 1):
        episode_title = f"{base_title} - Episode {i}"
        
        print(f"Inserting episode {i} with title: '{episode_title}'")
        
        db.insert_script(
            title=episode_title,
            content=episode_content.strip(),
            episode_num=i,
            author=author,
            creation_year=creation_year
        )

if __name__ == '__main__':
    script_file = 'scripts/天归（「西语版」）.txt'
    author_name = "张馨月(moon)"
    year = 2025
    parse_and_insert_script(script_file, author_name, year)
