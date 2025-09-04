import re
import time
import dbus
import signal
import logging
import psutil
from typing import Optional
from pydantic import BaseModel

from ..config import Settings
from ..consts import SYSTEM_CONFIG_FILE

SERVICE_LOGIN = 'org.freedesktop.login1'
INTERFACE_DBUS_PROPERTIES = 'org.freedesktop.DBus.Properties'
INTERFACE_LOGIN_USER = 'org.freedesktop.login1.User'
INTERFACE_LOGIN_SESSION = 'org.freedesktop.login1.Session'
INTERFACE_LOGIN_MANAGER = 'org.freedesktop.login1.Manager'


class LogindSession(BaseModel):
	dbus_path: str
	service_name: str
	class_: str
	display: Optional[int]
	type: str
	leader: int

	@property
	def id(self) -> str:
		basename = self.dbus_path.rsplit('/', 1)[-1]
		if basename.startswith("c"):
			return basename
		elif basename.startswith("_3"):
			return basename[2:]
		raise ValueError(f"Invalid session basename: {basename}")


class LogindClient:
	def __init__(self, settings: Settings):
		self.bus = dbus.SystemBus()
		self.settings = settings
		self._logger = logging.getLogger("xrdp_local_session.common.logind")

	def get_sessions_for_user(self, uid: int) -> list[str]:
		proxy = self.bus.get_object(SERVICE_LOGIN, f'/org/freedesktop/login1/user/_{uid}')
		try:
			sessions = proxy.Get(INTERFACE_LOGIN_USER, "Sessions", dbus_interface=INTERFACE_DBUS_PROPERTIES)
			return [session[1] for session in sessions]
		except dbus.DBusException as e:
			if e.get_dbus_name() == 'org.freedesktop.DBus.Error.UnknownObject':
				return []
			raise

	def get_session(self, dbus_path: str) -> LogindSession:
		proxy = self.bus.get_object(SERVICE_LOGIN, dbus_path)
		try:
			display_str = proxy.Get(INTERFACE_LOGIN_SESSION, "Display", dbus_interface=INTERFACE_DBUS_PROPERTIES)
			display = None
			if r := re.match(r"^:(\d+)$", display_str):
				display = int(r.group(1))
			return LogindSession(
				dbus_path=dbus_path,
				service_name=proxy.Get(INTERFACE_LOGIN_SESSION, "Service", dbus_interface=INTERFACE_DBUS_PROPERTIES),
				class_=proxy.Get(INTERFACE_LOGIN_SESSION, "Class", dbus_interface=INTERFACE_DBUS_PROPERTIES),
				display=display,
				type=proxy.Get(INTERFACE_LOGIN_SESSION, "Type", dbus_interface=INTERFACE_DBUS_PROPERTIES),
				leader=proxy.Get(INTERFACE_LOGIN_SESSION, "Leader", dbus_interface=INTERFACE_DBUS_PROPERTIES),
			)
		except dbus.DBusException as e:
			if e.get_dbus_name() == 'org.freedesktop.DBus.Error.UnknownObject':
				raise KeyError(f"Session {dbus_path} not found")
			raise

	def get_current_session(self) -> LogindSession:
		proxy = self.bus.get_object(SERVICE_LOGIN, "/org/freedesktop/login1")
		session_path = str(proxy.GetSession("auto", dbus_interface=INTERFACE_LOGIN_MANAGER))
		return self.get_session(session_path)

	def close_session(self, session: LogindSession) -> None:
		proxy = self.bus.get_object(SERVICE_LOGIN, session.dbus_path)
		interface = dbus.Interface(proxy, INTERFACE_LOGIN_SESSION)
		interface.Kill("all", signal.SIGTERM)
		self._logger.info("Session %s closed", session.dbus_path)

	def _get_subprocess_names(self, pid: int) -> set[str]:
		try:
			process = psutil.Process(pid)
		except psutil.NoSuchProcess:
			return set()
		result = set()
		for child in process.children():
			result.add(child.name())
			result |= self._get_subprocess_names(child.pid)
		return result

	def _wrong_session_workaround_process_allowlist(self) -> set[str]:
		result = set(self.settings.xdg_wrong_session_workaround_process_allowlist)
		for item in list(result):
			if len(item) > 15:
				result.add(item[:15])
		return result

	def find_xrdp_sessions(self, uid: int, display: int) -> list[LogindSession]:
		native_sessions = []
		main_sessions = []
		for session_path in self.get_sessions_for_user(uid):
			try:
				session = self.get_session(session_path)
			except KeyError:
				continue
			self._logger.debug("Checking session %s", session)
			if session.class_ == 'user' and session.type == 'x11':
				if session.service_name == 'xrdp-sesman' and session.display == display:
					self._logger.info("Found xrdp session for display %d at %s", display, session_path)
					native_sessions.append(session)
				elif self.settings.xdg_wrong_session_workaround_enabled is True and session.service_name in self.settings.xdg_wrong_session_workaround_dm_allowlist:
					subprocess_names = self._get_subprocess_names(session.leader)
					not_allowed_processes = subprocess_names - self._wrong_session_workaround_process_allowlist()
					if len(not_allowed_processes) > 0:
						self._logger.info("Found a main session at %s but it has processes not in the allowlist, so not using it: %s", session_path, not_allowed_processes)
						continue
					self._logger.info("Found an allowed main session for display %d at %s", display, session_path)
					main_sessions.append(session)
		return native_sessions + main_sessions

	def _get_session_interface(self, session: LogindSession) -> dbus.proxies.Interface:
		proxy = self.bus.get_object(SERVICE_LOGIN, session.dbus_path)
		return dbus.Interface(proxy, INTERFACE_LOGIN_SESSION)

	def lock_session(self, session: LogindSession) -> None:
		self._get_session_interface(session).Lock()

	def unlock_session(self, session: LogindSession) -> None:
		self._logger.info("Unlocking logind session for %s", session.dbus_path)
		self._get_session_interface(session).Unlock()

if __name__ == "__main__":
	import os
	client = LogindClient(Settings.load_from_file(SYSTEM_CONFIG_FILE))
	for session in client.get_sessions_for_user(os.getuid()):
		print(client.get_session(session))
		time.sleep(1)
		client.lock_session(client.get_session(session))
		time.sleep(1)
		client.unlock_session(client.get_session(session))
