## Multiplayer Slack Narrative Alignment Game

A Python based Slack experiment for studying how people align on shared meanings and narratives across different social network structures. Players submit responses in real time through direct messages with the bot. The system automatically pairs users, runs multiple rounds, and logs all behavior for analysis.

### Game Objective

The objective of the game is to examine how people converge on shared language when they interact with others in a structured communication network. Participants receive a prompt each round and generate a short hashtag response. They are paired with another player based on the network design. Their goal is to produce a response that they think will match or align with their partner’s interpretation of the prompt.
This allows researchers to observe:
- How shared meaning forms
- How interpretations shift across rounds
- How different network structures influence alignment
- How narratives stabilize, diverge, or drift

### Research Purpose

This game is part of an experimental platform used to study narrative alignment, social influence, and communication patterns. It supports investigations into:
- How information travels across a network
- Whether certain network structures lead to faster or stronger convergence
- How language changes when players interact through neighbors instead of seeing the whole group
- How individual interpretations vary and stabilize over time

The pairing logic allows researchers to compare:
- Homogeneous networks where everyone is equally connected
- Spatial networks where each player interacts only with neighbors chosen by proximity
- This helps model real social systems and online communities.

### How the Game Works
1. Participants join a Slack workspace through an invite link and interact with the bot and other participants in a channel.
2. Once enough players join, the bot builds the network structure.
3. The bot runs several rounds:
- Sends a prompt
- Pairs each participant with another user
- Collects responses through the popup modal forms
- Logs timestamps, response hashtags, game outcome, and pairing information
4. The next round begins automatically after all responses or a timeout.
5. After all rounds, the bot exports a CSV with all trial data.

### Network Logic

The system supports two network topologies:
Homogeneous Network
- Every player can be paired with every other player.
- All pairs are generated before rounds begin and prepares a schedule for all the pairs to occur.

Spatial Network
- Players are arranged in a circular or grid-like structure.
- Each player has a fixed number of “neighbors” based on:
    - A spatial ordering
    - A chosen neighbor range
    - Players interact only with nearby neighbors.
    - This models realistic communication networks found in sports teams, dorm communities, or social media clusters.
