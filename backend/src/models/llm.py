import os

from langchain_openai import ChatOpenAI

model_name = os.getenv("LLM_NAME")
base_url = os.getenv("LLM_HOST")
api_key = os.getenv("API_KEY")


llm = ChatOpenAI(model=model_name, verbose=True, base_url=base_url, api_key=api_key)
