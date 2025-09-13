#!/usr/bin/env python3
"""
PromptBin CLI - Unified command-line interface

Provides a single entry point that runs both MCP server and web interface by default,
with options to run individual components.
"""

import argparse
import logging
import os
import sys

# Configure UTF-8 encoding for Windows to support emojis
if sys.platform == "win32":
    import io

    # Set UTF-8 as default encoding for stdout and stderr
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    # Also set Windows console code page to UTF-8
    os.system("chcp 65001 > nul 2>&1")


def create_parser():
    """Create the argument parser for PromptBin CLI"""
    parser = argparse.ArgumentParser(
        description="PromptBin - MCP Server with Web Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  promptbin                    # Run both MCP server and web interface (default)
  promptbin --mcp              # Run only MCP server
  promptbin --web              # Run only web interface
  promptbin --port 8080        # Run on custom port
  promptbin --data-dir ~/my-prompts  # Use custom data directory
        """,
    )

    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--both",
        action="store_true",
        default=True,
        help="Run both MCP server and web interface (default)",
    )
    mode_group.add_argument("--mcp", action="store_true", help="Run only MCP server")
    mode_group.add_argument("--web", action="store_true", help="Run only web interface")

    # Configuration options
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", type=int, default=5001, help="Port to run on (default: 5001)"
    )
    parser.add_argument(
        "--data-dir",
        default=os.path.expanduser("~/promptbin-data"),
        help="Directory for prompt data (default: ~/promptbin-data)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",  # Remove direct environment variable access
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    # Version
    parser.add_argument("--version", action="version", version="PromptBin 0.4.2")

    return parser


def run_web_only(args):
    """Run only the web interface"""
    from .app import init_app
    from .core.config import PromptBinConfig
    import logging

    # Create configuration with CLI overrides
    config = PromptBinConfig.from_environment()
    config.flask_host = args.host
    config.flask_port = args.port
    config.data_dir = args.data_dir
    config.log_level = args.log_level.upper()
    config.validate()

    # Configure logging
    logging.basicConfig(level=getattr(logging, config.log_level.upper(), logging.INFO))

    print(
        f"🌐 Starting PromptBin web interface at "
        f"http://{config.flask_host}:{config.flask_port}"
    )

    # Initialize and run Flask app
    app = init_app(config)
    app.config["MODE"] = "standalone"
    app.run(host=config.flask_host, port=config.flask_port, debug=True)


def run_mcp_only(args):
    """Run only the MCP server"""
    from .mcp.server import PromptBinMCPServer
    from .core.config import PromptBinConfig

    # Create configuration with CLI overrides
    config = PromptBinConfig.from_environment()
    config.flask_host = args.host
    config.flask_port = args.port
    config.data_dir = args.data_dir
    config.log_level = args.log_level.upper()
    config.validate()

    print("🤖 Starting PromptBin MCP server...")

    # Create and run MCP server with configuration
    server = PromptBinMCPServer(config=config)
    return server.mcp.run()


def run_both(args):
    """Run both MCP server and web interface
    (MCP server will launch Flask subprocess)"""
    from .mcp.server import PromptBinMCPServer
    from .core.config import PromptBinConfig

    # Create configuration with CLI overrides
    config = PromptBinConfig.from_environment()
    config.flask_host = args.host
    config.flask_port = args.port
    config.data_dir = args.data_dir
    config.log_level = args.log_level.upper()
    config.validate()

    print("🚀 Starting PromptBin (MCP server + web interface)...")
    print("🤖 MCP server: Ready for AI tool connections")
    print(
        f"🌐 Web interface: Will be available at "
        f"http://{config.flask_host}:{config.flask_port}"
    )
    print("💡 Note: Web interface runs as a subprocess when in MCP mode")

    # Create and run MCP server with configuration
    server = PromptBinMCPServer(config=config)
    return server.mcp.run()


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Determine which mode to run
    if args.mcp:
        mode = "mcp"
    elif args.web:
        mode = "web"
    else:
        mode = "both"  # Default

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        if mode == "web":
            run_web_only(args)
        elif mode == "mcp":
            return run_mcp_only(args)
        else:  # both
            return run_both(args)
    except KeyboardInterrupt:
        print("\n👋 PromptBin stopped")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
