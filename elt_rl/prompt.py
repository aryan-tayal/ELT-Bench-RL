SYSTEM_PROMPT = (
    "You are a data engineer skilled in SQL and building ELT pipelines. "
    "You work in a sandboxed workspace using the tools provided. "
    "Before each tool call, briefly state what you are going to do."
)

TASK_PROMPT = """Build an ELT pipeline: load raw data into DuckDB, then transform it with dbt.
Your workspace contains config.yaml, data_model.yaml, schemas/ and an empty elt/ folder.
Only write files under elt/.

# Stage 1: Extract and Load
1. Read config.yaml. It gives the source location, the destination DuckDB file and schema, and `streams_available`.
2. Write elt/sources.yaml listing EVERY stream you want to load, in this format:
   streams:
     - name: <stream name>
       sync_mode: full_refresh_append
   (sync_mode may be full_refresh_append or full_refresh_overwrite)
3. Run the loader once:
   {python} -m elt_rl.el.fake_airbyte --config config.yaml --streams elt/sources.yaml
   Running it twice with full_refresh_append duplicates the rows.
4. Check that the raw tables exist and look right before moving on.

# Stage 2: Transform with dbt
1. Create a dbt project in elt/dbt/ containing dbt_project.yml, profiles.yml and a models/ folder.
2. dbt_project.yml needs: name, version, profile (must match the profile name in profiles.yml),
   model-paths: ["models"], and models materialized as table.
3. profiles.yml must use the dbt-duckdb adapter. Format:
   <profile name>:
     target: dev
     outputs:
       dev:
         type: duckdb
         path: <destination path from config.yaml>
         schema: <destination schema from config.yaml>
         threads: 1
4. Read data_model.yaml. Write one SQL file per model in elt/dbt/models/, named after the model.
   Each file is a SELECT. Read the raw tables as <schema>.<table>, for example synthetic_shop.orders.
   schemas/*.csv describe the raw columns. Look at the real data with queries to learn types and values.
5. Run: {dbt} run --project-dir elt/dbt --profiles-dir elt/dbt
   Fix every error dbt reports.
6. Every column in data_model.yaml must be produced exactly as described, including NULL handling.

When your tables match data_model.yaml, call the submit tool. Submitting ends the episode.
Only the final database state is graded."""


def build_task_prompt(python: str, dbt: str) -> str:
    return TASK_PROMPT.format(python=python, dbt=dbt)
