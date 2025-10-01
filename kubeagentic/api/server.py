"""Server script to run KubeAgentic API."""

import uvicorn
import argparse
import os
from pathlib import Path

from kubeagentic.api.app import create_app
from kubeagentic.utils.logging import setup_logging


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info",
    api_keys: list = None,
    agents_dir: str = None,
):
    """
    Run the KubeAgentic API server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload
        log_level: Logging level
        api_keys: List of API keys for authentication
        agents_dir: Directory containing agent configurations to preload
    """
    # Setup logging
    setup_logging(level=log_level.upper())
    
    # Create app
    app = create_app(api_keys=api_keys if api_keys else None)
    
    # Preload agents if directory provided
    if agents_dir and os.path.isdir(agents_dir):
        from kubeagentic.core.manager import AgentManager
        manager = AgentManager()
        
        agents_path = Path(agents_dir)
        for config_file in agents_path.glob("*.yaml"):
            try:
                manager.load_agent(config_path=str(config_file))
                print(f"Loaded agent from: {config_file}")
            except Exception as e:
                print(f"Failed to load agent from {config_file}: {e}")
    
    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
    )


def main():
    """Main entry point for server."""
    parser = argparse.ArgumentParser(description="KubeAgentic API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Logging level")
    parser.add_argument("--api-keys", nargs="+", help="API keys for authentication")
    parser.add_argument("--agents-dir", help="Directory with agent configurations to preload")
    
    args = parser.parse_args()
    
    run_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        api_keys=args.api_keys,
        agents_dir=args.agents_dir,
    )


if __name__ == "__main__":
    main() 