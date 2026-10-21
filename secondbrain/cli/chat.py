from dotenv import load_dotenv
load_dotenv()

from secondbrain.agent.service import answer_query


def main() -> None:
    thread_id = input("Thread ID: ").strip() or "default"

    print("=" * 50)
    print("SecondBrain Agentic RAG")
    print("Type 'exit' to quit.")
    print("=" * 50)

    while True:
        query = input("\nYou: ").strip()

        if query.lower() in ["exit", "quit"]:
            break
        if not query:
            continue

        response = answer_query(
            query=query,
            thread_id=thread_id,
        )

        print("\nAssistant:\n")
        print(response)


if __name__ == "__main__":
    main()
