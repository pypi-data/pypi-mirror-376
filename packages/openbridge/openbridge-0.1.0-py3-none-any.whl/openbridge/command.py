import os
import shutil
import signal
import subprocess
import sys
from typing import Optional

from .config import OpenBridgeConfig
from .server import ProxyServer


class ClaudeCommandFinder:
    """Utility to find and validate claude command."""

    @staticmethod
    def find() -> str:
        """Find claude command across different platforms."""
        possible_commands = ["claude", "claude.exe"]

        for cmd in possible_commands:
            if shutil.which(cmd):
                return cmd

        raise FileNotFoundError(
            "'claude' command not found in PATH. Please install the claude CLI tool."
        )


class ClaudeRunner:
    """Manages running claude command with proxy integration."""

    def __init__(
        self, config: OpenBridgeConfig, host: str = "0.0.0.0", port: int = 8323
    ):
        self.config = config
        self.host = host
        self.port = port
        self.claude_cmd = ClaudeCommandFinder.find()
        self.proxy_server: Optional[ProxyServer] = None

    def setup_signal_handlers(self):
        """Setup signal handlers for clean shutdown."""

        def signal_handler(signum, frame):
            if self.proxy_server:
                self.proxy_server.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def run(self):
        """Run claude with proxy server."""
        print(f"🌉 Starting OpenBridge proxy on {self.host}:{self.port}")
        print(f"🤖 Found claude command: {self.claude_cmd}")

        self.setup_signal_handlers()

        try:
            # Start proxy server using context manager
            with ProxyServer(self.config, self.host, self.port) as server:
                self.proxy_server = server

                # Set environment variable for claude to use our proxy
                env = os.environ.copy()
                env["ANTHROPIC_BASE_URL"] = f"http://{self.host}:{self.port}/"

                print(
                    f"🚀 Starting claude with ANTHROPIC_BASE_URL=http://{self.host}:{self.port}/"
                )

                # Run claude command
                claude_process = subprocess.run([self.claude_cmd], env=env)

                print(f"📋 Claude exited with code: {claude_process.returncode}")

        except KeyboardInterrupt:
            print("\n⏹️  Interrupted by user")
        except FileNotFoundError as e:
            print(f"❌ {e}")
            print("Please install the claude CLI tool or ensure it's in your PATH")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
