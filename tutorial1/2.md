## Retrieve tokens

Paste the following lines into your .env file, if they are not already there:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
GAME_CHANNEL_ID=CYOURCHANNELID        #channel ID's always start with a C and have 11 characters
```

1. ```SLACK_BOT_TOKEN```
- Go to your Slack app dashboard: https://api.slack.com/apps
- Select your app, in the left sidebar, click OAuth & Permissions.
- Under OAuth Tokens for Your Workspace, copy the Bot User OAuth Token (it starts with xoxb-).
- Paste it into your .env file after SLACK_BOT_TOKEN=.

2. ```SLACK_SIGNING_SECRET```
- In the same app dashboard, go to Basic Information in the sidebar.
- Scroll to App Credentials.
- Copy the Signing Secret.
- Paste it after SLACK_SIGNING_SECRET=.

3.``` SLACK_APP_TOKEN```
- Go to Socket Mode in the sidebar.
- Toggle Enable Socket Mode to ON.
- Click Generate App-Level Token (make sure it has the connections:write scope).
- Copy the token (it starts with xapp-).
- Paste it after SLACK_APP_TOKEN=.

4. ```GAME_CHANNEL_ID```
- Open Slack and navigate to the channel where you want the game to run.
- Click the channel name at the top, choose View channel details, scroll to the bottom.
- Copy the Channel ID (it always starts with C and has 11 characters, like C07K4QY5Z3P).
- Paste it after GAME_CHANNEL_ID=.
