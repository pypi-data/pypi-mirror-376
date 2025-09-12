from .discord_client import DiscordClient

def add_reaction(client: DiscordClient, user_id: str, message_id: str, reaction: str):
    dm_channel = client.find_existing_dm_channel(user_id)
    if not dm_channel:
        dm_channel = client.create_dm_channel(user_id)
    client.send_reaction(dm_channel, message_id, reaction)
