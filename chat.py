# chat.py - Interactive chat interface
from bot import process_message


def print_banner():
    print("=" * 60)
    print("   DevStudio Support Bot")
    print("   Type /exit to quit, /help for commands")
    print("=" * 60)


def print_help():
    print("\nAvailable commands:")
    print("  /exit    - Quit the chat")
    print("  /help    - Show this help")
    print("  /clear   - Clear the screen")
    print("\nExample questions:")
    print("  - What is your refund policy?")
    print("  - Where is my order ORD-482910?")
    print("  - I want to talk to a human")
    print("  - What services do you offer?")
    print("")


def main():
    print_banner()

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["/exit", "exit", "quit", "/quit"]:
                print("\nBot: Goodbye! Have a great day.")
                break

            if user_input.lower() == "/help":
                print_help()
                continue

            if user_input.lower() == "/clear":
                print("\033[H\033[J", end="")
                print_banner()
                continue

            response = process_message(user_input)
            print("\nBot: " + response.replace("\n", "\n     "))

        except KeyboardInterrupt:
            print("\n\nBot: Goodbye!")
            break
        except EOFError:
            print("\n\nBot: Goodbye!")
            break
        except Exception as e:
            print("\nBot: Sorry, an error occurred: " + str(e))


if __name__ == "__main__":
    main()

