# Run the slack bot
## Download the Project Files

Before running the Slack bot, download this repository from GitHub.

1. At the top of [this page](https://github.com/nluechin/slack-network-experiments/tree/main), click the green “Code” button.
2. Select “Download ZIP.”
3. Once the ZIP file finishes downloading, unzip it on your computer.
4. Open the unzipped folder in VS Code (or your preferred editor).

## Run Slack Bot
Now that you’ve downloaded and unzipped the repository, you’re ready to launch the bot inside your Slack workspace.
1. Choose which version to run

- hashtag_game_individual/ = single-participant version

- hashtag_game_multiplayer/ = group network experiment version

Open the folder you want to run in your terminal:
```
cd hashtag_game_multiplayer
```
## Start Slack Bot
Once everything is set up, start the bot by running the Python file. If everything is connected correctly, your terminal should show:
```⚡ Slack Bolt app is running!```

## Test the bot in Slack
Go to your Slack workspace. Navigate to the channel you specified in your .env file (under GAME_CHANNEL_ID).

Type: @YourBotName start
