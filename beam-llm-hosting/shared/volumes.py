from beam import Volume
from .download_models import CACHE_PATH

VOLUMES = [
    Volume(name="roleplay-ai-cache", mount_path=CACHE_PATH),
    Volume(name="roleplay-ai-triton", mount_path='/root/.triton/cache/'),
]
