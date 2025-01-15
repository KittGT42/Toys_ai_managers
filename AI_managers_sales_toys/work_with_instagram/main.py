from flask import Flask
from hypercorn.asyncio import serve
from hypercorn.config import Config
from work_with_instagram.main_instagram import app as instagram_app

config = Config()
config.bind = ["0.0.0.0:5002"]

async def main():
    try:
        await serve(instagram_app, config)
    except Exception as e:
        print(f"Instagram server error: {e}")