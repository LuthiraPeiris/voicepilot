from commands.parser import process_command


def main():
    print("VoicePilot started.")
    print("Type 'exit' to stop.")

    while True:
        command = input("\nEnter command: ")

        result = process_command(command)

        if result == "EXIT":
            print("VoicePilot stopped.")
            break

        print(result)


if __name__ == "__main__":
    main()