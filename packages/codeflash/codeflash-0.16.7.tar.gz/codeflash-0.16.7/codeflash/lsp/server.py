from __future__ import annotations

import sys
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any, Optional, TextIO

from lsprotocol.types import INITIALIZE, LogMessageParams, MessageType
from pygls import uris
from pygls.protocol import LanguageServerProtocol, lsp_method
from pygls.server import LanguageServer, StdOutTransportAdapter, aio_readline

if TYPE_CHECKING:
    from lsprotocol.types import InitializeParams, InitializeResult

    from codeflash.optimization.optimizer import Optimizer


class CodeflashLanguageServerProtocol(LanguageServerProtocol):
    _server: CodeflashLanguageServer

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        server = self._server
        initialize_result: InitializeResult = super().lsp_initialize(params)

        workspace_uri = params.root_uri
        if workspace_uri:
            workspace_path = uris.to_fs_path(workspace_uri)
            pyproject_toml_path = self._find_pyproject_toml(workspace_path)
            if pyproject_toml_path:
                server.prepare_optimizer_arguments(pyproject_toml_path)
            else:
                server.show_message("No pyproject.toml found in workspace.")
        else:
            server.show_message("No workspace URI provided.")

        return initialize_result

    def _find_pyproject_toml(self, workspace_path: str) -> Path | None:
        workspace_path_obj = Path(workspace_path)
        for file_path in workspace_path_obj.rglob("pyproject.toml"):
            return file_path.resolve()
        return None


class CodeflashLanguageServer(LanguageServer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.optimizer: Optimizer | None = None
        self.args_processed_before: bool = False
        self.args = None

    def prepare_optimizer_arguments(self, config_file: Path) -> None:
        from codeflash.cli_cmds.cli import parse_args

        args = parse_args()
        args.config_file = config_file
        args.no_pr = True  # LSP server should not create PRs
        args.worktree = True
        self.args = args
        # avoid initializing the optimizer during initialization, because it can cause an error if the api key is invalid

    def show_message_log(self, message: str, message_type: str) -> None:
        """Send a log message to the client's output channel.

        Args:
            message: The message to log
            message_type: String type - "Info", "Warning", "Error", or "Log"

        """
        # Convert string message type to LSP MessageType enum
        type_mapping = {
            "Info": MessageType.Info,
            "Warning": MessageType.Warning,
            "Error": MessageType.Error,
            "Log": MessageType.Log,
            "Debug": MessageType.Debug,
        }

        lsp_message_type = type_mapping.get(message_type, MessageType.Info)

        # Send log message to client (appears in output channel)
        log_params = LogMessageParams(type=lsp_message_type, message=message)
        self.lsp.notify("window/logMessage", log_params)

    def cleanup_the_optimizer(self) -> None:
        try:
            self.optimizer.cleanup_temporary_paths()
            # restore args and test cfg
            if self.optimizer.original_args_and_test_cfg:
                self.optimizer.args, self.optimizer.test_cfg = self.optimizer.original_args_and_test_cfg
            self.optimizer.args.function = None
            self.optimizer.current_worktree = None
            self.optimizer.current_function_optimizer = None
        except Exception:
            self.show_message_log("Failed to cleanup optimizer", "Error")

    def start_io(self, stdin: Optional[TextIO] = None, stdout: Optional[TextIO] = None) -> None:
        self.show_message_log("Starting IO server", "Info")

        self._stop_event = Event()
        transport = StdOutTransportAdapter(stdin or sys.stdin.buffer, stdout or sys.stdout.buffer)
        self.lsp.connection_made(transport)
        try:
            self.loop.run_until_complete(
                aio_readline(
                    self.loop,
                    self.thread_pool_executor,
                    self._stop_event,
                    stdin or sys.stdin.buffer,
                    self.lsp.data_received,
                )
            )
        except BrokenPipeError:
            self.show_message_log("Connection to the client is lost! Shutting down the server.", "Error")
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            self.cleanup_the_optimizer()
            self.shutdown()
