import os
import logging
from typing import Optional, Type
from types import TracebackType
from .config import Settings
from .common.xrdp import XRDPSession

class ActiveMarker:
	def __init__(self, settings: Settings, session: XRDPSession) -> None:
		self._settings = settings
		self._session = session
		self._logger = logging.getLogger("xrdp_local_session.active_marker")

	@property
	def _filename(self) -> str:
		return self._settings.local_active_marker_filename_format.format(
			username=self._session.username,
			x11_display=self._session.display,
			logind_session_id=self._session.session_id,
			uid=os.getuid(),
		)

	def _set(self) -> None:
		if self._settings.local_active_marker_directory is None:
			return

		full_path = os.path.join(self._settings.local_active_marker_directory, self._filename)
		try:
			fd = os.open(full_path, os.O_CREAT | os.O_WRONLY, 0o600)
			os.close(fd)
		except Exception as e:
			self._logger.warning("Failed to create active marker file %s: %s", full_path, e)
			if self._settings.local_active_marker_mandatory is True:
				raise

	def _unset(self) -> None:
		if self._settings.local_active_marker_directory is None:
			return

		full_path = os.path.join(self._settings.local_active_marker_directory, self._filename)
		if os.path.exists(full_path):
			os.unlink(full_path)

	def __enter__(self) -> None:
		self._set()

	def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
		self._unset()
