"""
Entry point for running agentlin modules as executables.

Usage:
    ```sh
    python -m agentlin.tools.server.bash_mcp_server --port 9999
    agentlin mcp-server --name bash --port 9999
    agentlin code-interpreter-server --port 8889 --debug
    agentlin agent-server --port 8000
    agentlin task-server --port 8001
    agentlin sgl-server --port 8002
    ```
"""

from typing import Dict, Any
import os
import sys
import enum
import importlib

import typer
import uvicorn
from fastmcp import FastMCP
from loguru import logger

from agentlin.evaluation.__main__ import app as eval_app


app = typer.Typer()
app.add_typer(eval_app, name="eval", help="Run Evaluations")


class McpServerModule:
    """MCP 服务器模块的类型注释类"""
    mcp: FastMCP


class MCPServer(enum.Enum):
    bash = "bash"
    file_system = "file_system"
    memory = "memory"
    web = "web"
    todo = "todo"
    aime = "aime"
    wencai = "wencai"

    def __str__(self):
        return self.name


example_usage = "\n\n".join([f"agentlin mcp_server --name {mcp_server.name} --port 7779 --debug" for mcp_server in MCPServer])


@app.command(
    help=f"""Run the specified MCP server.\n\nExamples:\n\n{example_usage}""",
)
def mcp_server(
    name: MCPServer = typer.Option(
        MCPServer.bash,
        "--name",
        help="The name of the MCP server to run.",
        case_sensitive=False,
    ),
    host: str = typer.Option("0.0.0.0", help="The host to bind the server to"),
    port: int = typer.Option(7779, help="The port to run the server on"),
    path: str = typer.Option("/mcp", help="The path for the MCP server"),
    home: str = typer.Option(None, help="The target directory for file operations (if applicable)"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    """
    Launch an MCP server.
    """
    selected_server = name
    server_name = selected_server.name
    server_path = f"agentlin.tools.server.{server_name}_mcp_server"
    server_module: McpServerModule = importlib.import_module(server_path)
    mcp = server_module.mcp

    if selected_server == MCPServer.file_system:
        if home:
            server_module.TARGET_DIRECTORY = home
        else:
            typer.echo("For file_system server, please specify --home to set the target directory.")
            raise typer.Exit(code=1)

    typer.echo(f"Starting {server_name} MCP server on {host}:{port} at path {path} with debug={debug}")
    # Run the selected MCP server
    mcp.run("http", host=host, port=port, path=path, log_level="debug" if debug else "info")


@app.command(
    help="Run the code interpreter server",
)
def code_interpreter_server(
    host: str = typer.Option("0.0.0.0", help="The host to bind the code interpreter server to"),
    port: int = typer.Option(8889, help="The port to run the code interpreter server on"),
    debug: bool = typer.Option(False, help="Enable debug mode for the code interpreter server"),
    env_file: str = typer.Option(".env", help="Path to the .env file for environment variables"),
    log_dir: str = typer.Option("logs/code_interpreter", help="Directory to store logs"),
):
    """
    Run the code interpreter server with the specified host and port.
    """
    typer.echo(f"Starting code interpreter server on {host}:{port}")
    if env_file:
        from dotenv import load_dotenv

        load_dotenv(env_file)
        logger.info(f"Loading environment variables from {env_file}")

    from agentlin.tools.server.code_interpreter_server import app, init_server

    init_server(app, log_dir, debug)

    typer.echo(f"Running Code Interpreter Server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info" if not debug else "debug")


@app.command(
    help="Run the agent server",
)
def agent_server(
    host: str = typer.Option("0.0.0.0", help="The host to bind the agent server to"),
    port: int = typer.Option(9999, help="The port to run the agent server on"),
    debug: bool = typer.Option(False, help="Enable debug mode for the agent server"),
    env_file: str = typer.Option(".env", help="Path to the .env file for environment variables"),
    workers: int = typer.Option(1, help="The number of workers to run the agent server on"),
):
    """
    Run the agent server with the specified host and port.
    """
    typer.echo(f"Starting agent server on {host}:{port}")
    if env_file:
        from dotenv import load_dotenv

        load_dotenv(env_file)
        logger.info(f"Loading environment variables from {env_file}")

    if workers > 1:
        uvicorn.run("agentlin.route.server:app", host=host, port=port, log_level="info" if not debug else "debug", workers=workers)
    else:
        from agentlin.route.server import app

        if debug:
            logger.info("Debug mode is enabled.")
            app.debug = True

        typer.echo(f"Running Agent Server at http://{host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info" if not debug else "debug")


@app.command(
    help="Run the task server",
)
def task_server(
    host: str = typer.Option("0.0.0.0", help="The host to bind the task server to"),
    port: int = typer.Option(9999, help="The port to run the task server on"),
    debug: bool = typer.Option(False, help="Enable debug mode for the task server"),
    env_file: str = typer.Option(".env", help="Path to the .env file for environment variables"),
):
    """
    Run the task server with the specified host and port.
    """
    typer.echo(f"Starting task server on {host}:{port}")
    if env_file:
        from dotenv import load_dotenv

        load_dotenv(env_file)
        logger.info(f"Loading environment variables from {env_file}")

    from agentlin.rollout.task_server import app
    import multiprocessing
    multiprocessing.set_start_method(method="fork", force=True)

    if debug:
        logger.info("Debug mode is enabled.")
        app.debug = True

    typer.echo(f"Running Agent Server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info" if not debug else "debug")


@app.command(
    help="Run the sgl server",
)
def sgl_server(
    host: str = typer.Option("0.0.0.0", help="The host to bind the sgl server to"),
    port: int = typer.Option(9999, help="The port to run the sgl server on"),
    env_file: str = typer.Option(".env", help="Path to the .env file for environment variables"),
):
    """
    Run the sgl server with the specified host and port.
    """
    typer.echo(f"Starting sgl server on {host}:{port}")
    if env_file:
        from dotenv import load_dotenv

        load_dotenv(env_file)
        logger.info(f"Loading environment variables from {env_file}")


    from agentlin.rollout.sgl_server import app

    from sglang.srt.utils import kill_process_tree
    from sglang.srt.server_args import prepare_server_args
    from sglang.srt.entrypoints.http_server import launch_server
    server_args = prepare_server_args(sys.argv[1:])

    try:
        typer.echo(f"Running SGL Server at http://{host}:{port}")
        launch_server(server_args)
    finally:
        kill_process_tree(os.getpid(), include_parent=False)



if __name__ == "__main__":
    app()
