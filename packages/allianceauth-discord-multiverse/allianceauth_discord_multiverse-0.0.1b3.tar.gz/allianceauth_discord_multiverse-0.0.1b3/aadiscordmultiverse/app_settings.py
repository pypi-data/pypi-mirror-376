from .utils import clean_setting

DISCORD_APP_ID = clean_setting('DISCORD_APP_ID', '')
DISCORD_APP_SECRET = clean_setting('DISCORD_APP_SECRET', '')
DISCORD_BOT_TOKEN = clean_setting('DISCORD_BOT_TOKEN', '')

# max retries of tasks after an error occurred
DISCORD_TASKS_MAX_RETRIES = clean_setting('DISCORD_TASKS_MAX_RETRIES', 3)

# Pause in seconds until next retry for tasks after the API returned an error
DISCORD_TASKS_RETRY_PAUSE = clean_setting('DISCORD_TASKS_RETRY_PAUSE', 60)

# DMV Specific Settings otherwise use discord core settings
DISCORD_CALLBACK_URL = clean_setting('DMV_CALLBACK_URL', '')
