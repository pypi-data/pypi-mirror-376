from .discord_client import DiscordClient
import time

def fake_typing(client: DiscordClient, user_id: str):
    dm_channel = client.find_existing_dm_channel(user_id)
    if not dm_channel:
        dm_channel = client.create_dm_channel(user_id)

    try:
        while True:
            url = f"https://discord.com/api/v9/channels/{dm_channel}/typing"
            response = client.session.post(url)
            if not response.ok:
                break
            time.sleep(3)
    except KeyboardInterrupt:
        pass
