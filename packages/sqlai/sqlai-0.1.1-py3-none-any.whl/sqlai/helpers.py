from pathlib import Path

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from .config import read_config, userinput_selection


def read_sql_file(file_path: str) -> str:
    """Read the content of a SQL file and return it as a string."""
    path = Path(file_path)

    if path.suffix.lower() != ".sql":
        print("⚠️   Only .sql files are allowed")
        exit(1)

    elif not path.exists():
        print(f"⚠️   File not found: {file_path}")
        exit(1)

    else:
        return path.read_text(encoding="utf-8")


def ask_gemini(sql_query: str, question: str) -> str:
    """Send SQL query and a question to Gemini API and return the response text."""

    config = read_config()
    if config:
        ai_provider = config["ai_provider"]  # not used yet
        api_key = config["api_key"]
        model = config["model"]

    # Configure with API key
    genai.configure(api_key=api_key)

    # Pick a model (flash is fast, pro is better quality)
    selected_model = genai.GenerativeModel(model)

    # Build the prompt
    prompt = f"SQL Query:\n{sql_query}\n\nQuestion:\n{question}"

    # Send to Gemini
    response = selected_model.generate_content(
        prompt, generation_config=GenerationConfig(temperature=0.5)
    )

    return response.text


def run(file_path):

    sql_file = read_sql_file(file_path)

    choice = userinput_selection(
        options=["explain", "validate", "improve"], prompt="Select an action"
    )

    config = read_config()
    if config:
        sql_dialect = config["sql_dialect"]

    if choice == "explain":
        response = ask_gemini(
            sql_query=sql_file,
            question=f"Give detailed explanation of what the SQL query (dialect: {sql_dialect}) does, but do not exceed 500 characters.",
        )
        print(response)
    elif choice == "validate":

        response = ask_gemini(
            sql_query=sql_file,
            question=f"""
                Check for the following violations in the provided SQL Query (Dialect: {sql_dialect}):
                - Missing or Misplaced Commas in SELECT lists
                - non-existing functions
                - functions with incorrect number of arguments
                - columns that reference an undefined table or table alias
                - Forgetting GROUP BY with Aggregates
                - Unquoted string literals
                - Incorrect clause order [SELECT, FROM, JOIN, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT). Consider that
                  some dialects might have additional clauses like QUALIFY in BigQuery.
                - Missing SELECT or FROM clause 
                - Missing column alias

                If you don't spot any violations, then return `OK`, else explain violation in short sentence - nothing else!
                """,
        )

        if response.strip() == "OK":
            print("✅ OK")
        else:
            print(f"⚠️ {response}")

    elif choice == "improve":
        response = ask_gemini(
            sql_query=sql_file,
            question=f"""
                If possible, improve the SQL query and make it more efficient / easier to read.
                Return only the SQL query itself without enclosing it in ``` query ```, do not describe what you have changed.

                Important - take into account the SQL dialect: {sql_dialect}
                """,
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response)

        print("✅ Done")
