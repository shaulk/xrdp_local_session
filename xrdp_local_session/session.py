import os
import sys
import pwd
import subprocess
import logging
import typer
from typing import Optional


from .common.logind import LogindClient
from .common.xrdp import SesmanClient, XRDPSession
from .config import Settings
from .consts import SYSTEM_CONFIG_FILE

class Main:
	def __init__(self, settings: Settings, username: Optional[str]=None) -> None:
		self._settings = settings
		if settings.logind_enabled is True:
			self.logind_client = LogindClient(settings)
		self.logger = logging.getLogger("xrdp_local_session.core")
		self._proc: Optional[subprocess.Popen] = None
		self._username = username
		if self._username is None:
			self._username = self._get_current_username()
		self.sesman_client = SesmanClient(self._username)

	def _get_current_username(self) -> str:
		return pwd.getpwuid(os.getuid()).pw_name

	def _launch_xrdp_local(self, socket_path: str, xrdp_session: XRDPSession, is_existing_session: bool) -> None:
		pipe_read, pipe_write = os.pipe()
		try:
			try:
				os.set_inheritable(pipe_write, True)
				os.set_inheritable(pipe_read, False)
				self._proc = subprocess.Popen(
					["xrdp_local", socket_path, str(pipe_write)],
					close_fds=False,
				)
			finally:
				os.close(pipe_write)
			# We wait for an acknowledgement so we unlock only after a successful connection to Xorg
			for line in os.fdopen(pipe_read, closefd=False):
				match line.strip():
					case "connected":
						self.logger.info("xrdp_local connected")
						if self._settings.logind_enabled is True:
							if self._settings.unlock_on_local_connection is True and is_existing_session is True:
								logind_sessions = self.logind_client.find_xrdp_sessions(os.getuid(), xrdp_session.display)
								if len(logind_sessions) == 0:
									self.logger.warning("No logind session found for existing session, will be unable to unlock it automatically.")
								for session in logind_sessions:
									self.logger.info("Unlocking logind session %s for %s", session.id, self._username)
									self.logind_client.unlock_session(session)
									self.logger.info("Logind session %s unlocked", session.id)
						return
					case _:
						self.logger.warning(f"Unknown xrdp_local output: {line}")
				raise RuntimeError("xrdp_local disconnected before successfully connecting to Xorg.")
		finally:
			os.close(pipe_read)

	def get_session(self, *, create_new_session: bool=True) -> tuple[XRDPSession, bool]:
		session = self.sesman_client.find_session_by_username(self._username)
		if session is not None:
			self.logger.info("Existing session found for %s at :%d", session.username, session.display)
			return session, True

		if create_new_session is False:
			raise KeyError("No existing session found for %s", self._username)

		self.logger.info("No existing session for %s found, launching new session", self._username)
		session = self.sesman_client.launch_new_session()
		self.logger.info("New session launched for %s at :%d", session.username, session.display)
		return session, False

	def run(self) -> tuple[int, bool]:
		xrdp_session, is_existing_session = self.get_session()
		socket_path = self.sesman_client.get_socket_path_for_session(xrdp_session)
		self._launch_xrdp_local(socket_path, xrdp_session, is_existing_session)
		if self._proc is None:
			raise RuntimeError("xrdp_local not launched")
		self.logger.info("xrdp_local launched successfully")
		if self._proc.wait() != 0:
			self.logger.warning("xrdp_local exited with non-zero status %d", self._proc.returncode)
			return self._proc.returncode, is_existing_session
		self.logger.info("xrdp_local exited with status 0")
		return 0, is_existing_session


def typer_main(
	verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
	settings_file: str = typer.Option(SYSTEM_CONFIG_FILE, "-c", "--config-file", help="Path to the global configuration file"),
) -> None:
	"""
	Run a session for xrdp_local, connecting a running xrdp session or launching
	a new one.

	You probably should not run this directly. Instead, use the xrdp-local
	session in your session manager.
	"""
	settings = Settings.load_from_file(settings_file)
	should_close_session = True
	try:
		level = logging.INFO
		if verbose is True or settings.verbose is True:
			level = logging.DEBUG
		logging.basicConfig(level=level)
		main = Main(settings)
		return_code, is_existing_session = main.run()
		if is_existing_session is False:
			# We don't close the session if we've launched it, because the
			# desktop environment will be connected to it, so if we close it
			# it will break auto-unlock on subsequent connections.
			should_close_session = False
		sys.exit(return_code)
	finally:
		if settings.logind_enabled is True and should_close_session is True:
			logging.info("Launching session closer")
			subprocess.run(["xrdp_local_session_session_closer"])


def main() -> None:
	typer.run(typer_main)

if __name__ == "__main__":
	main()
