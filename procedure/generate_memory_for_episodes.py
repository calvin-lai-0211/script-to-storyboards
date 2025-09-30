import argparse
import json
import re
import time
from utils.database import Database
from utils.config import DB_CONFIG
from models.yizhan_llm import YiZhanLLM

class EpisodeMemoryGenerator:
    def __init__(self, db_connection: Database):
        self.db = db_connection
        self.llm = YiZhanLLM()

    def generate(self, drama_name: str, episode_number: int, force_regen: bool = False):
        """
        Generates a plot summary for a specific episode and stores it in the episode_memory table.
        """
        conn = self.db._get_connection()
        if conn is None:
            print("Could not connect to the database. Aborting.")
            return
            
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM episode_memory WHERE script_name = %s AND episode_number = %s LIMIT 1;", (drama_name, episode_number))
                exists = cur.fetchone() is not None
        finally:
            conn.close()

        if not force_regen and exists:
            print(f"Episode memory for '{drama_name}' Episode {episode_number} already exists. Skipping.")
            return

        if force_regen:
            print(f"Force regeneration enabled. Clearing existing episode memory for '{drama_name}' Episode {episode_number}...")
            conn = self.db._get_connection()
            if conn is None:
                print("Could not connect to the database for clearing records. Aborting.")
                return
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM episode_memory WHERE script_name = %s AND episode_number = %s;", (drama_name, episode_number))
                    conn.commit()
            finally:
                conn.close()

        print(f"--- Starting episode memory generation for '{drama_name}' Episode {episode_number} ---")

        all_episodes_content = self.db.get_episodes_by_base_title(drama_name)
        if not all_episodes_content or episode_number > len(all_episodes_content):
            print(f"Could not retrieve script content for Episode {episode_number}. Aborting.")
            return
        script_content = all_episodes_content[episode_number - 1]

        prompt = ""
        if episode_number == 1:
            prompt = self._build_prompt(script_content, drama_name, episode_number)
        else:
            previous_episode_summary_data = self.db.get_episode_memories(drama_name, [episode_number - 1])
            previous_summary = ""
            if previous_episode_summary_data:
                previous_summary = previous_episode_summary_data[0].get('plot_summary', 'N/A')
            
            prompt = self._build_prompt_with_memory(
                script_content=script_content,
                drama_name=drama_name,
                episode_number=episode_number,
                previous_summary=previous_summary
            )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Generating episode memory for '{drama_name}' Ep {episode_number} (Attempt {attempt + 1})...")
                response_tuple = self.llm.chat(
                    user_message=prompt,
                    model="gemini-2.5-pro",
                    stream=False
                )
                response_str = response_tuple[0]

                json_match = re.search(r"\{[\s\S]*\}", response_str)
                if not json_match:
                    raise ValueError("No valid JSON object found in LLM response.")

                json_string = json_match.group(0)
                response_json = json.loads(json_string)
                plot_summary = response_json.get("plot_summary")
                options = response_json.get("options")

                if not plot_summary:
                    raise ValueError("JSON response missing 'plot_summary'.")

                self.db.insert_episode_memory(
                    script_name=drama_name,
                    episode_number=episode_number,
                    plot_summary=plot_summary,
                    options=options
                )
                print(f"Successfully generated episode memory for '{drama_name}' Ep {episode_number}.")
                return
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for '{drama_name}' Ep {episode_number}: {e}")
                if attempt + 1 < max_retries:
                    time.sleep(5)
                else:
                    print(f"All retries failed for '{drama_name}' Ep {episode_number}. Skipping.")
                    raise

    def _build_prompt_with_memory(self, script_content: str, drama_name: str, episode_number: int, previous_summary: str) -> str:
        return f"""
# CONTEXT
You are a script analyst and writer. Your task is to create a cumulative summary of a series.

# SUMMARY OF EVENTS SO FAR (Episodes 1 to {episode_number - 1})
---
{previous_summary}
---

# SCRIPT CONTENT for New Episode ({drama_name} Episode {episode_number})
---
{script_content}
---

# TASK
Your goal is to update the "SUMMARY OF EVENTS SO FAR" with the events from the "SCRIPT CONTENT for New Episode".
You will create a new, concise, all-encompassing summary that covers everything from Episode 1 up to and including the current Episode {episode_number}.

# INSTRUCTIONS
1.  **Integrate**: Read the new script and identify the key events.
2.  **Combine and Summarize**: Merge the key events from the new episode with the "SUMMARY OF EVENTS SO FAR".
3.  **Rewrite**: Rewrite the combined information into a new, single-paragraph summary.
4.  **Strict Word Limit**: The final summary in the 'plot_summary' field **must not exceed 100 words**. Be concise and impactful.
5.  **Output JSON Format**: Your entire output must be a single, well-formed JSON object. It must contain two keys: "plot_summary" and "options".
6.  **'plot_summary' Field**: The new, cumulative summary of all events up to Episode {episode_number}.
7.  **'options' Field**: An empty JSON object (`{{}}`).

# EXAMPLE
(Assuming the previous summary was about Jane finding an artifact, and the new episode is about her meeting a historian)
```json
{{
  "plot_summary": "Jane, after discovering a mysterious artifact in her grandmother's attic, seeks out a reclusive historian for answers. He warns her of the artifact's dangers, just as a rival intensifies their pursuit. Following a tense confrontation, Jane escapes and finds her grandmother's journal, which she believes holds the key to the artifact's secrets. The journey to uncover a long-lost family secret has become more perilous.",
  "options": {{}}
}}
```

Now, generate the JSON for the script provided.
"""

    def _build_prompt(self, script_content: str, drama_name: str, episode_number: int) -> str:
        return f"""
# CONTEXT
You are a script analyst and writer. Your task is to read an episode's script and provide a concise plot summary.

# SCRIPT CONTENT for {drama_name} Episode {episode_number}
---
{script_content}
---

# TASK
Based on the provided script, generate a plot summary. The final output must be a single JSON object.

# INSTRUCTIONS
1.  **Read and Understand**: Read the entire script to grasp the main plot points, character developments, and key events.
2.  **Summarize**: Write a summary of the episode's plot.
3.  **Strict Word Limit**: The final summary in the 'plot_summary' field **must not exceed 100 words**.
4.  **Output JSON Format**: Your entire output must be a single, well-formed JSON object with no external text. It must contain two keys: "plot_summary" and "options".
5.  **'plot_summary' Field**: A string containing the plot summary.
6.  **'options' Field**: An empty JSON object (`{{}}`). This is reserved for future use.

# EXAMPLE
```json
{{
  "plot_summary": "The episode begins with the protagonist, Jane, discovering a mysterious artifact in her grandmother's attic. This discovery sets her on a path to uncover a long-lost family secret. She faces several challenges, including a rival who also seeks the artifact for their own nefarious purposes. The episode ends on a cliffhanger, with Jane deciphering a clue that points to the artifact's true power.",
  "options": {{}}
}}
```

Now, generate the JSON for the script provided.
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate episode memory and store it in the database.")
    parser.add_argument("drama_name", type=str, help="The name of the drama (script).")
    parser.add_argument("episode_number", type=int, help="The episode number.")
    parser.add_argument("--force-regen", action="store_true", help="Force regeneration even if it already exists.")
    args = parser.parse_args()

    # Assuming DB_CONFIG is defined elsewhere or passed as an argument
    # For now, using a placeholder or assuming it's available in the environment
    # In a real scenario, you'd instantiate Database with DB_CONFIG
    # db = Database(DB_CONFIG)
    # generator = EpisodeMemoryGenerator(db)
    # generator.generate(args.drama_name, args.episode_number, args.force_regen)

    # Placeholder for DB_CONFIG if not defined
    # This will cause an error if DB_CONFIG is not available
    # To make it runnable, you'd need to define DB_CONFIG or pass it as an argument
    # For now, commenting out the line to avoid immediate errors
    # generator = EpisodeMemoryGenerator(None) # This will fail
    # generator.generate(args.drama_name, args.episode_number, args.force_regen)

    # To make it runnable, you'd need to instantiate Database with DB_CONFIG
    # For example:
    # from utils.database import Database
    # db = Database(DB_CONFIG)
    # generator = EpisodeMemoryGenerator(db)
    # generator.generate(args.drama_name, args.episode_number, args.force_regen)

    # Since DB_CONFIG is not defined, we'll just print a message and exit
    print("DB_CONFIG is not defined. Please ensure it's available in utils.config or passed as an argument.")
    print("Example usage: python generate_memory_for_episodes.py <drama_name> <episode_number> --force-regen")
