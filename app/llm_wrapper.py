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

async def ask_local(messages: List[Dict[str, str]]) -> str:
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

async def ask_beam(messages: List[Dict[str, str]], endpoint: str) -> str:
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
        return await ask_local(messages)

    raise ValueError("Could not get response from LLM")

async def ask_characterbuilder(messages: List[Dict[str, str]]):
    if llm_to_use == "beam":
        return await ask_beam(messages, beam_characterbuilder_url)
    elif llm_to_use == "local":
        return await ask_local(messages)

    raise ValueError("Could not get response from LLM")

async def ask_storysummarizer(messages: List[Dict[str, str]]):
    if llm_to_use == "beam":
        return await ask_beam(messages, beam_storysummariser_url)
    elif llm_to_use == "local":
        return await ask_local(messages)

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
