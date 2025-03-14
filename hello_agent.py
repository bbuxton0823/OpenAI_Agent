#!/usr/bin/env python
"""
A simple example of using the OpenAI Agents SDK with a .env file.
Make sure to set your OPENAI_API_KEY in the .env file before running.
"""

import os
from dotenv import load_dotenv
from agents import Agent, Runner

# Load environment variables from .env file
load_dotenv()

# Check if API key is set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "your_api_key_here":
    print("Error: Please set your OPENAI_API_KEY in the .env file")
    exit(1)

# Set the API key for the OpenAI client
os.environ["OPENAI_API_KEY"] = api_key


def main():
    # Create a simple agent
    agent = Agent(
        name="Hello Agent",
        instructions="You are a helpful assistant.",
    )

    # User input
    user_input = "Write a haiku about Python programming."

    print(f"Asking agent: {user_input}")
    print("\nAgent is thinking...\n")

    # Run the agent
    result = Runner.run_sync(agent, user_input)

    # Print the result
    print("Agent response:")
    print(result.final_output)


if __name__ == "__main__":
    main()