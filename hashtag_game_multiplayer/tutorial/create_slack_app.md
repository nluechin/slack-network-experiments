# How to Build a slack App!

This is a tutorial on how to build a slack app using slack's python SDK and  python-slackclient.


## Create the Slack App
1. First thing to do is create an app. Follow the slack developer instructions [here](https://api.slack.com/) or follow along with my steps below:

- Click this link [https://api.slack.com/apps/new](https://api.slack.com/apps/new)
<img width="1427" height="799" alt="Screenshot 2025-11-06 at 2 12 53 PM" src="https://github.com/user-attachments/assets/f09b8559-c34c-44ff-ad7e-6037d15e73bf" />

- Click "Create an App". Then in the pop up window, select "From Scratch".
- Name the App (e.g. HashtagGame) and pick a workspace to develop your app in (or create a new workspace).
   - Note: Once you choose a workspace to create your app in, you can not change it to a different workspace.
- Press "Create App".

2. After creating your Slack app, it’s time for the fun part — adding scopes! Scopes define what your app is allowed to do within your workspace. The scopes you choose determine what actions the hashtag game chatbot can perform. To make sure the multiplayer version runs properly, follow the next steps carefully and select the exact scopes listed below.
- After clicking "create app", you will be brought to the app's home page. on the left side menu click OAuth & Permissions.
<img width="1311" height="722" alt="Screenshot 2025-11-06 at 2 26 50 PM" src="https://github.com/user-attachments/assets/1d8c49a7-6395-4b3a-9ac8-a3c9d2eef2ae" />
- On the page, scroll down a bit to see the header "Scopes" and "Bot Token Scopes". Add the same bot token scopes shown in the screenshot below by clicking "Add an OAuth Scope".
<img width="641" height="722" alt="Screenshot 2025-11-06 at 2 41 12 PM" src="https://github.com/user-attachments/assets/95040b68-1f16-41db-92bd-e54b30c513d3" />

(app_mentions:read, channels:read, chat:write, commands, groups:read, im:write, users:read)

- Then press "reinstall my app" (a notification of this usually pops up in a yellow window at the top of the page)
    - Do NOT miss this step

## Enable Socket Mode
To run this game locally Socket Mode allows your app to receive Slack events over a WebSocket connection instead of needing a public URL for an Events API endpoint.
1. In your Slack app dashboard, go to Settings → Socket Mode.
2. Toggle Enable Socket Mode to ON.
<img width="900" height="899" alt="Screenshot 2025-11-06 at 3 38 02 PM" src="https://github.com/user-attachments/assets/b5d9ba52-0066-4e60-9b0a-c92cacf34d06" />

## Set up .env and Project Folder.
Using VS code, create a new project folder and set up your .env file.
```
$ mkdir project_folder
$ cd project_folder

```
Open this folder in VS Code, then create a new file named .env inside it.
Your .env file will store your Slack tokens and secrets so the app can connect to your workspace.

Paste the following lines into your .env file:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
GAME_CHANNEL_ID=CYOURCHANNELID        #channel ID's always start with a C and have 11 characters
```

Fill in the values, You can find these values in your Slack app dashboard under Basic Information and OAuth & Permissions. Guidance on how to retrieve these values are found [here](https://github.com/nluechin/slack-network-experiments/blob/main/hashtag_game_multiplayer/tutorial/retrieve_tokens.md).

Once you’ve saved your .env file, you’re ready to move on to installing the dependencies and running the Slack bot.
