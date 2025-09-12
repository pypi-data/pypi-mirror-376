from pathlib import Path

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from .config import read_config, userinput_selection
from .linting import rules
from .violations import examples


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
        options=[
            "fix",
            "format",
            "explain",
        ],
        prompt="Select an action",
    )

    config = read_config()
    if config:
        sql_dialect = config["sql_dialect"]

    if choice == "explain":
        print("👀  Checking the query ...")
        response = ask_gemini(
            sql_query=sql_file,
            question=f"""
            Give detailed explanation of what the SQL query (dialect: {sql_dialect}) does, structured in bullet points.
            The Answer should not exceed 500 characters.
            """,
        )
        print(response)
    elif choice == "fix":
        print("👀  Checking the query ...")
        response_1 = ask_gemini(
            sql_query=sql_file,
            question=f"""
                Check for the following violations in the provided SQL Query (Dialect: {sql_dialect}):
                
                {examples}

                If you don't spot any violations, then return `OK`, else list ALL violations you can find in short bullet points like this:
                - violation_1: more info
                - violation_2: more info
                _ ...
                """,
        )

        if response_1.strip() == "OK":
            print("✅  OK")
        else:
            print(f"⚠️   {response_1}")

            print("🔧  Fixing the query ...")

            response_2 = ask_gemini(
                sql_query=sql_file,
                question=f"""
                Look at the SQL query and fix the following erros:
                {response_1}
                
                Return only the SQL query itself without enclosing it in ``` query ```, do not describe what you have changed.

                Important - take into account the SQL dialect: {sql_dialect}
                """,
            )

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response_2)

            print("✅  Fixed")

    elif choice == "format":

        print("👀  Checking the query ...")

        response = ask_gemini(
            sql_query=sql_file,
            question=f"""
                Formatting the SQL query by enforcing the following rules:
                {rules}
                
                Return only the SQL query itself without enclosing it in ``` query ```, do not describe what you have changed.

                Important - If necessary, take into account the SQL dialect: {sql_dialect}
                """,
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response)

        print("✅  Formatted")
