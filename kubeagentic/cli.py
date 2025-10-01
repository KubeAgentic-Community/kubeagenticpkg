"""Command-line interface for KubeAgentic."""

import logging
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table

from kubeagentic import __version__
from kubeagentic.config.parser import ConfigParser
from kubeagentic.config.validator import ConfigValidator
from kubeagentic.core.agent import Agent
from kubeagentic.core.manager import AgentManager

app = typer.Typer(
    name="kubeagentic",
    help="KubeAgentic - Build AI agents from YAML configuration",
    add_completion=False,
)
console = Console()


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold green]KubeAgentic[/bold green] version [cyan]{__version__}[/cyan]")


@app.command()
def validate(
    config_file: Path = typer.Argument(..., help="Path to agent configuration file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Validate an agent configuration file.
    
    Example:
        kubeagentic validate examples/simple_agent.yaml
    """
    try:
        console.print(f"[yellow]Validating configuration:[/yellow] {config_file}")
        
        # Parse configuration
        config = ConfigParser.parse_file(config_file)
        
        # Validate
        warnings = ConfigValidator.validate(config)
        
        # Check environment
        env_check = ConfigValidator.check_environment(config)
        
        console.print("[green]✓[/green] Configuration is valid!")
        console.print(f"[blue]Agent:[/blue] {config.agent.name}")
        console.print(f"[blue]Description:[/blue] {config.agent.description}")
        
        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  [yellow]⚠[/yellow]  {warning}")
        
        if env_check["warnings"]:
            console.print("\n[yellow]Environment warnings:[/yellow]")
            for warning in env_check["warnings"]:
                console.print(f"  [yellow]⚠[/yellow]  {warning}")
        
        if verbose:
            console.print("\n[blue]API Keys Status:[/blue]")
            for provider, has_key in env_check["api_keys"].items():
                status = "[green]✓[/green]" if has_key else "[red]✗[/red]"
                console.print(f"  {status} {provider}")
        
    except Exception as e:
        console.print(f"[red]✗ Validation failed:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def test(
    config_file: Path = typer.Argument(..., help="Path to agent configuration file"),
    message: str = typer.Option("Hello!", "--message", "-m", help="Test message"),
):
    """
    Test an agent locally with a sample message.
    
    Example:
        kubeagentic test examples/simple_agent.yaml --message "What is Python?"
    """
    try:
        console.print(f"[yellow]Loading agent from:[/yellow] {config_file}")
        
        # Create agent
        agent = Agent.from_config_file(config_file)
        console.print(f"[green]✓[/green] Agent '{agent.name}' loaded successfully!")
        
        console.print(f"\n[blue]Sending message:[/blue] {message}")
        
        # Invoke agent
        response = agent.invoke(message)
        
        console.print(f"\n[green]Response:[/green]")
        console.print(response["content"])
        
    except Exception as e:
        console.print(f"[red]✗ Test failed:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def serve(
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to agent configuration file"),
    config_dir: Optional[Path] = typer.Option(None, "--config-dir", "-d", help="Directory containing agent configs"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
    log_level: str = typer.Option("info", "--log-level", help="Logging level"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for authentication"),
):
    """
    Start the API server (Phase 2).
    
    Example:
        kubeagentic serve --config examples/vllm_simple.yaml --port 8000
        kubeagentic serve --config-dir examples/ --port 8000 --reload
    """
    try:
        from kubeagentic.api.server import run_server
        
        console.print("[bold green]Starting KubeAgentic API Server (Phase 2)[/bold green]")
        console.print(f"Host: {host}")
        console.print(f"Port: {port}")
        console.print(f"Auto-reload: {reload}")
        console.print(f"Log level: {log_level}")
        
        if api_key:
            console.print("[green]✓[/green] Authentication: Enabled")
            api_keys = [api_key]
        else:
            console.print("[yellow]⚠[/yellow] Authentication: Disabled (no API key)")
            api_keys = None
        
        agents_dir = None
        if config_dir:
            console.print(f"[blue]Preloading agents from:[/blue] {config_dir}")
            agents_dir = str(config_dir)
        elif config_file:
            console.print(f"[blue]Preloading agent from:[/blue] {config_file}")
            # For single file, we'll load it via the manager after startup
            agents_dir = str(config_file.parent)
        
        console.print(f"\n[bold]Server will be available at:[/bold] http://{host}:{port}")
        console.print(f"[bold]API Documentation:[/bold] http://{host}:{port}/docs")
        console.print(f"[bold]OpenAPI Schema:[/bold] http://{host}:{port}/openapi.json\n")
        
        run_server(
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            api_keys=api_keys,
            agents_dir=agents_dir,
        )
        
    except ImportError as e:
        console.print(f"[red]✗ Import error:[/red] {e}")
        console.print("[yellow]Make sure all Phase 2 dependencies are installed[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Failed to start server:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def info(config_file: Path = typer.Argument(..., help="Path to agent configuration file")):
    """
    Show information about an agent configuration.
    
    Example:
        kubeagentic info examples/simple_agent.yaml
    """
    try:
        config = ConfigParser.parse_file(config_file)
        agent_def = config.agent
        
        # Create info table
        table = Table(title=f"Agent: {agent_def.name}", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Name", agent_def.name)
        table.add_row("Description", agent_def.description)
        
        # LLM info
        if agent_def.llm:
            table.add_row("LLM Provider", agent_def.llm.provider.value)
            table.add_row("LLM Model", agent_def.llm.model)
        elif agent_def.llms:
            llm_info = ", ".join([f"{llm.provider.value}/{llm.model}" for llm in agent_def.llms])
            table.add_row("LLMs (with fallback)", llm_info)
        
        table.add_row("Tools", str(len(agent_def.tools)))
        table.add_row("Memory Type", agent_def.memory.type.value)
        table.add_row("Max Messages", str(agent_def.memory.max_messages))
        table.add_row("Log Level", agent_def.logging.level.value)
        table.add_row("Max Tokens/Request", str(agent_def.limits.max_tokens_per_request))
        table.add_row("Requests/Minute", str(agent_def.limits.max_requests_per_minute))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗ Failed to read config:[/red] {e}")
        raise typer.Exit(code=1)


def main():
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main() 