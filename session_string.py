from pyrogram import Client

# get these values from api.telegram.org
api_id = "APP_ID_HERE"
api_hash = "APP_HASH_HERE"


async def main():
    async with Client(":memory:", api_id=int(api_id), api_hash=api_hash) as app:
        # Generate the session string
        session_string = await app.export_session_string()
        print("Your session string is:", session_string)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())