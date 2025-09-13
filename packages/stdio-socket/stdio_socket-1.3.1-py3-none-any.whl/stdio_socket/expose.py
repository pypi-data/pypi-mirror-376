"""Interface for ``python -m stdio_socket``."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Annotated

import typer

from . import __version__
from .version import version_callback

__all__ = ["expose"]


def expose(
    command: Annotated[str, typer.Argument(help="Command to run and expose stdio")],
    socket: Annotated[
        Path, typer.Option(help="The filepath to the socket to use")
    ] = Path("/tmp/stdio.sock"),
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            help="print the version number and exit",
        ),
    ] = None,
    ptty: Annotated[bool, typer.Option(help="enable psuedo tty")] = False,
    stdin: Annotated[bool, typer.Option(help="enable stdin on main process")] = False,
    ctrl_d: Annotated[bool, typer.Option(help="enable Ctrl-D")] = False,
):
    """
    Expose the stdio of a process on a socket at unix:///tmp/stdio.sock.

    This allows a local process to connect to stdio of the running process.
    Use Ctrl+C to disconnect from the socket.

    The following command will connect to the socket and provide interactive
    access to the process:
        socat UNIX-CONNECT:/tmp/stdio.sock -,raw,echo=0
    or use the built in client:
        console
    """
    asyncio.run(_expose_stdio_async(command, socket, ptty, stdin, ctrl_d))


async def _expose_stdio_async(
    command: str, socket_path: Path, ptty: bool, stdin: bool, ctrl_d: bool
):
    os.system("stty -echo raw")

    # force line buffering
    command = f"stdbuf -oL -eL {command}"

    if ptty:
        # these stty settings and psuedo-tty make bash and vim work
        command = f'pptty "{command}"'

    # a list of currently connected clients
    clients: list[asyncio.StreamWriter] = []

    # Start the process and pass the current environment variables
    process = await asyncio.create_subprocess_shell(
        command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=os.environ,
    )

    sys.stderr.write(f"Process started with PID {process.pid}\n")

    async def do_stdin(reader: asyncio.StreamReader, allow_break: bool = False):
        """read stdin from a stream and forward to the process stdin"""
        assert process.stdin is not None  # for typechecker

        while True:
            char: bytes = await reader.read(1)
            if char == b"\x04" and not ctrl_d:  # Ctrl-D
                sys.stderr.write("Ctrl-D received, NOT exiting...\n")
                continue
            if not char or char == b"\x03" and allow_break:  # Ctrl-C
                break
            else:
                process.stdin.write(char)
                await process.stdin.drain()

    async def do_stdout():
        """Forward process stdout/stderr to sys.stdout and connected clients"""
        assert process.stdout is not None  # for typechecker

        while True:
            block = await process.stdout.read(2048)
            if not block:
                break
            block = block.replace(b"\n", b"\r\n")
            sys.stdout.buffer.write(block)
            sys.stdout.flush()
            for writer in clients:
                # insert a carriage return before newlines
                writer.write(block)
                await writer.drain()

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection."""

        try:
            sys.stderr.write("Client connected.\r\n")
            clients.append(writer)
            await asyncio.gather(do_stdin(reader, allow_break=True))
        finally:
            sys.stderr.write("Client disconnected.\r\n")
            clients.remove(writer)
            writer.close()
            await writer.wait_closed()

    async def monitor_system_stdin():
        """Forward system stdin to the process stdin."""

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        await do_stdin(reader)

    try:
        msg = f"\r\n>> launching {command} using stdio-socket v{__version__} <<\r\n"
        sys.stderr.write(msg)

        # Start forwarding stdout and stderr to sys.stdout and connected clients
        asyncio.create_task(do_stdout())

        # Start monitoring system stdin and forward it to the process
        if stdin:
            asyncio.create_task(monitor_system_stdin())

        # Create a Unix domain socket server, calling handle_client for each connection
        server = await asyncio.start_unix_server(handle_client, path=str(socket_path))
        sys.stderr.write(f"\r\nSocket created at {socket_path}.\r\n")
        asyncio.create_task(server.serve_forever())

        """Monitor the process and exit when it terminates."""
        await process.wait()
        sys.stderr.write("\r\nProcess exited. Cleaning up...\r\n")
        server.close()

    finally:
        # restore terminal to normal state
        os.system("stty sane cooked")

        # Clean up the socket and subprocess
        if socket_path.exists():
            socket_path.unlink()
        sys.stderr.write("\n\rSocket closed.\n")
