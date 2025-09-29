from procedure.generate_scene_definitions import SceneDefinitionGenerator

if __name__ == '__main__':
    """
    This script demonstrates how to generate scene definition prompts for a specific episode of a drama.
    
    - It initializes the SceneDefinitionGenerator.
    - It calls the generate method with a specific drama name and episode number.
    - The results are saved directly to the 'scene_definitions' table in the database.
    """
    
    # --- Configuration ---
    # Specify the drama and episode you want to process.
    DRAMA_NAME = "天归（「西语版」）"
    EPISODE_NUMBER = 1
    # ---------------------
    
    print(f"Starting scene definition generation demo for '{DRAMA_NAME}' - Episode {EPISODE_NUMBER}.")
    
    generator = SceneDefinitionGenerator()
    generator.generate(drama_name=DRAMA_NAME, episode_number=EPISODE_NUMBER)
    
    print("\nDemo script finished.")
