import threading
import time

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openai import OpenAI

from .config import OpenBridgeConfig
from .models import MessagesRequest
from .proxy import AnthropicToOpenAIProxy
from .templates import get_homepage_html


def create_app(config: OpenBridgeConfig, host: str, port: int) -> FastAPI:
    """Create FastAPI app for self-hosted proxy using configuration."""
    app = FastAPI(title="OpenBridge Self-Hosted Proxy")

    if not config.api_key:
        raise ValueError(
            "API key required. Set OPENAI_API_KEY environment variable, configure huggingface-hub, or add api_key to openbridge.yaml"
        )

    # Initialize OpenAI client and proxy
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    proxy = AnthropicToOpenAIProxy(client, config.model, config.max_tokens)

    @app.post("/v1/messages")
    async def messages(request: MessagesRequest):
        return await proxy.process_request(request)

    @app.get("/", response_class=HTMLResponse)
    def root():
        return get_homepage_html(config.model, host, port)

    @app.get("/health")
    def health():
        return {"status": "healthy", "model": config.model}

    return app


class ProxyServer:
    """Manages the OpenBridge proxy server lifecycle."""

    def __init__(self, config: OpenBridgeConfig, host: str, port: int):
        self.config = config
        self.host = host
        self.port = port
        self.app = create_app(config, host, port)
        self.server_thread = None
        self.server_should_stop = threading.Event()
        self.server = None

    def start(self):
        """Start the proxy server in a background thread."""

        def run_server():
            """Run the uvicorn server in a thread."""
            uvicorn_config = uvicorn.Config(
                self.app, host=self.host, port=self.port, log_level="warning"
            )
            self.server = uvicorn.Server(uvicorn_config)

            try:
                self.server.run()
            except Exception as e:
                if not self.server_should_stop.is_set():
                    print(f"❌ Server error: {e}")

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Wait for server to start
        time.sleep(2)

    def stop(self):
        """Stop the proxy server gracefully."""
        print("\n🛑 Shutting down OpenBridge proxy...")
        self.server_should_stop.set()

        if self.server:
            try:
                self.server.should_exit = True
            except:
                pass

        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=3)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
