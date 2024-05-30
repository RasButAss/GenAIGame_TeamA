import os
from openai import AzureOpenAI
os.environ['AZURE_OPENAI_API_KEY'] = "3c749ed024f440269bd40f8472fa8f56"
os.environ['AZURE_OPENAI_API_ENDPOINT'] = "https://openai-for-internship-southindia.openai.azure.com/"



client = AzureOpenAI(
  api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
  api_version = "2024-02-01",
  azure_endpoint =os.getenv("AZURE_OPENAI_API_ENDPOINT") 
)


def get_embedding(text, model="text-embedding3"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding


# result = get_embedding("Your")
# print(result)