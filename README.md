# Setup

## Prerequisites

Install Python version 3.10 or newer.

Install uv, which will be used to manage the project environment and dependencies.

pip install uv


## Initialize the Project

Inside the project directory run:

uv init

This will create the project configuration and prepare the environment.


## Create the Virtual Environment

Create a virtual environment:

uv venv

Activate the environment:

source .venv/bin/activate


## Install Dependencies

Install the required libraries for the agent:

uv add openai-agents python-dotenv


## Create Environment Variables

Create a file named .env in the project root directory.

Add your OpenAI API key:

OPENAI_API_KEY=your_openai_api_key_here

The application will automatically load this variable using python-dotenv.



## Run the Agent

After installing dependencies and configuring the environment variables, run the agent:

uv run agents.py

The agent will connect to the MCP server, attempt registration, and start participating in the game once the lobby opens.