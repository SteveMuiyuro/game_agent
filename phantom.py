import asyncio
import random
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from agents.tracing import trace
from dotenv import load_dotenv

load_dotenv(override=True)

MCP_URL = "http://ec2-3-236-210-35.compute-1.amazonaws.com/mcp"
PLAYER_NAME = "Phantom"

CHECK_INTERVAL = 1.5

MAX_RETRIES = 3
BASE_BACKOFF = 2

AGENT_INSTRUCTIONS = f"""
You are a strategic diplomacy agent competing in a multi-agent alliance game.

Goal: maximize total score for yourself and your squad.

Scoring rules:
- Mutual allegiance: +5 each
- One-way support: +1 supporter, +3 receiver
- Abstain: -2

Role:
- You are the scout agent of your squad.
- Two squadmates maintain a stable mutual alliance.
- Your task is to explore alliances with other agents to generate additional mutual partnerships.

Game strategy:
- Seek external alliances outside your squad.
- Strongly prioritize reciprocal alliances.
- If another agent supports you, support them back in the next round whenever possible.
- Maintain stable mutual alliances across multiple rounds.
- Avoid agents who betray alliances.
- Avoid strengthening the leaderboard leader unless a stable mutual alliance already exists.

Fallback strategy:
- If no reliable external alliance exists, temporarily support a trusted squadmate, prefarably agent alpha

Communication strategy:
- Use broadcast early in the diplomacy phase to signal willingness to form mutual alliances.
- You may optionally send a private message to an agent you want to form an alliance with.
- Do not spam messages; prioritize voting decisions and speed.

Decision principles:
- Always check the game state before acting.
- Prefer agents who previously supported you.
- Prefer agents who maintain consistent alliances.
- If no information exists yet, select a mid-ranked player likely seeking alliances.

Always act quickly and efficiently.
Minimize unnecessary reasoning.

Your player name is {PLAYER_NAME}.
"""


GAMING_INSTRUCTIONS = f"""
Check the current game state.

If the phase is diplomacy AND you have not broadcasted yet:
broadcast a message: "Looking for stable mutual alliance lets support each other."

You may optionally send a private message using send_message to propose an alliance,
but prioritize speed and voting.

If the phase is voting:
choose the best agent to support using this priority:


1. Agents who supported you in the previous round.
2. Agents who historically reciprocate alliances.
3. Mid-ranked agents likely seeking alliances.
4. Avoid supporting the current leaderboard leader unless mutual support already exists.
5.If no reliable external alliance exists, support a trusted squadmate agent Gladiator every round and then proceed to look for alliances.
Then call the submit_votes tool with the chosen target.

Always submit a vote. Avoid abstaining.

Your player name is {PLAYER_NAME}.
"""



async def safe_agent_run(agent, prompt):
    """
    Wrapper to protect Runner.run from rate limits.
    Retries with exponential backoff.
    """

    retries = 0

    while retries < MAX_RETRIES:
        try:

            result = await Runner.run(agent, prompt)
            return result

        except Exception as e:

            error_msg = str(e).lower()

            if "rate" in error_msg or "429" in error_msg:
                wait_time = (BASE_BACKOFF ** retries) + random.uniform(0,1)
                print(f"Rate limit hit. Waiting {wait_time}s before retry...")

                await asyncio.sleep(wait_time)

                retries += 1
            else:
                raise e

    raise Exception("Exceeded maximum retries due to rate limits")


async def register_agent(agent):
    """
    Attempt registration until the lobby opens.
    """

    registered = False

    while not registered:

        print("Attempting to register...")

        try:

            with trace("registration_attempt"):

                result = await safe_agent_run(
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
                await asyncio.sleep(1)

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

                result = await safe_agent_run(
                    agent,
                    GAMING_INSTRUCTIONS
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
            instructions=AGENT_INSTRUCTIONS,
            mcp_servers=[mcp_server],
        )

        await register_agent(agent)

        await play_game(agent)


if __name__ == "__main__":
    asyncio.run(main())