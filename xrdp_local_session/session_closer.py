"""
This script is used to close the current logind session after the
xrdp_local_session exits.

The reason we need to do this explicitly is that in some environments, (e.g.
default Kubuntu), pam is configured to launch additional processes which the
desktop environment is expected to close (kwalletd in Kubuntu), and since we're
not aware of what is configured to run in any given system, we can either force
close all processes in the cgroup (assuming it's cgroups are in use), or we can
simply as logind to terminate the session, which is cleaner.

This program waits a bit and then ask logind to close its session. It's called
by xrdp_local_session just before it exits.
"""

import os
import time
import logging

import typer

from .config import Settings
from .consts import SYSTEM_CONFIG_FILE
from .common.logind import LogindClient

class SessionCloser:
	def __init__(self, logind_client: LogindClient) -> None:
		self.logind_client = logind_client
		self._logger = logging.getLogger("xrdp_local_session.session_closer")

	def close_current_session(self) -> None:
		session = self.logind_client.get_current_session()
		self._logger.info("Closing current session %s", session.id)
		self.logind_client.close_session(session)
		self._logger.info("Current session %s closed", session.id)

def typer_main(
	settings_file: str = typer.Option(SYSTEM_CONFIG_FILE, "-c", "--config-file", help="Path to the global configuration file"),
	verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose logging to stderr"),
	delay: float = typer.Option(1, "-d", "--delay", help="Delay in seconds before closing the session"),
	no_daemonize: bool = typer.Option(False, "-n", "--no-daemonize", help="Do not daemonize the process"),
) -> None:
	level = logging.INFO
	if verbose is True:
		level = logging.DEBUG
	logging.basicConfig(level=level)

	settings = Settings.load_from_file(settings_file)

	if no_daemonize is False:
		if os.fork() > 0:
			os._exit(0)

	time.sleep(delay)

	session_closer = SessionCloser(LogindClient(settings))
	session_closer.close_current_session()

def main() -> None:
	typer.run(typer_main)

if __name__ == "__main__":
	main()
