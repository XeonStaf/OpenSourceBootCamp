import os

from langchain_openai import ChatOpenAI

model_name = os.getenv("LLM_NAME")
base_url = os.getenv("LLM_HOST")
api_key = os.getenv("API_KEY")

print(f"Model: {model_name}, URL: {base_url}, key: {api_key}")

llm = ChatOpenAI(
    model=model_name,
    verbose=True,
    base_url=base_url,
    api_key=api_key,
    # timeout=120,
    # max_tokens=2500,
    # temperature=0.5,
    # presence_penalty=0,
    # top_p=0.95
)
