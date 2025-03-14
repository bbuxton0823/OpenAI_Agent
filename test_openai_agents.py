#!/usr/bin/env python
# Test script for OpenAI Agents Python SDK

import agents


def main():
    print("Successfully imported OpenAI Agents SDK")
    print(f"Available classes: {dir(agents)[:10]}...")


if __name__ == "__main__":
    main()