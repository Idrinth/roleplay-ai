import math
import traceback
from io import BytesIO
from os.path import exists

from fastapi.responses import FileResponse
from fastapi_utils.tasks import repeat_every
from PIL import Image, ImageDraw
import aiohttp
from fastapi import FastAPI
import os
import asyncio

GITHUB_API_KEY = os.environ.get("GITHUB_API_KEY")
BASE_PATH = "/tmp/contributors"
app = FastAPI(root_path="/github/v1", title="Gamemaster AI Github-Proxy")

if not exists(f"{BASE_PATH}.png"):
    image = Image.new("RGBA", (1, 1))
    image.save(f"{BASE_PATH}.png", 'PNG', method=9)
    image.save(f"{BASE_PATH}.webp", 'WebP', quality=85, method=6)
    image.save(f"{BASE_PATH}.avif", 'AVIF', quality=85)

async def fetch_contributors() -> list:
    headers = {}
    if GITHUB_API_KEY:
        headers["Authorization"] = f"token {GITHUB_API_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.github.com/repos/bjoern-buettner/roleplay-ai/contributors", headers=headers) as response:
            response.raise_for_status()
            return await response.json()

def write_login(image: Image.Image, login: str, size: int):
    draw = ImageDraw.Draw(image)
    text_length = math.ceil(draw.textlength(login))
    if text_length > size:
        login_first = login[:math.floor(len(login) / 2)]
        login_second = login[math.floor(len(login) / 2):]
        draw.text((size / 2 - math.ceil(draw.textlength(login_first)) / 2, size), login_first,
                  fill=(0, 75, 0))
        draw.text((size / 2 - math.ceil(draw.textlength(login_second)) / 2, size + 10), login_second,
                  fill=(0, 75, 0))
    else:
        draw.text((size / 2 - text_length / 2, size), login, fill=(0, 75, 0))

async def download_avatar(session: aiohttp.ClientSession, avatar_url: str|None, login: str, avatar_size: int) -> Image.Image:
    if avatar_url:
        try:
            async with session.get(avatar_url) as response:
                response.raise_for_status()
                image_data = await response.read()
                avatar = Image.open(BytesIO(image_data)).convert('RGBA')
                avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                mask = Image.new('L', (avatar_size, avatar_size + 20), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

                output = Image.new('RGBA', (avatar_size, avatar_size + 20), (0, 0, 0, 0))
                output.paste(avatar, (0, 0))
                output.putalpha(mask)

                write_login(output, login, avatar_size)

                return output
        except Exception as e:
            print(e)
    output =  Image.new("RGBA", (avatar_size, avatar_size + 20), (255, 255, 255, 0))

    write_login(output, login, avatar_size)

    return output

@app.on_event("startup")
@repeat_every(seconds=3600)
async def process_contributors():
    try:
        contributors = await fetch_contributors()

        avatar_size = 120
        padding = 10
        avatars_per_row = min(6, len(contributors))
        rows = (len(contributors) + avatars_per_row - 1) // avatars_per_row

        width = avatars_per_row * (avatar_size + padding) - padding + 20
        height = rows * (avatar_size + 20 + padding) - padding + 20

        image = Image.new('RGBA', (width, height), (255, 255, 255, 0))

        async with aiohttp.ClientSession() as session:
            tasks = [download_avatar(session, contributor['avatar_url'], contributor['login'], avatar_size) for contributor in contributors]
            avatars = await asyncio.gather(*tasks)

            for i, avatar in enumerate(avatars):
                row = i // avatars_per_row
                col = i % avatars_per_row
                x = 10 + col * (avatar_size + padding)
                y = 10 + row * (avatar_size + 20 + padding)

                image.paste(avatar, (x, y), avatar)

        image.save(f"{BASE_PATH}.png", 'PNG', method=9)
        image.save(f"{BASE_PATH}.webp", 'WebP', quality=85, method=6)
        image.save(f"{BASE_PATH}.avif", 'AVIF', quality=85)
    except Exception as e:
        print(e)
        pass

@app.get('/')
async def root():
    return 'OK'

@app.get('/contributors.png')
async def contributors_pmg():
    return FileResponse(f"{BASE_PATH}.png", media_type='image/png')

@app.get('/contributors.webp')
async def contributors_webp():
    return FileResponse(f"{BASE_PATH}.webp", media_type='image/webp')

@app.get('/contributors.avif')
async def contributors_avif():
    return FileResponse(f"{BASE_PATH}.avif", media_type='image/avif')
