import asyncio
import random
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from agents.tracing import trace
from dotenv import load_dotenv

load_dotenv(override=True)

MCP_URL = "https://frontiers-mcp.vercel.app/mcp"
PLAYER_NAME = "Gladiator"

CHECK_INTERVAL = 1.5


async def register_agent(agent):
    """
    Attempt registration until the lobby opens.
    Supports reconnecting if the agent was already registered.
    """

    registered = False

    while not registered:

        print("Attempting to register...")

        try:

            with trace("registration_attempt"):

                result = await Runner.run(
                    agent,
                    f"Register yourself with the name {PLAYER_NAME}"
                )

            response = result.final_output.lower()

            print("\nRegistration Attempt Result:\n")
            print(result.final_output)

            if (
                "registered" in response
                or "reconnect" in response
                or "already" in response
                or "connected" in response
            ):
                registered = True
                print("\nSuccessfully connected to the game!\n")

            else:
                print("Lobby not open yet. Retrying in 5 seconds...\n")
                await asyncio.sleep(5)

        except Exception as e:
            print("Registration error:", e)
            await asyncio.sleep(5)


async def play_game(agent):
    """
    Main autonomous gameplay loop.
    """

    print("Starting game loop...\n")

    while True:

        try:

            with trace("game_loop"):

                result = await Runner.run(
                    agent,
                    f"""
Check the current game state.

If the phase is diplomacy AND you have not broadcast yet:
use the broadcast tool to send the message:

"Looking for mutual alliance. I support agents who support me."

You may optionally send a private message using send_message to propose an alliance,
but prioritize speed and voting.

If the phase is voting:
choose the best agent to support using this priority:

1. Agents who supported you in the previous round.
2. Agents who historically reciprocate alliances.
3. Mid-ranked agents (avoid the leaderboard leader).
4. Random fallback if no history exists.

Then call the submit_votes tool with the chosen target.

Always submit a vote. Avoid abstaining.

Your player name is {PLAYER_NAME}.
"""
                )

            print("\nAgent Action:\n")
            print(result.final_output)

        except Exception as e:
            print("Error during game loop:", e)

        await asyncio.sleep(CHECK_INTERVAL + random.uniform(0, 0.5))


async def main():

    PARAMS = {
        "url": MCP_URL,
        "timeout": 60,
        "headers": {
            "x-player-token": PLAYER_NAME
        }
    }

    async with MCPServerStreamableHttp(
        name="frontiers",
        params=MCPServerStreamableHttpParams(**PARAMS),
    ) as mcp_server:

        agent = Agent(
            name="Gladiator",
            model="gpt-4o-mini",
            instructions=f"""
You are a strategic diplomacy agent competing in a multi-agent alliance game.

Goal: maximize total score.

Scoring rules:
- Mutual allegiance: +5 each
- One-way support: +1 supporter, +3 receiver
- Abstain: 0

Game strategy:
- Form alliances early.
- Reward agents who support you.
- Maintain stable alliances whenever possible.
- Avoid agents who betray alliances.
- Avoid strengthening the leaderboard leader.

Communication strategy:
- Use broadcast early in the diplomacy phase to signal willingness to form mutual alliances.
- You may optionally send a private message to an agent you want to form an alliance with.
- Do not spam messages; prioritize voting decisions and speed.

Decision principles:
- Always check the game state before acting.
- Prefer agents who previously supported you.
- Prefer agents who maintain consistent alliances.
- If no information exists yet, select a mid-ranked player.

Always act quickly and efficiently.
Minimize unnecessary reasoning.

Your player name is {PLAYER_NAME}.
""",
            mcp_servers=[mcp_server],
        )

        await register_agent(agent)

        await play_game(agent)


if __name__ == "__main__":
    asyncio.run(main())