import os

# Tests must not send traces to LangSmith. load_dotenv() never overrides a variable that is already set.
os.environ["LANGSMITH_TRACING"] = "false"
