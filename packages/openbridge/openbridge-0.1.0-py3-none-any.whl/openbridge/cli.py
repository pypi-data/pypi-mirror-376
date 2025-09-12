import click
import uvicorn
from dotenv import load_dotenv
from rich import print

from .command import ClaudeRunner
from .config import load_config, print_config_info
from .server import create_app

load_dotenv()


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8323, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def main(host: str, port: int, reload: bool):
    """OpenBridge Self-Hosted Proxy CLI."""
    config = load_config()

    print(f"🌉 OpenBridge proxy starting on {host}:{port}")
    print(f"📋 Config: ANTHROPIC_BASE_URL=http://{host}:{port}/")
    print_config_info(config)

    app = create_app(config, host, port)
    uvicorn.run(app, host=host, port=port, reload=reload, log_level="warning")


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind proxy to")
@click.option("--port", default=8323, type=int, help="Port to bind proxy to")
def obcli(host: str, port: int):
    """Start OpenBridge proxy and run claude command, stopping proxy when claude exits."""
    config = load_config()

    # Show configuration info
    print_config_info(config)
    print()

    # Create and run the claude runner
    runner = ClaudeRunner(config, host, port)
    runner.run()


if __name__ == "__main__":
    main()
