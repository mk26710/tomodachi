import discord

# Default is 'https://discord.com/api/v7'
# discord.http.Route.BASE = "https://canary.discord.com/api/v7"

DEFAULT_PREFIX = "?"

BACKEND_URL = "http://localhost:1234"
BACKEND_TOKEN = "somerandomthingsblablabla"

SHARD_COUNT = 1
SHARD_IDS = [0]

SUPPORT_GUILD_ID = -1
DEFAULT_EMOJI_ID = -1
OWNER_IDS = {
    -1,
}

DEFAULT_STATUS = "あなたは私の友達です。"
BRAND_COLOR = discord.Color(0x83D0ED)

IMGUR_ID = "asdasd"
TOKEN = "bvnvbndsfg"

REDIS_URI = "redis://localhost:6379/0"
POSTGRES_CREDENTIALS = {
    "user": "username",
    "password": "password",
    "database": "bot",
    "host": "localhost",
    "port": 5432,
}
POSTGRES_DSN = "postgresql://{user}:{password}@{host}:{port}/{database}".format(**POSTGRES_CREDENTIALS)

EXTENSIONS = ("default",)
JISHAKU_FLAGS = ("HIDE",)
