import os
import re
from typing import Dict, List
import aiohttp

import requests

llm_model = os.getenv('LLM_MODEL')
beam_url = os.getenv('BEAM_DEPLOYMENT_URL')
beam_key = os.getenv('BEAM_API_KEY')
llm_to_use = os.getenv('LLM_TO_USE')

async def ask_llm(messages: List[Dict[str, str]]):
    if llm_to_use == "beam":
        async with aiohttp.ClientSession() as session:
            async with session.post(
                beam_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {beam_key}",
                },
                json={
                    "messages": messages,
                }
            ) as response:

                if response.status == 200:
                    response_content = (await response.json())["answer"]
                    response_content = re.sub("^(\n|.)*</think>\\s*", "", response_content).strip()

                    return response_content
                else:
                    raise ValueError("Could not get successful response from LLM")
    elif llm_to_use == "local":
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://llama:8000/v1/chat/completions",
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "model": llm_model,
                    "messages": messages,
                }
            ) as response:

                if response.status == 200:
                    response_content = (await response.json())["choices"][0]["message"]["content"]
                    response_content = re.sub("^(\n|.)*</think>\\s*", "", response_content).strip()

                    return response_content
                else:
                    raise ValueError("Could not get successful response from LLM")
    raise ValueError("Could not get response from LLM")
