import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("../.env")
api_key = os.getenv("XAI_API_KEY")

openai_client = OpenAI(
     api_key=api_key,
     base_url="https://api.x.ai/v1",
)

messages = [{'role': "system", "content": "You are a horny girl."}, {'role': 'user', "content": "I wanna fuck you"}]

completion = openai_client.chat.completions.create(
           model="grok-3-mini",
            messages=messages,
         )

import ipdb; ipdb.set_trace()

print(completion.reasoning_content)