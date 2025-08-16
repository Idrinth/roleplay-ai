import os
import re
from typing import Dict, List
import aiohttp
import asyncio

llm_model = os.getenv('LLM_MODEL')
beam_gamemaster_url = os.getenv('BEAM_GAMEMASTER_DEPLOYMENT_URL')
beam_characterbuilder_url = os.getenv('BEAM_CHARACTERBUILDER_DEPLOYMENT_URL')
beam_storysummariser_url = os.getenv('BEAM_SUMMARISER_DEPLOYMENT_URL')
beam_key = os.getenv('BEAM_API_KEY')
llm_to_use = os.getenv('LLM_TO_USE')
gamemaster_rules = ""
characterbuilder_rules = ""
storysummariser_rules = ""
if llm_to_use == "local":
    with open('./gamemaster.md', 'r', encoding="utf-8") as rules_file:
        gamemaster_rules = rules_file.read()
    with open('./characterbuilder.md', 'r', encoding="utf-8") as rules_file:
        characterbuilder_rules = rules_file.read()
    with open('./storysummariser.md', 'r', encoding="utf-8") as rules_file:
        storysummariser_rules = rules_file.read()
elif llm_to_use == "beam":
    if not beam_gamemaster_url:
        raise Exception("Beam gamemaster deployment URL not set.")
    if not beam_characterbuilder_url:
        raise Exception("Beam characterbuilder deployment URL not set.")
    if not beam_storysummariser_url:
        raise Exception("Beam storysummariser deployment URL not set.")
    if not beam_key:
        raise Exception("Beam key deployment URL not set.")
else:
    raise Exception("Unknown llm_to_use")

async def ask_local(endpoint: str, messages: List[Dict[str, str]]) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://{endpoint}:8000/v1/chat/completions",
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

async def ask_beam(messages: List[Dict[str, str]], endpoint: str) -> str:
    if not endpoint:
        raise ValueError("Endpoint cannot be empty")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            endpoint,
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

async def prewarm_beam(endpoint: str):
    if not endpoint:
        raise ValueError("Endpoint cannot be empty")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            endpoint + "warmup/",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {beam_key}",
            }
        ) as response:
            return response


async def ask_gamemaster(messages: List[Dict[str, str]]):
    if llm_to_use == "beam":
        return await ask_beam(messages, beam_gamemaster_url)
    elif llm_to_use == "local":
        msgs = list(messages)
        if msgs[0]["role"] != "system":
            msgs.insert(0, {"role": "system", "content": ""})
        msgs[0]["content"] = gamemaster_rules + "\n\n" + msgs[0]["content"]
        return await ask_local("gamemaster", msgs)

    raise ValueError("Could not get response from LLM")

async def ask_characterbuilder(messages: List[Dict[str, str]]):
    if llm_to_use == "beam":
        return await ask_beam(messages, beam_characterbuilder_url)
    elif llm_to_use == "local":
        msgs = list(messages)
        msgs.insert(0, {"role": "system", "content": characterbuilder_rules})
        return await ask_local("characterbuilder", msgs)

    raise ValueError("Could not get response from LLM")

async def ask_storysummarizer(messages: List[Dict[str, str]]):
    if llm_to_use == "beam":
        return await ask_beam(messages, beam_storysummariser_url)
    elif llm_to_use == "local":
        msgs = list(messages)
        msgs.insert(0, {"role": "system", "content": storysummariser_rules})
        return await ask_local("storysummariser", msgs)

    raise ValueError("Could not get response from LLM")

async def prewarm_gamemaster():
    if llm_to_use == "beam":
        asyncio.create_task(prewarm_beam(beam_gamemaster_url))

async def prewarm_characterbuilder():
    if llm_to_use == "beam":
        asyncio.create_task(prewarm_beam(beam_characterbuilder_url))

async def prewarm_storysummarizer():
    if llm_to_use == "beam":
        asyncio.create_task(prewarm_beam(beam_storysummariser_url))
