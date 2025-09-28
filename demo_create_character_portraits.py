from procedure.generate_character_portraits import CharacterPortraitGenerator

if __name__ == '__main__':
    """
    This script demonstrates how to generate character portrait prompts for a specific episode of a drama.
    
    - It initializes the CharacterPortraitGenerator.
    - It calls the generate method with a specific drama name and episode number.
    - The results are saved directly to the 'character_portraits' table in the database.
    """
    
    # --- Configuration ---
    # Specify the drama and episode you want to process.
    DRAMA_NAME = "天归（「西语版」）"
    EPISODE_NUMBER = 1
    # ---------------------
    
    print(f"Starting character portrait generation demo for '{DRAMA_NAME}' - Episode {EPISODE_NUMBER}.")
    
    generator = CharacterPortraitGenerator()
    generator.generate(drama_name=DRAMA_NAME, episode_number=EPISODE_NUMBER)
    
    print("\nDemo script finished.")
