# How to Build a slack App!

This is a tutorial on how to build a slack app using slack's python SDK and  python-slackclient.


## Create the Slack App
1. First thing to do is create an app. follow the slack developer instructions [here](https://api.slack.com/) or follow along with my steps below.

- click this link [https://api.slack.com/apps/new](https://api.slack.com/apps/new)
<img width="1427" height="799" alt="Screenshot 2025-11-06 at 2 12 53 PM" src="https://github.com/user-attachments/assets/f09b8559-c34c-44ff-ad7e-6037d15e73bf" />

- select get started and in the pop up window you will select "From Scratch"
- Name the App (e.g. HashtagGame) and pick a workspace to develop your app in. once you choose a workspace to develop your app in you can not change it.
- press create app after you are done

2. After you created the app it is time to add the scopes
  - After clicking "create app", you will be brought to the app's home page. on the left side menu click OAuth & Permissions.
<img width="1311" height="722" alt="Screenshot 2025-11-06 at 2 26 50 PM" src="https://github.com/user-attachments/assets/1d8c49a7-6395-4b3a-9ac8-a3c9d2eef2ae" />

- scroll the page a bit to see the header "Scopes" and "Bot Token Scopes". Add the same bot token scopes shown in the screenshot below by clicking "Add an Oauth Scope"
<img width="641" height="722" alt="Screenshot 2025-11-06 at 2 41 12 PM" src="https://github.com/user-attachments/assets/95040b68-1f16-41db-92bd-e54b30c513d3" />

  - app_mentions:read
  - channels:read
  - chat:write
  - commands
  - groups:read
  - im:write
  - users:read 
  
- then press "reinstall my app" (a notification of this usually pops up in a yellow window at the top of the page)
- in short, scopes gives permission to what your app can do in your designated worksapce. So the scopes we have chosen will allow the hashtag game chat bot to perform these specific actions, therefore it is important to select these exact scopes.
