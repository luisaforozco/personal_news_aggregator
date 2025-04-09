import os

from acp.server.highlevel import Context
from beeai_sdk.providers.agent import Server
from beeai_sdk.schemas.text import TextInput, TextOutput

import os
import requests
from langchain_ollama.llms import OllamaLLM
from langchain_community.llms import Replicate
from ibm_granite_community.notebook_utils import get_env_var
from transformers import AutoTokenizer

from webscraping import load_html_2

try: # Look for a locally accessible Ollama server for the model
    response = requests.get(os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    model = OllamaLLM(
        model="granite3.2:2b",
        num_ctx=65536, # 64K context window
    )
    model = model.bind(raw=True) # Client side controls prompt
except Exception: # Use Replicate for the model
    model = Replicate(
        model="ibm-granite/granite-3.2-8b-instruct",
        replicate_api_token=get_env_var('REPLICATE_API_TOKEN'),
        model_kwargs={
            "max_tokens": 2000, # Set the maximum number of tokens to generate as output.
            "min_tokens": 200, # Set the minimum number of tokens to generate as output.
            "temperature": 0.75,
            "presence_penalty": 0,
            "frequency_penalty": 0,
        },
    )

# Tokenizer
model_path = "ibm-granite/granite-3.2-2b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_path)

server = Server("personal_news_aggregator-agent")

urls = ["https://www.nu.nl/economie/6351889/consumentenbond-opent-meldpunt-voor-gedupeerden-variabel-energiecontract.html"]

@server.agent()
async def hello_world(input: TextInput, ctx: Context) -> TextOutput:
    
    #for url in urls:
    #    response = load_html_2[url]
    scrapped_content = "Boeing heeft een schikking getroffen met nabestaanden van twee slachtoffers van een dodelijk vliegtuigongeluk in maart 2019. Daarmee heeft de vliegtuigbouwer op de valreep twee rechtszaken kunnen voorkomen."

    # concatenate responses
    
    prompt = tokenizer.apply_chat_template(
        conversation=[
            {"role": "system", "content": "Your task is to provide a summary that can be read in less than 5 minutes given the inputs. Keep the tone friendly but concise, we are in the Netherlands."},
            {"role": "user", "content": scrapped_content,}
            ],
        add_generation_prompt=True,
        tokenize=False,
    )

    output = model.invoke(prompt)
    
    template = os.getenv("HELLO_TEMPLATE", "Hallo %s")
    return TextOutput(text=template % output)

if __name__ == "__main__":
    server()