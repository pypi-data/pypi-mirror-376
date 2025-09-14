from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import webbrowser
import json
import shutil
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import base64
from PIL import ImageGrab, Image
import io
import requests
import threading
from functools import lru_cache
import time

try:
    from importlib.resources import files
except ImportError:
    # Fallback for Python < 3.9
    try:
        from importlib_resources import files
    except ImportError:
        # Final fallback using pkg_resources
        import pkg_resources
        
        def files(package):
            """Minimal fallback implementation"""
            class FilesCompat:
                def __init__(self, package_name):
                    self.package_name = package_name
                
                def joinpath(self, *parts):
                    path = "/".join(parts)
                    try:
                        return pkg_resources.resource_string(self.package_name, path)
                    except:
                        return b""
                        
                def read_text(self, encoding="utf-8"):
                    return self.joinpath().decode(encoding)
            
            return FilesCompat(package)

# Load environment variables from .env file
load_dotenv()


class CommandProcessor:
    def __init__(self):
        # Load commands from JSON file
        self.commands = self.load_commands()

        # Cache for command lookup optimization
        self._command_cache = {}
        self._build_command_cache()

        # Initialize OpenAI client for conversation handling
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("⚠️  WARNING: OPENROUTER_API_KEY not found in .env file!")
            print("   Please add your API key to the .env file")
            api_key = "your_api_key_here"  # Fallback

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        print("Command processor initialized and ready!")
        print("AI conversation handler loaded!")

    def _build_command_cache(self):
        """Build a cache for faster command lookup"""
        for category, commands in self.commands.items():
            for cmd_config in commands:
                for trigger in cmd_config["triggers"]:
                    self._command_cache[trigger.lower()] = cmd_config

    @lru_cache(maxsize=128)
    def load_commands(self):
        """Load commands from JSON file with caching"""
        try:
            # Try to load from package data first
            try:
                # Use modern importlib.resources instead of deprecated pkg_resources
                package_files = files("siphoai") / "data" / "commands.json"
                with package_files.open("r", encoding="utf-8") as file:
                    return json.load(file)
            except:
                # Fallback to local file
                with open("commands.json", "r", encoding="utf-8") as file:
                    return json.load(file)
        except FileNotFoundError:
            print("Error: commands.json file not found!")
            return {}
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in commands.json!")
            return {}

    def get_ai_response(self, user_message, context="general"):
        """Get AI response for conversations and command feedback"""
        try:
            # Create system message based on context
            if context == "success":
                system_message = "You are Sipho AI, a helpful voice assistant. The user's command was executed successfully. Provide a brief, friendly confirmation response."
            elif context == "failure":
                system_message = "You are Sipho AI, a helpful voice assistant. The user's command failed to execute. Provide a brief, helpful response suggesting alternatives or troubleshooting."
            else:
                system_message = "You are Sipho AI, a helpful voice assistant. Respond to the user's message in a friendly, concise manner."

            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": os.getenv("SITE_URL", "http://localhost:5000"),
                    "X-Title": os.getenv("SITE_NAME", "Sipho AI Voice Assistant"),
                },
                extra_body={},
                model="moonshotai/kimi-k2:free",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
            )

            return completion.choices[0].message.content

        except Exception as e:
            print(f"AI response error: {e}")
            # Fallback responses based on context
            if context == "success":
                return "Command executed successfully!"
            elif context == "failure":
                return "Sorry, I couldn't execute that command. Please try again."
            else:
                return "I'm here to help! You can ask me to open apps, search the web, or check the time."

    def enhance_response_with_ai(self, result, original_command):
        """Enhance command results with AI-generated responses"""
        try:
            if result["success"]:
                # Get AI enhancement for success messages
                ai_response = self.get_ai_response(
                    f"I successfully executed the command: {original_command}. The result was: {result['message']}",
                    context="success",
                )
                result["ai_message"] = ai_response
            else:
                # Get AI enhancement for failure messages
                ai_response = self.get_ai_response(
                    f"I couldn't execute the command: {original_command}. The error was: {result['message']}",
                    context="failure",
                )
                result["ai_message"] = ai_response

        except Exception as e:
            print(f"AI enhancement error: {e}")
            # Keep original message if AI fails
            pass

        return result

    def check_executable_exists(self, executable_path):
        """Check if an executable exists in the system"""
        # Expand environment variables
        expanded_path = os.path.expandvars(executable_path)

        # Check if it's a full path
        if os.path.isabs(expanded_path):
            return os.path.exists(expanded_path)

        # Check if it's in PATH
        return shutil.which(executable_path) is not None

    def handle_missing_third_party_app(self, third_party_info):
        """Handle missing third-party application"""
        app_name = third_party_info["app_name"]
        download_url = third_party_info["download_url"]
        install_instructions = third_party_info["install_instructions"]

        return {
            "success": False,
            "error": "missing_application",
            "app_name": app_name,
            "download_url": download_url,
            "install_instructions": install_instructions,
            "message": f"{app_name} is not installed or not found.",
        }

    def take_screenshot(self):
        """Take a screenshot and return the image path and PIL image"""
        try:
            # Create screenshots directory if it doesn't exist
            screenshots_dir = "screenshots"
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)

            # Take screenshot
            screenshot = ImageGrab.grab()

            # Save with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)

            screenshot.save(filepath)
            print(f"Screenshot saved: {filepath}")
            return filepath, screenshot
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None, None

    def analyze_screen_with_ai(self, screenshot_image):
        """Analyze screenshot using direct OpenRouter API requests (more reliable for vision)"""
        try:
            # Resize image to reduce payload size
            max_size = 1024
            original_width, original_height = screenshot_image.size

            if original_width > max_size or original_height > max_size:
                # Calculate new size maintaining aspect ratio
                if original_width > original_height:
                    new_width = max_size
                    new_height = int((original_height * max_size) / original_width)
                else:
                    new_height = max_size
                    new_width = int((original_width * max_size) / original_height)

                screenshot_image = screenshot_image.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS
                )
                print(
                    f"Resized screenshot from {original_width}x{original_height} to {new_width}x{new_height}"
                )

            # Convert PIL image to base64
            buffer = io.BytesIO()
            screenshot_image.save(buffer, format="JPEG", quality=85, optimize=True)
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            data_url = f"data:image/jpeg;base64,{base64_image}"

            print(f"Image size after compression: {len(base64_image)} characters")
            print("Sending screenshot to OpenRouter for analysis...")

            # Direct API call to OpenRouter (more reliable than OpenAI client for vision)
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("SITE_URL", "http://localhost:5000"),
                "X-Title": os.getenv("SITE_NAME", "Sipho AI Voice Assistant"),
            }

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this screenshot and describe what you see. Include details about what applications or windows are open, what the user might be doing, and any important information visible. Be detailed but concise.",
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ]

            payload = {
                "model": "google/gemini-2.0-flash-001",  # Using Gemini for vision as in your example
                "messages": messages,
                "max_tokens": 400,
                "temperature": 0.3,
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()  # Raise exception for HTTP errors

            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "I took the screenshot but couldn't analyze it. The API response was unexpected."

        except requests.exceptions.RequestException as e:
            print(f"Network error analyzing screenshot: {e}")
            return f"I took the screenshot but couldn't analyze it due to a network error: {str(e)}"
        except Exception as e:
            print(f"Error analyzing screenshot: {e}")
            return f"I took the screenshot but couldn't analyze it. Error: {str(e)}"

    def is_likely_command(self, text):
        """Determine if input is likely a command vs conversation"""
        command_indicators = [
            "open",
            "launch",
            "start",
            "run",
            "execute",
            "play",
            "stop",
            "search",
            "find",
            "google",
            "youtube",
            "website",
            "volume",
            "sound",
            "mute",
            "unmute",
            "increase",
            "decrease",
            "time",
            "date",
            "calendar",
            "weather",
            "calculator",
            "help",
            "commands",
            "what can you do",
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in command_indicators)

    def execute_command(self, command, confirmed=False):
        """Execute the command using JSON configuration or handle as conversation - OPTIMIZED"""
        if not command:
            return {"success": False, "message": "No command provided"}

        command_lower = command.lower()

        # Fast cache lookup first
        for trigger, cmd_config in self._command_cache.items():
            if trigger in command_lower:
                result = self.process_command(cmd_config, command, confirmed)
                # Enhance with AI response in background for non-critical commands
                if cmd_config.get("action") not in ["system_command", "volume_control"]:
                    threading.Thread(
                        target=self._enhance_response_async, args=(result, command)
                    ).start()
                    return result
                else:
                    return self.enhance_response_with_ai(result, command)

        # If no specific command found, handle as conversation
        return self._handle_conversation(command)

    def _handle_conversation(self, command):
        """Handle conversational queries with optimized AI calls"""
        try:
            # Check if this seems like a command attempt or pure conversation
            if self.is_likely_command(command):
                # Seems like a command but no match found - get AI help with alternatives
                system_message = """You are Sipho AI, a helpful voice assistant. The user tried to execute a command that I don't recognize. 
                Provide a helpful response suggesting similar commands I might support, or ask for clarification. 
                Keep it brief and friendly. Mention they can say 'help' to see available commands."""
            else:
                # Pure conversational query - respond naturally
                system_message = """You are Sipho AI, a helpful voice assistant. The user is having a conversation with you. 
                Respond naturally and helpfully to their message. Keep responses concise but friendly."""

            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "Sipho AI Voice Assistant",
                },
                extra_body={},
                model="moonshotai/kimi-k2:free",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": command},
                ],
                timeout=10,  # Add timeout for faster response
            )

            ai_response = completion.choices[0].message.content

            return {
                "success": True,
                "message": ai_response,
                "action": "conversation",
                "is_ai_response": True,
                "type": (
                    "command_attempt"
                    if self.is_likely_command(command)
                    else "conversation"
                ),
            }

        except Exception as e:
            print(f"AI response error: {e}")
            return {
                "success": False,
                "message": "I didn't understand that. Try saying 'help' to see available commands, or ask me a question!",
                "suggestion": "Say 'help' for available commands",
            }

    def _enhance_response_async(self, result, original_command):
        """Enhance response with AI in background thread"""
        try:
            self.enhance_response_with_ai(result, original_command)
        except Exception as e:
            print(f"Background AI enhancement error: {e}")

    def process_command(self, cmd_config, original_command, confirmed=False):
        """Process a matched command based on its action type"""
        action = cmd_config["action"]
        response = cmd_config["response"]

        # Check if command requires confirmation and not already confirmed
        if cmd_config.get("requires_confirmation", False) and not confirmed:
            confirmation_message = cmd_config.get(
                "confirmation_message", "Are you sure you want to execute this command?"
            )
            return {
                "requires_confirmation": True,
                "question": confirmation_message,
                "message": f"{confirmation_message} Please confirm to proceed.",
            }

        # Check if command requires third-party app
        if "requires_third_party" in cmd_config:
            third_party_info = cmd_config["requires_third_party"]
            executable = third_party_info["executable"]

            if not self.check_executable_exists(executable):
                return self.handle_missing_third_party_app(third_party_info)

        try:
            if action == "web_open":
                webbrowser.open(cmd_config["url"])
                return {
                    "success": True,
                    "message": response,
                    "action": "web_open",
                    "url": cmd_config["url"],
                }

            elif action == "run_application":
                # Expand environment variables in command
                command = [os.path.expandvars(arg) for arg in cmd_config["command"]]
                subprocess.run(command)
                return {
                    "success": True,
                    "message": response,
                    "action": "run_application",
                }

            elif action == "system_command":
                subprocess.run(cmd_config["command"])
                return {
                    "success": True,
                    "message": response,
                    "action": "system_command",
                }

            elif action == "volume_control":
                subprocess.run(cmd_config["command"])
                return {
                    "success": True,
                    "message": response,
                    "action": "volume_control",
                }

            elif action == "get_time":
                current_time = datetime.now().strftime("%I:%M %p")
                return {
                    "success": True,
                    "message": f"{response} {current_time}",
                    "action": "get_time",
                    "time": current_time,
                }

            elif action == "get_date":
                current_date = datetime.now().strftime("%B %d, %Y")
                return {
                    "success": True,
                    "message": f"{response} {current_date}",
                    "action": "get_date",
                    "date": current_date,
                }

            elif action == "web_search":
                search_term = original_command.replace("search for", "").strip()
                if search_term:
                    search_url = f"https://www.google.com/search?q={search_term}"
                    webbrowser.open(search_url)
                    return {
                        "success": True,
                        "message": f"{response} {search_term}",
                        "action": "web_search",
                        "search_term": search_term,
                        "url": search_url,
                    }
                else:
                    return {
                        "success": False,
                        "message": "What would you like me to search for?",
                        "action": "web_search",
                    }

            elif action == "show_help":
                help_data = self.get_help_data()
                return {
                    "success": True,
                    "message": response,
                    "action": "show_help",
                    "help_data": help_data,
                }

            elif action == "analyze_screen":
                try:
                    filepath, screenshot = self.take_screenshot()
                    if screenshot:
                        analysis = self.analyze_screen_with_ai(screenshot)
                        return {
                            "success": True,
                            "message": f"📸 {response}\n\n🔍 Analysis: {analysis}",
                            "action": "analyze_screen",
                            "screenshot_path": filepath,
                            "analysis": analysis,
                        }
                    else:
                        return {
                            "success": False,
                            "message": "Failed to take screenshot. Please check your display settings and permissions.",
                            "action": "analyze_screen",
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Error analyzing screen: {str(e)}",
                        "action": "analyze_screen",
                    }

            elif action == "take_screenshot":
                try:
                    filepath, screenshot = self.take_screenshot()
                    if filepath:
                        return {
                            "success": True,
                            "message": f"📸 Screenshot saved to: {filepath}",
                            "action": "take_screenshot",
                            "screenshot_path": filepath,
                        }
                    else:
                        return {
                            "success": False,
                            "message": "Failed to take screenshot. Please check your display settings and permissions.",
                            "action": "take_screenshot",
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Error taking screenshot: {str(e)}",
                        "action": "take_screenshot",
                    }

            elif action == "exit_app":
                return {"success": True, "message": response, "action": "exit_app"}

        except FileNotFoundError:
            if "requires_third_party" in cmd_config:
                return self.handle_missing_third_party_app(
                    cmd_config["requires_third_party"]
                )
            else:
                return {
                    "success": False,
                    "message": "Could not find the application. Make sure it's installed.",
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"There was an error executing the command: {str(e)}",
            }

        return {"success": False, "message": "Unknown command action"}

    @lru_cache(maxsize=1)
    def get_help_data(self):
        """Get available commands data structure for API response - CACHED"""
        help_data = {}

        for category, commands in self.commands.items():
            category_name = category.replace("_", " ").title()
            help_data[category_name] = []

            for cmd_config in commands:
                triggers = cmd_config["triggers"][:2]  # Show first 2 triggers
                help_data[category_name].append(
                    {
                        "triggers": triggers,
                        "description": cmd_config.get(
                            "response", "No description available"
                        ),
                    }
                )

        return help_data


def create_flask_app():
    """Create and configure the Flask application"""
    # Get the package directory for static files
    try:
        package_path = files("siphoai")
        static_folder = str(package_path / "static")
    except:
        # Fallback to local static folder
        static_folder = "static"

    app = Flask(__name__, static_folder=static_folder)
    CORS(app, origins=["https://siphoai.vercel.app", "http://localhost:5173"])

    # Initialize the command processor
    command_processor = CommandProcessor()

    # Homepage route - Serves external HTML file
    @app.route("/")
    def home():
        """Serve homepage from external HTML file"""
        try:
            # Load external HTML file
            template_path = files("siphoai") / "templates" / "index.html"
            with template_path.open("r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            return f"""
            <html>
                <head><title>Sipho AI - Error</title></head>
                <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
                    <h1>🎤 Sipho AI Server</h1>
                    <p>Error loading homepage: {str(e)}</p>
                    <p>Server is running. Try the API endpoints:</p>
                    <ul>
                        <li><a href="/api/status">GET /api/status</a></li>
                        <li><a href="/api/help">GET /api/help</a></li>
                    </ul>
                </body>
            </html>
            """

    # Server info API for dynamic content
    @app.route("/api/server-info")
    def get_server_info():
        """Get server information including QR code for dynamic loading"""
        import socket
        import qrcode
        import io
        import base64

        try:
            # Get local IP address
            hostname = socket.gethostname()
            try:
                # Try to get the actual network IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except:
                local_ip = socket.gethostbyname(hostname)

            port = os.getenv("FLASK_PORT", "5000")
            server_url = f"http://{local_ip}:{port}"

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(server_url)
            qr.make(fit=True)

            # Convert QR code to base64
            qr_img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()

            return jsonify(
                {
                    "success": True,
                    "server_url": server_url,
                    "local_ip": local_ip,
                    "port": port,
                    "qr_base64": qr_base64,
                }
            )

        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "server_url": "http://localhost:5000",
                    "local_ip": "localhost",
                    "port": "5000",
                    "qr_base64": "",
                }
            )

    # Flask routes - API only (OPTIMIZED)
    @app.route("/api/command", methods=["POST"])
    def handle_command():
        """Handle both command execution and conversation via AI - OPTIMIZED"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "No data provided"}), 400

            command = data.get("command", "").strip()
            confirmed = data.get("confirmed", False)

            if not command:
                return (
                    jsonify({"success": False, "message": "No command provided"}),
                    400,
                )

            # Add request timing for monitoring
            start_time = time.time()
            result = command_processor.execute_command(command, confirmed)
            processing_time = time.time() - start_time

            result["processing_time"] = round(processing_time, 3)

            # Log the conversation
            log_conversation(
                command=command,
                response=result.get("message", ""),
                success=result.get("success"),
                action=result.get("action"),
                error=result.get("message") if not result.get("success") else None,
                response_time=int(processing_time * 1000),  # Convert to milliseconds
            )

            return jsonify(result)

        except Exception as e:
            error_msg = f"Server error: {str(e)}"
            # Log the error
            log_conversation(
                command=command if "command" in locals() else "Unknown",
                response="",
                success=False,
                error=error_msg,
                response_time=None,
            )
            return jsonify({"success": False, "message": error_msg}), 500

    @app.route("/api/help", methods=["GET"])
    def get_help():
        """Get help information via API - CACHED"""
        try:
            help_data = command_processor.get_help_data()
            return jsonify({"success": True, "help_data": help_data})
        except Exception as e:
            return (
                jsonify({"success": False, "message": f"Server error: {str(e)}"}),
                500,
            )

    @app.route("/api/status", methods=["GET"])
    def get_status():
        """Get server status"""
        # Check if API key is configured
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        ai_enabled = bool(api_key and api_key != "your_api_key_here")

        return jsonify(
            {
                "success": True,
                "message": "Sipho AI Command Server is running with AI conversation support",
                "commands_loaded": len(command_processor.commands),
                "ai_enabled": ai_enabled,
                "features": [
                    "voice_commands",
                    "ai_conversation",
                    "web_search",
                    "app_launching",
                ],
            }
        )

    @app.route("/api/test-openrouter-key", methods=["POST"])
    def test_openrouter_key():
        """Test OpenRouter API key"""
        try:
            data = request.get_json()
            if not data or "api_key" not in data:
                return jsonify({"success": False, "message": "API key required"}), 400

            api_key = data["api_key"].strip()
            if not api_key:
                return (
                    jsonify({"success": False, "message": "API key cannot be empty"}),
                    400,
                )

            # Test the API key by making a simple request
            test_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )

            completion = test_client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": os.getenv("SITE_URL", "http://localhost:5000"),
                    "X-Title": os.getenv("SITE_NAME", "Sipho AI Voice Assistant"),
                },
                model="moonshotai/kimi-k2:free",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )

            return jsonify(
                {
                    "success": True,
                    "message": "API key is valid",
                    "model": "moonshotai/kimi-k2:free",
                }
            )

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                return jsonify({"success": False, "message": "Invalid API key"}), 200
            elif "403" in error_msg or "forbidden" in error_msg.lower():
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "API key lacks required permissions",
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {"success": False, "message": f"API test failed: {error_msg}"}
                    ),
                    200,
                )

    @app.route("/api/save-config", methods=["POST"])
    def save_config():
        """Save API configuration to .env file"""
        try:
            data = request.get_json()
            if not data or "openrouter_api_key" not in data:
                return jsonify({"success": False, "message": "API key required"}), 400

            api_key = data["openrouter_api_key"].strip()
            if not api_key:
                return (
                    jsonify({"success": False, "message": "API key cannot be empty"}),
                    400,
                )

            # Path to .env file
            env_path = ".env"

            # Read existing .env content
            env_content = []
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    env_content = f.readlines()

            # Update or add the API key
            updated = False
            for i, line in enumerate(env_content):
                if line.strip().startswith("OPENROUTER_API_KEY="):
                    env_content[i] = f"OPENROUTER_API_KEY={api_key}\n"
                    updated = True
                    break

            if not updated:
                env_content.append(f"OPENROUTER_API_KEY={api_key}\n")

            # Write back to .env file
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(env_content)

            # Update environment variable for current session
            os.environ["OPENROUTER_API_KEY"] = api_key

            # Update the command processor's client
            command_processor.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )

            return jsonify(
                {
                    "success": True,
                    "message": "Configuration saved successfully. API key updated.",
                }
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Failed to save configuration: {str(e)}",
                    }
                ),
                500,
            )

    @app.route("/api/conversation-logs", methods=["GET"])
    def get_conversation_logs():
        """Get conversation logs"""
        try:
            # Get logs from file or database (for now, we'll use a simple file-based approach)
            logs_file = "conversation_logs.json"

            if os.path.exists(logs_file):
                with open(logs_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []

            # Sort by timestamp (most recent first)
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return jsonify({"success": True, "logs": logs, "total_count": len(logs)})

        except Exception as e:
            return (
                jsonify(
                    {"success": False, "message": f"Failed to load logs: {str(e)}"}
                ),
                500,
            )

    @app.route("/api/clear-logs", methods=["POST"])
    def clear_conversation_logs():
        """Clear all conversation logs"""
        try:
            logs_file = "conversation_logs.json"

            # Clear the logs file
            with open(logs_file, "w", encoding="utf-8") as f:
                json.dump([], f)

            return jsonify({"success": True, "message": "Logs cleared successfully"})

        except Exception as e:
            return (
                jsonify(
                    {"success": False, "message": f"Failed to clear logs: {str(e)}"}
                ),
                500,
            )

    def log_conversation(
        command, response, success=None, action=None, error=None, response_time=None
    ):
        """Log a conversation to the logs file"""
        try:
            logs_file = "conversation_logs.json"

            # Load existing logs
            if os.path.exists(logs_file):
                with open(logs_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []

            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "response": response,
                "success": success,
                "action": action,
                "error": error,
                "response_time": response_time,
                "type": "conversation" if success is None else "command",
            }

            # Add to logs (keep only last 1000 entries)
            logs.append(log_entry)
            if len(logs) > 1000:
                logs = logs[-1000:]

            # Save logs
            with open(logs_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)

        except Exception as e:
            print(f"Failed to log conversation: {e}")

    # Optimize Flask for production
    app.config["JSON_SORT_KEYS"] = False  # Faster JSON serialization
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False  # Smaller response size

    return app


def run_server():
    """Run the Flask server with optimized configuration"""
    import logging
    import sys

    app = create_flask_app()

    # Get Flask configuration from environment variables
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    # Suppress all Flask startup messages
    if not debug:
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        # Disable Flask's startup messages
        cli = sys.modules["flask.cli"]
        cli.show_server_banner = lambda *x: None

    print("🚀 Starting Sipho AI Command API Server...")
    print(f"📡 Server running on: http://localhost:{port}")
    print("💡 API endpoints:")
    print("   • POST /api/command - Execute commands & AI conversations")
    print("   • GET /api/help - Available commands")
    print("   • GET /api/status - Server status")
    print("")
    print("✅ AI Integration: Enhanced with conversational responses")
    print("✅ Smart Detection: Commands vs conversations auto-detected")
    print("⚠️  Add your OpenRouter API key to .env file for AI features")
    print("")
    print("🎤 Ready to process voice commands!")
    print("Press CTRL+C to stop the server")

    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)


if __name__ == "__main__":
    run_server()
