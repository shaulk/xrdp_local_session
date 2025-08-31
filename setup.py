from setuptools import setup, find_packages

setup(
    name="xrdp_local_session",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer",
        "dbus-python",
        "pydantic",
        "psutil",
    ],
    entry_points={
        "console_scripts": [
            "xrdp_local_session=xrdp_local_session.session:main",
            "xrdp_local_session_session_closer=xrdp_local_session.session_closer:main",
        ],
    },
)
