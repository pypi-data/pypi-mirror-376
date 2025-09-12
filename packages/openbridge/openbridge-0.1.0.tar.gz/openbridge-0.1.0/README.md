> Formerly "claude-code-kimi-groq" - now OpenBridge! Legacy code still available in the `cckg-legacy` branch.

# OpenBridge

Use models like Kimi K2, DeepSeek V3.1, and GLM-4.5 in Claude Code.

Open-source API bridge that enables any LLM to work with Anthropic-compatible tools.

## Quick Start

Quick start using Kimi K2 on Hugging Face

## Usage

```bash
# Install the package
pip install openbridge

# Start the proxy
openbridge --port 8323

# Configure your environment
export ANTHROPIC_API_KEY=NOT_NEEDED # If you are not already logged in to Anthropic
export ANTHROPIC_BASE_URL=http://localhost:8323/

# Run Claude Code
claude
```

CLI options:
- `--host` - Host to bind to (default: 0.0.0.0)
- `--port` - Port to bind to (default: 8323)

## License

BSD-3-Clause