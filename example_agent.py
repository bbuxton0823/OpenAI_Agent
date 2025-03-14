#!/usr/bin/env python
# Example of using the OpenAI Agents Python SDK

# Import statements are commented out since they're only used
# in the commented code
# import os
# from agents import Agent
# import openai
# from dotenv import load_dotenv


def main():
    print("OpenAI Agents SDK Example")
    print("Note: Set your OpenAI API key in the .env file")

    # Uncomment and run the following code when you have your API key set
    """
    # Uncomment these imports
    import os
    from agents import Agent
    import openai
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # Set your OpenAI API key from environment variable
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Create a simple agent
    agent = Agent(
        name="Example Agent",
        description="A simple example agent using the OpenAI Agents SDK",
        model="gpt-4o",
    )

    # Run the agent with a user message
    response = agent.run("Hello, can you tell me about the OpenAI Agents SDK?")

    # Print the response
    print("\nAgent Response:")
    print(response)
    """


if __name__ == "__main__":
    main()