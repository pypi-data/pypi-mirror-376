import json
import os
import pkg_resources


class CommandManager:
    def __init__(self, commands_file=None):
        if commands_file is None:
            # Try to find commands.json in package data or current directory
            try:
                self.commands_file = pkg_resources.resource_filename(
                    "siphoai", "data/commands.json"
                )
            except:
                self.commands_file = "commands.json"
        else:
            self.commands_file = commands_file

        self.commands = self.load_commands()

    def load_commands(self):
        """Load commands from JSON file"""
        try:
            with open(self.commands_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: {self.commands_file} not found!")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {self.commands_file}!")
            return {}

    def save_commands(self):
        """Save commands to JSON file"""
        try:
            with open(self.commands_file, "w", encoding="utf-8") as file:
                json.dump(self.commands, file, indent=2, ensure_ascii=False)
            print(f"Commands saved to {self.commands_file}")
            return True
        except Exception as e:
            print(f"Error saving commands: {e}")
            return False

    def add_web_command(self, triggers, url, response):
        """Add a new web command"""
        if "web_commands" not in self.commands:
            self.commands["web_commands"] = []

        new_command = {
            "triggers": triggers if isinstance(triggers, list) else [triggers],
            "action": "web_open",
            "url": url,
            "response": response,
        }

        self.commands["web_commands"].append(new_command)
        print(f"Added web command: {triggers}")

    def add_application_command(
        self,
        triggers,
        command,
        response,
        requires_confirmation=False,
        third_party_info=None,
    ):
        """Add a new application command"""
        if "application_commands" not in self.commands:
            self.commands["application_commands"] = []

        new_command = {
            "triggers": triggers if isinstance(triggers, list) else [triggers],
            "action": "run_application",
            "command": command if isinstance(command, list) else [command],
            "response": response,
        }

        if requires_confirmation:
            new_command["requires_confirmation"] = True
            new_command["confirmation_message"] = (
                f"Are you sure you want to run {triggers[0] if isinstance(triggers, list) else triggers}?"
            )

        if third_party_info:
            new_command["requires_third_party"] = third_party_info

        self.commands["application_commands"].append(new_command)
        print(f"Added application command: {triggers}")

    def add_system_command(
        self, triggers, command, response, requires_confirmation=True
    ):
        """Add a new system command"""
        if "system_commands" not in self.commands:
            self.commands["system_commands"] = []

        new_command = {
            "triggers": triggers if isinstance(triggers, list) else [triggers],
            "action": "system_command",
            "command": command if isinstance(command, list) else [command],
            "response": response,
        }

        if requires_confirmation:
            new_command["requires_confirmation"] = True
            new_command["confirmation_message"] = (
                f"Are you sure you want to execute this system command?"
            )

        self.commands["system_commands"].append(new_command)
        print(f"Added system command: {triggers}")

    def add_third_party_command(
        self,
        triggers,
        command,
        response,
        app_name,
        executable,
        download_url,
        install_instructions,
    ):
        """Add a new third-party application command"""
        if "third_party_apps" not in self.commands:
            self.commands["third_party_apps"] = []

        third_party_info = {
            "app_name": app_name,
            "executable": executable,
            "download_url": download_url,
            "install_instructions": install_instructions,
            "alternative_message": f"{app_name} is not installed.",
        }

        new_command = {
            "triggers": triggers if isinstance(triggers, list) else [triggers],
            "action": "run_application",
            "command": command if isinstance(command, list) else [command],
            "response": response,
            "requires_third_party": third_party_info,
        }

        self.commands["third_party_apps"].append(new_command)
        print(f"Added third-party command: {triggers}")

    def list_commands(self):
        """List all available commands"""
        print("\n" + "=" * 60)
        print("CURRENT VOICE COMMANDS")
        print("=" * 60)

        for category, commands in self.commands.items():
            if commands:  # Only show categories that have commands
                category_name = category.replace("_", " ").title()
                print(f"\n{category_name}:")
                print("-" * len(category_name))

                for i, cmd in enumerate(commands, 1):
                    triggers = ", ".join([f'"{t}"' for t in cmd["triggers"]])
                    print(f"  {i}. Triggers: {triggers}")
                    print(f"     Action: {cmd['action']}")
                    print(f"     Response: {cmd['response']}")
                    if "url" in cmd:
                        print(f"     URL: {cmd['url']}")
                    if "command" in cmd:
                        print(f"     Command: {' '.join(cmd['command'])}")
                    print()

    def remove_command(self, category, index):
        """Remove a command by category and index"""
        if category in self.commands and 0 <= index < len(self.commands[category]):
            removed = self.commands[category].pop(index)
            print(f"Removed command: {removed['triggers']}")
            return True
        else:
            print("Invalid category or index")
            return False

    def interactive_add_command(self):
        """Interactive command addition"""
        print("\n" + "=" * 50)
        print("ADD NEW VOICE COMMAND")
        print("=" * 50)

        command_types = {
            "1": "Web Command (opens a website)",
            "2": "Application Command (runs an installed application)",
            "3": "System Command (executes system command)",
            "4": "Third-Party App Command (runs app that might not be installed)",
        }

        print("Command Types:")
        for key, desc in command_types.items():
            print(f"  {key}. {desc}")

        choice = input("\nSelect command type (1-4): ").strip()

        if choice == "1":
            self._add_web_command_interactive()
        elif choice == "2":
            self._add_application_command_interactive()
        elif choice == "3":
            self._add_system_command_interactive()
        elif choice == "4":
            self._add_third_party_command_interactive()
        else:
            print("Invalid choice!")

    def _add_web_command_interactive(self):
        """Interactive web command addition"""
        print("\nAdding Web Command...")
        triggers = input("Enter trigger phrases (separated by commas): ").split(",")
        triggers = [t.strip().lower() for t in triggers if t.strip()]

        url = input("Enter URL: ").strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        response = input("Enter response message: ").strip()

        self.add_web_command(triggers, url, response)

    def _add_application_command_interactive(self):
        """Interactive application command addition"""
        print("\nAdding Application Command...")
        triggers = input("Enter trigger phrases (separated by commas): ").split(",")
        triggers = [t.strip().lower() for t in triggers if t.strip()]

        command = input("Enter application command/executable: ").strip()
        response = input("Enter response message: ").strip()

        requires_confirmation = (
            input("Requires voice confirmation? (y/N): ").lower() == "y"
        )

        self.add_application_command(
            triggers, [command], response, requires_confirmation
        )

    def _add_system_command_interactive(self):
        """Interactive system command addition"""
        print("\nAdding System Command...")
        print("WARNING: System commands can be dangerous. Only add trusted commands!")

        triggers = input("Enter trigger phrases (separated by commas): ").split(",")
        triggers = [t.strip().lower() for t in triggers if t.strip()]

        command = (
            input("Enter system command (with arguments separated by spaces): ")
            .strip()
            .split()
        )
        response = input("Enter response message: ").strip()

        requires_confirmation = (
            input("Requires voice confirmation? (Y/n): ").lower() != "n"
        )

        confirm = input(
            f"Are you sure you want to add this system command: {' '.join(command)}? (y/N): "
        )
        if confirm.lower() == "y":
            self.add_system_command(triggers, command, response, requires_confirmation)
        else:
            print("System command not added.")

    def _add_third_party_command_interactive(self):
        """Interactive third-party application command addition"""
        print("\nAdding Third-Party Application Command...")

        triggers = input("Enter trigger phrases (separated by commas): ").split(",")
        triggers = [t.strip().lower() for t in triggers if t.strip()]

        app_name = input("Enter application name: ").strip()
        command = input("Enter application executable path: ").strip()
        response = input("Enter response message: ").strip()

        download_url = input("Enter download URL: ").strip()
        if not download_url.startswith(("http://", "https://")):
            download_url = "https://" + download_url

        install_instructions = input("Enter installation instructions: ").strip()

        executable = input("Enter executable file name or path to check: ").strip()

        self.add_third_party_command(
            triggers,
            [command],
            response,
            app_name,
            executable,
            download_url,
            install_instructions,
        )


def main():
    """Main interactive menu"""
    manager = CommandManager()

    print("\n" + "=" * 50)
    print("VOICE COMMAND MANAGER")
    print("=" * 50)
    print("1. List all commands")
    print("2. Add new command")
    print("3. Save commands")
    print("4. Reload commands")
    print("5. Exit")

    choice = input("\nSelect option (1-5): ").strip()

    if choice == "1":
        manager.list_commands()
    elif choice == "2":
        manager.interactive_add_command()
    elif choice == "3":
        manager.save_commands()
    elif choice == "4":
        manager.commands = manager.load_commands()
        print("Commands reloaded!")
    elif choice == "5":
        print("Goodbye!")
    else:
        print("Invalid choice!")

    # Auto-save if changes were made
    if choice in ["2"]:  # Only auto-save after adding commands
        save_choice = input("\nSave changes? (Y/n): ").strip().lower()
        if save_choice != "n":
            manager.save_commands()

    print("\nCommand manager completed. Press Enter to exit...")
    input()


if __name__ == "__main__":
    main()
