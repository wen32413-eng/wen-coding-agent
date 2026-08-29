from config import validate_config, WORKSPACE
from agent import CodingAgent


def main():
    validate_config()

    print("=" * 60)
    print("Mini Coding Agent")
    print("=" * 60)

    print(f"Workspace: {WORKSPACE}")
    print()
    print("Enter a programming task.")
    print("Type 'exit' or 'quit' to stop.")
    print()

    agent = CodingAgent()

    while True:
        try:
            task = input("> ").strip()

        except (KeyboardInterrupt, EOFError):
            print()
            print("Bye.")
            break

        if not task:
            continue

        if task.lower() in {
            "exit",
            "quit",
        }:
            print("Bye.")
            break

        agent.run(task)


if __name__ == "__main__":
    main()