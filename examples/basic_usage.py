"""Basic usage example of Qwen3 Agent Framework."""

import requests

API_BASE = "http://localhost:8080"


def example_bash_command():
    """Example: Execute bash command via agent."""
    print("Sending request: 'List all files in the current directory'")

    response = requests.post(
        f"{API_BASE}/chat",
        json={
            "message": "List all files in the current directory",
            "max_iterations": 5,
        },
        timeout=120,
    )

    result = response.json()
    print(f"\n✅ Response: {result['response']}")
    print(f"📊 Iterations: {result['iterations']}")
    print(f"⏱️  Processing time: {result['processing_time']:.2f}s")

    if result.get("logs"):
        print(f"📝 Logs: {len(result['logs'])} entries")


def example_python_code():
    """Example: Execute Python code via agent."""
    print(
        "\nSending request: 'Calculate the sum of numbers from 1 to 100 using Python'"
    )

    response = requests.post(
        f"{API_BASE}/chat",
        json={
            "message": "Calculate the sum of numbers from 1 to 100 using Python",
            "max_iterations": 5,
        },
        timeout=120,
    )

    result = response.json()
    print(f"\n✅ Response: {result['response']}")
    print(f"📊 Iterations: {result['iterations']}")
    print(f"⏱️  Processing time: {result['processing_time']:.2f}s")


def example_health_check():
    """Example: Check API health."""
    print("Checking API health...")

    response = requests.get(f"{API_BASE}/health", timeout=5)
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Timestamp: {result['timestamp']}")


if __name__ == "__main__":
    print("=" * 60)
    print("Qwen3 Agent Framework - Usage Examples")
    print("=" * 60)

    print("\n--- Health Check ---")
    example_health_check()

    print("\n--- Bash Command Example ---")
    example_bash_command()

    print("\n--- Python Code Example ---")
    example_python_code()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
