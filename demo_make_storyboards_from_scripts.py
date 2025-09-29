from procedure.make_storyboards import MakeStoryboardsText
import json
if __name__ == '__main__':
    storyboard_generator = MakeStoryboardsText()
    # The base title of the script to generate storyboards for.
    script_title = "天归（「西语版」）"
    generated_storyboard = storyboard_generator.generate(script_title)

    if generated_storyboard:
        print(f"Storyboard for '{script_title}' generated and saved to database successfully.")
    else:
        print(f"Failed to generate storyboard for '{script_title}'.")
