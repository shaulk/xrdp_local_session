import re
import os
import pwd
import logging
import subprocess
from pydantic import BaseModel


XRDP_SOCKET_PATHS = [
	"/run/xrdp/sockdir/{uid}/xrdp_display_{display}",
	"/run/xrdp/{uid}/xrdp_display_{display}",
]

class XRDPSession(BaseModel):
	session_id: int
	display: int
	username: str
	session_type: str


class SesmanClient:
	def __init__(self, username: str) -> None:
		self._logger = logging.getLogger("xrdp_local.sesman_client")
		self._username = username

	def get_sessions(self) -> list[XRDPSession]:
		command = ["xrdp-sesadmin", "-c=list"]
		uid = os.getuid()
		if uid != pwd.getpwnam(self._username).pw_uid:
			if uid != 0:
				raise RuntimeError("Cannot list sessions for other users unless running as root")
			command = ["sudo", "-u", self._username] + command
		result = subprocess.run(
			command,
			stdout=subprocess.PIPE,
		)
		# xrdp-sesadmin return codes are not reliable, so we parse the output anyway
		sessions = []
		session_info: dict[str, str | int] = {}
		for line_bytes in result.stdout.splitlines():
			line = line_bytes.decode("utf-8")
			if r := re.match(r"^Session ID: (\d+)$", line):
				if len(session_info) > 0:
					sessions.append(XRDPSession.validate(session_info))
				session_info = {"session_id": int(r.group(1))}
			elif r := re.match(r"^\s*Display: :(\d+)$", line):
				session_info["display"] = int(r.group(1))
			elif r := re.match(r"^\s*User: (.+)$", line):
				session_info["username"] = r.group(1)
			elif r := re.match(r"^\s*Session type: (.+)$", line):
				session_info["session_type"] = r.group(1)
		if len(session_info) > 0:
			sessions.append(XRDPSession.validate(session_info))
		self._logger.debug("Found %d sessions: %s", len(sessions), sessions)
		return sessions

	def find_session_by_username(self, username: str) -> XRDPSession | None:
		for session in self.get_sessions():
			if session.username == username:
				return session
		return None

	def find_session_by_display(self, display: int) -> XRDPSession | None:
		for session in self.get_sessions():
			if session.display == display:
				return session
		return None

	def get_socket_path_for_session(self, session: XRDPSession) -> str:
		uid = pwd.getpwnam(session.username).pw_uid
		for path in XRDP_SOCKET_PATHS:
			path = path.format(uid=uid, display=session.display)
			if os.path.exists(path):
				return path
		raise RuntimeError(f"No socket path found for session {session.session_id}")

	def launch_new_session(self) -> XRDPSession:
		self._logger.debug("Launching new session...")
		result = subprocess.run(["xrdp-sesrun"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		if result.returncode != 0:
			raise RuntimeError(f"Failed to launch new session: {result.stderr.decode('utf-8')}")
		if r := re.match(r"ok display=:(\d+) guid=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", result.stdout.decode("utf-8").strip().lower()):
			session = self.find_session_by_display(int(r.group(1)))
			if session is None:
				raise RuntimeError(f"Failed to find session by display: {r.group(1)}")
			self._logger.info("Launched new session with display: %d", session.display)
			return session
		raise RuntimeError(f"Failed to launch new session: {result.stdout.decode('utf-8')}")
