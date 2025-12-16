from __future__ import annotations

import os
import json
from typing import Optional
from pydantic import BaseModel, Field

# We don't use pydantic-settings or native Pydantic 2.0 configuration because
# some distros we support have Pydantic 1.x packaged (specifically Debian
# Bookworm, Ubuntu Jammy and Ubuntu Noble).
# TODO: Switch to Pydantic 2.0 with pydantic-settings once we drop support older
# distros.
class Settings(BaseModel):
	unlock_on_local_connection: bool = Field(default=True, description="Automatically unlock the session when a user logs in locally.")

	verbose: bool = Field(default=False, description="Verbose logging to stderr")

	logind_enabled: bool = Field(default=True, description="Enable logind support")

	# See the README for details on this workaround
	xdg_wrong_session_workaround_enabled: bool = Field(default=True, description="Enable the wrong logind session workaround")
	xdg_wrong_session_workaround_dm_allowlist: list[str] = Field(default=[
		"sddm",
		"sddm-autologin",
		"gdm",
		"lightdm",
		"lxdm",
		"lxsession",
		"lxqt-session",
	], description="List of session managers to allow when the desktop environment is connected to the wrong logind session")
	xdg_wrong_session_workaround_process_allowlist: list[str] = Field(default=[
		"xrdp_local",
		"xrdp_local_session",
		"ssh-agent",
		"sddm-helper",
		"gdm-session-worker",
	], description="List of processes to allow when the desktop environment is connected to the wrong logind session")

	local_active_marker_directory: Optional[str] = Field(default=None, description="Directory in which to keep a file marking a connection as active locally")
	local_active_marker_filename_format: str = Field(default="{username}_{x11_display}", description="Format of the active marker file name")
	local_active_marker_mandatory: bool = Field(default=False, description="Whether to require no error in creating the active marker")

	@classmethod
	def load_from_file(cls, path: str) -> Settings:
		kwargs = {}
		if os.path.exists(path):
			with open(path, "r") as f:
				kwargs = json.load(f)
		return cls(**kwargs)
