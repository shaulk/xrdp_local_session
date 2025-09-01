Name:           xrdp-local-session
Version:        0.1
Release:        1%{?dist}
Summary:        Local client for xrdp providing seamless switching between local and RDP connections - session manager

License:        Apache 2.0
URL:            https://github.com/shaulk/xrdp_local_session
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-setuptools
BuildRequires:  pyproject-rpm-macros

Requires:       python3
Requires:       python3-psutil
Requires:       sudo
Requires:       xrdp-local

BuildArch:      noarch

%global debug_package %{nil}


%description
xrdp_local_session is glue code that allows xrdp_local to be used seamlessly in a modern Linux desktop.
xrdp_local allows you to connect to local xrdp sessions without using RDP,
in effect letting you switch your xrdp session between using the local hardware
normally and connecting remotely using RDP.

%prep
%setup

%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -l xrdp_local_session
mkdir -p %{buildroot}/%{_datadir}/xsessions
cp xrdp-local-session.desktop %{buildroot}/%{_datadir}/xsessions/
mkdir -p %{buildroot}/usr/share/doc/%{name}
cp README.md %{buildroot}/usr/share/doc/%{name}/
cp COPYING %{buildroot}/usr/share/doc/%{name}/

cat %{pyproject_files}
%files -f "%{pyproject_files}"
%{_bindir}/xrdp_local_session
%{_bindir}/xrdp_local_session_session_closer
%{_datadir}/xsessions/xrdp-local-session.desktop
%{_datadir}/doc/%{name}/README.md
%{_datadir}/doc/%{name}/COPYING

%changelog
* Fri Aug 15 2025 Shaul Kremer <shaulk@users.noreply.github.com> - 0.10.4-1
- Initial package
