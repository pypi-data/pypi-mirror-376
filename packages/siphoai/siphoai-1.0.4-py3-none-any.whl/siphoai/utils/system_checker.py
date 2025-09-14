import os
import shutil
import json
from pathlib import Path
import pkg_resources


class SystemChecker:
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

        self.commands_data = self.load_commands()
        self.third_party_apps = self.extract_third_party_apps()

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

    def extract_third_party_apps(self):
        """Extract all third-party app requirements from commands JSON"""
        third_party_apps = {}

        for category, commands in self.commands_data.items():
            if isinstance(commands, list):
                for cmd in commands:
                    if "requires_third_party" in cmd:
                        third_party = cmd["requires_third_party"]
                        app_name = third_party["app_name"]

                        third_party_apps[app_name.lower()] = {
                            "app_name": app_name,
                            "executable": third_party["executable"],
                            "download_url": third_party.get("download_url", ""),
                            "install_instructions": third_party.get(
                                "install_instructions", ""
                            ),
                            "triggers": cmd.get("triggers", []),
                            "category": category,
                            "alternative_message": third_party.get(
                                "alternative_message", f"{app_name} is not available."
                            ),
                        }

        return third_party_apps

    def get_username(self):
        """Get current username"""
        return os.getenv("USERNAME", "User")

    def check_executable_exists(self, executable_path):
        """Check if an executable exists"""
        # Expand environment variables and username
        expanded_path = os.path.expandvars(executable_path)
        expanded_path = expanded_path.replace("{username}", self.get_username())

        # Check if it's a full path
        if os.path.isabs(expanded_path):
            return os.path.exists(expanded_path)

        # Check if it's in PATH
        return shutil.which(executable_path) is not None

    def scan_installed_apps(self):
        """Scan for all third-party applications from JSON"""
        installed_apps = {}

        for app_key, app_info in self.third_party_apps.items():
            app_name = app_info["app_name"]
            executable = app_info["executable"]

            if self.check_executable_exists(executable):
                installed_apps[app_key] = {
                    "app_name": app_name,
                    "executable": executable,
                    "status": "✅ Installed",
                    "found": True,
                    "triggers": app_info["triggers"],
                    "category": app_info["category"],
                }
            else:
                installed_apps[app_key] = {
                    "app_name": app_name,
                    "executable": executable,
                    "status": "❌ Not Found",
                    "found": False,
                    "triggers": app_info["triggers"],
                    "category": app_info["category"],
                    "download_url": app_info["download_url"],
                    "install_instructions": app_info["install_instructions"],
                }

        return installed_apps

    def check_third_party_requirements(self):
        """Check all third-party requirements from commands JSON"""
        missing_apps = {}
        available_apps = {}

        for app_key, app_info in self.third_party_apps.items():
            app_name = app_info["app_name"]
            executable = app_info["executable"]

            if self.check_executable_exists(executable):
                available_apps[app_key] = {
                    "app_name": app_name,
                    "executable": executable,
                    "status": "Available",
                    "triggers": app_info["triggers"],
                    "category": app_info["category"],
                }
            else:
                missing_apps[app_key] = {
                    "app_name": app_name,
                    "executable": executable,
                    "download_url": app_info["download_url"],
                    "install_instructions": app_info["install_instructions"],
                    "triggers": app_info["triggers"],
                    "category": app_info["category"],
                    "status": "Missing",
                }

        return {"available": available_apps, "missing": missing_apps}

    def generate_install_suggestions(self):
        """Generate installation suggestions for missing apps"""
        app_status = self.check_third_party_requirements()
        missing_apps = app_status["missing"]

        if not missing_apps:
            print("✅ All third-party applications are available!")
            return

        print("\n" + "=" * 60)
        print("MISSING THIRD-PARTY APPLICATIONS")
        print("=" * 60)

        for app_key, info in missing_apps.items():
            print(f"\n📱 {info['app_name']}")
            print(f"   Status: {info['status']}")
            print(f"   Category: {info['category'].replace('_', ' ').title()}")
            print(f"   Triggers: {', '.join(info['triggers'])}")
            print(f"   Executable: {info['executable']}")
            print(f"   Download: {info['download_url']}")
            print(f"   Instructions: {info['install_instructions']}")

        print(f"\n💡 Install these applications to use their voice commands!")

    def generate_system_report(self):
        """Generate a comprehensive system report"""
        print("\n" + "=" * 60)
        print("VOICE COMMAND SYSTEM REPORT")
        print("=" * 60)

        # Check apps from JSON
        print("\n🔍 THIRD-PARTY APPLICATIONS SCAN (from commands.json):")
        print("-" * 50)
        installed_apps = self.scan_installed_apps()

        if not installed_apps:
            print("  No third-party applications required in commands.json")
        else:
            for app_key, info in installed_apps.items():
                category = info["category"].replace("_", " ").title()
                print(f"  {info['app_name']:20} {info['status']:15} [{category}]")
                print(f"    Triggers: {', '.join(info['triggers'])}")
                if not info["found"]:
                    print(f"    Download: {info.get('download_url', 'N/A')}")

        # Check third-party requirements
        print("\n🎯 VOICE COMMAND REQUIREMENTS SUMMARY:")
        print("-" * 50)
        app_status = self.check_third_party_requirements()

        if app_status["available"]:
            print("  ✅ Available Applications:")
            for app_key, info in app_status["available"].items():
                category = info["category"].replace("_", " ").title()
                print(
                    f"    • {info['app_name']} [{category}] - Triggers: {', '.join(info['triggers'])}"
                )

        if app_status["missing"]:
            print("  ❌ Missing Applications:")
            for app_key, info in app_status["missing"].items():
                category = info["category"].replace("_", " ").title()
                print(
                    f"    • {info['app_name']} [{category}] - Triggers: {', '.join(info['triggers'])}"
                )

        # System information
        print(f"\n💻 SYSTEM INFORMATION:")
        print("-" * 50)
        print(f"  Username: {self.get_username()}")
        print(f"  OS: {os.name}")
        print(f"  Python Executable: {shutil.which('python') or 'Not in PATH'}")
        print(f"  Commands File: {self.commands_file}")

        total_apps = len(installed_apps)
        installed_count = sum(1 for app in installed_apps.values() if app["found"])

        print(f"\n📊 SUMMARY:")
        print("-" * 50)
        print(f"  Total Third-Party Apps in JSON: {total_apps}")
        print(f"  Installed Apps: {installed_count}/{total_apps}")
        print(f"  Available Voice Commands: {len(app_status['available'])}")
        print(f"  Missing Dependencies: {len(app_status['missing'])}")

        if app_status["missing"]:
            print(f"\n🔧 NEXT STEPS:")
            print("-" * 50)
            print("  1. Run option 3 to see detailed installation suggestions")
            print("  2. Install missing applications")
            print("  3. Re-run this report to verify installations")


def main():
    """Main system checker interface"""
    checker = SystemChecker()

    print("\n" + "=" * 50)
    print("DYNAMIC SYSTEM CHECKER")
    print("=" * 50)
    print("1. Scan for third-party apps (from commands.json)")
    print("2. Check voice command requirements")
    print("3. Generate installation suggestions")
    print("4. Generate full system report")
    print("5. Exit")

    choice = input("\nSelect option (1-5): ").strip()

    if choice == "1":
        print("\nScanning for third-party applications from commands.json...")
        installed_apps = checker.scan_installed_apps()
        if not installed_apps:
            print("  No third-party applications found in commands.json")
        else:
            for app_key, info in installed_apps.items():
                print(f"  {info['app_name']}: {info['status']}")
                if info["found"]:
                    print(f"    ✓ Found at: {info['executable']}")
                else:
                    print(f"    ✗ Not found: {info['executable']}")

    elif choice == "2":
        app_status = checker.check_third_party_requirements()
        print(f"\nThird-party app status:")
        print(f"  Available: {len(app_status['available'])} apps")
        print(f"  Missing: {len(app_status['missing'])} apps")

        if app_status["available"]:
            print("\n  Available apps:")
            for app_key, info in app_status["available"].items():
                print(f"    ✅ {info['app_name']}")

        if app_status["missing"]:
            print("\n  Missing apps:")
            for app_key, info in app_status["missing"].items():
                print(f"    ❌ {info['app_name']}")

    elif choice == "3":
        checker.generate_install_suggestions()

    elif choice == "4":
        checker.generate_system_report()

    elif choice == "5":
        print("Goodbye!")
    else:
        print("Invalid choice!")

    print("\nSystem checker completed. Press Enter to exit...")
    input()


if __name__ == "__main__":
    main()
