import os
from mirix import Mirix
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

mirix_agent = Mirix(
  api_key=API_KEY,
  model_provider="azure_opena",
  config_path="../.local/mirix_jplml_azure.yaml",
)

mirix_agent.insert_tool(
    name="calculate_sum",
    source_code="def calculate_sum(a: int, b: int) -> int:\n    return a + b",
    description="Calculate the sum of two numbers",
    args_info={"a": "First number", "b": "Second number"},
    returns_info="The sum of a and b",
    tags=["math"]
)

response = mirix_agent("What is the sum of 872345 and 234523? You HAVE to call the calculate_sum tool!")
print(response)

