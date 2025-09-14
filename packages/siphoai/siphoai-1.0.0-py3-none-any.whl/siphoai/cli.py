#!/usr/bin/env python3
"""
Sipho AI Command Line Interface
Entry point for the siphoai command
"""

import argparse
import sys
import os
from .app import run_server, CommandProcessor

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='siphoai',
        description='Sipho AI - Voice Command Assistant'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='%(prog)s 1.0.0'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind the server to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind the server to (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server command (default)
    server_parser = subparsers.add_parser('server', help='Start the API server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    server_parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    server_parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test a command')
    test_parser.add_argument('text', help='Command text to test')
    
    # Help command
    help_parser = subparsers.add_parser('help-commands', help='Show available voice commands')
    
    args = parser.parse_args()
    
    # Set environment variables for Flask configuration
    os.environ['FLASK_HOST'] = args.host
    os.environ['FLASK_PORT'] = str(args.port)
    os.environ['FLASK_DEBUG'] = 'true' if args.debug else 'false'
    
    if args.command == 'test':
        # Test a command without starting the server
        processor = CommandProcessor()
        result = processor.execute_command(args.text)
        print(f"Command: {args.text}")
        print(f"Result: {result}")
        return
    elif args.command == 'help-commands':
        # Show available commands
        processor = CommandProcessor()
        help_data = processor.get_help_data()
        
        print("\n🎤 Sipho AI - Available Voice Commands")
        print("=" * 50)
        
        for category, commands in help_data.items():
            print(f"\n📂 {category}:")
            for cmd in commands:
                triggers = ", ".join(f'"{t}"' for t in cmd['triggers'])
                print(f"  • {triggers}")
                print(f"    → {cmd['description']}")
        
        print(f"\n💡 Usage: Just say any of these phrases to execute the command!")
        print(f"💡 Start the server with: siphoai")
        return
    else:
        # Default: start server
        print("🚀 Starting Sipho AI Voice Command Assistant...")
        print("💡 Use 'siphoai help-commands' to see available voice commands")
        print("💡 Use 'siphoai test \"your command\"' to test commands")
        print("")
        
        # Check for .env file
        if not os.path.exists('.env'):
            print("⚠️  WARNING: No .env file found!")
            print("   Create a .env file with your OPENROUTER_API_KEY for AI features")
            print("   Example: echo 'OPENROUTER_API_KEY=your_key_here' > .env")
            print("")
        
        run_server()


if __name__ == '__main__':
    main()