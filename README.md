# xrdp_local_session

xrdp_local_session is glue code that allows
[xrdp_local](https://github.com/shaulk/xrdp_local) to be used seamlessly in a
modern Linux desktop.

It's basically a small Python program that acts as an X11 session manager (like
`gnome-session` or `plasma-session`), and uses
[xrdp_local](https://github.com/shaulk/xrdp_local) to join a new or existing
[xrdp](https://github.com/neutrinolabs/xrdp) session.

When properly installed, it lets you seamlessly switch your session between your
local hardware and a remote RDP session, locking your local machine when a
remote client connects.

To provide a better RDP experience, `xrdp_local_session` can also unlock the
session when you reconnect locally.

This provides a seamless RDP experience almost on par with the modern Windows
RDP server, despite the limitations of X11.

## How it works
The full ecosystem consists of several components:
  - A local X11 display manager like [SDDM](https://github.com/sddm/sddm) or
    [LightDM](https://github.com/canonical/lightdm).
  - A local X11 server connected to real hardware. 
  - An X11 server running [xorgxrdp](https://github.com/neutrinolabs/xorgxrdp)
    instead of regular real hardware drivers.
  - [xrdp](https://github.com/neutrinolabs/xrdp) listening for RDP connections.  
(up to here it's just a regular X11-based Linux desktop setup with xrdp
installed)
  - An `xrdp_local_session` xsession entry that runs `xrdp_local_session`
    instead of a regular desktop.
  - [xrdp_local](https://github.com/shaulk/xrdp_local), which connects locally
    to the xrdp X11 server, showing it in the local machine.

Basically, you have two X11 servers running:
  - One running your actual desktop session within an `xrdp` context, not
    connected to any physical hardware, instead accepting connections from
    either `xrdp_local`, or `xrdp`.
  - One running `xrdp_local`, showing the desktop on the other X11 server,
    connected to real hardware.

When `xrdp` connects to its X11 server (because a user logs in through RDP),
`xrdp_local` is disconnected and exits, which switches the physical hardware
back to the login screen. When a local user signs back in, the RDP session
closes and the session is switched back to the local X11 server.

### Login flow
When the user logs in graphically (using a regular X11 display manager like
SDDM) and picks the xrdp_local_session session, the following happens:
  - A new local-only X11 session is started, launching xrdp_local_session as its
    main process.
  - xrdp_local_session checks if an existing xrdp session is running using
    xrdp-sesadmin. If one isn't one running, it uses xrdp-sesrun to start one.
  - xrdp_local_session then runs xrdp_local to join the xrdp session, displaying
    the output on the local X11 server.
  - If there was an RDP client connected,
    [xorgxrdp](https://github.com/neutrinolabs/xorgxrdp) will automatically
    disconnect it when xrdp_local connects.
  - If [configured to do so](#configuration) and it's an existing session,
    xrdp_local_session also unlocks the xrdp session (so you don't have to type
    your password twice).

### RDP connection flow
When the user connects to an `xrdp` session using an RDP client, the following
happens:
  - `xrdp` authenticates the user, forking and connecting to `xorgxrdp` (which
    runs the actual desktop session).
  - `xorgxrdp` disconnects any existing clients, that is, `xrdp_local`.
  - `xrdp_local` exits, and the display manager switches to the login screen.

## Installation
### Installing using your distribution's package manager
#### Debian, Ubuntu and other Debian-based distributions
Get the sources list for your distribution from our
[repositories page](https://xrdp-local.github.io/repos/) and put it at
`/etc/apt/sources.list.d/xrdp_local.list`.

Then, run:
```
apt update
apt install xrdp_local_session
```

#### Fedora and other Red Hat-based distributions
Get the sources list for your distribution from our
[repositories page](https://xrdp-local.github.io/repos/) and put it at
`/etc/yum.repos.d/xrdp_local.repo`. Also grab the
[GPG signing key](https://xrdp-local.github.io/repos/GPG-KEY-xrdp-local) and
put it at `/etc/pki/rpm-gpg/GPG-KEY-xrdp-local`.

Then, run:
```
dnf install xrdp_local_session
```

### Installing manually from packages
Grab the latest release from the releases page for both
[xrdp_local_session](https://github.com/shaulk/xrdp_local_session/releases) and
[xrdp_local](https://github.com/shaulk/xrdp_local/releases). Also get our
patched versions of xrdp and xorgxrdp from the
[xrdp_local_deps releases page](https://github.com/shaulk/xrdp_local_deps/releases).

### Installation from source
`xrdp_local_session` is a regular Python program, so you can install it with
pip. As root, run:
```
pip install xrdp_local_session
```
Then, copy the `xrdp_local_session.desktop` file to
`/usr/share/xsessions/xrdp_local_session.desktop`.

See also
[how to install xrdp_local](https://github.com/shaulk/xrdp_local#installing).

## Configuration
`xrdp_local_session` can be configured with a JSON file at
`/etc/xrdp_local_session.json`.

The following options are available:
  - `verbose`: Whether to enable verbose logging everywhere.
  - `unlock_on_local_connection`: Whether to unlock the session when a local
    user logs in.
  - `logind_enabled`: Whether to enable logind support. This is required for
    auto-unlocking the session when a local user logs in.
  - `xdg_wrong_session_workaround_enabled`: Whether to enable the workaround for
    the systemd-logind app.slice bug. This is enabled by default, but you might
    want to disable it if you're not using KDE Plasma. See [The systemd-logind
    app.slice bug](#the-systemd-logind-appslice-bug) for more details.
  - `xdg_wrong_session_workaround_dm_allowlist`: A list of display managers to
    allow when the desktop environment is connected to the wrong logind session.
    This should be the value returned by `loginctl show-session <session-id>`,
    under the `Service` attribute.
  - `xdg_wrong_session_workaround_process_allowlist`: A list of processes to
    allow when the desktop environment is connected to the wrong logind session.
    This is to make sure we don't accidentally unlock an unrelated session. In
    general, other than `xrdp_local` itself, it should only contain processes
    that are started implicitly by the system even outside a standard desktop
    environment.

### Changing the default desktop session
#### Arch Linux
On Arch Linux, selecting the default xrdp desktop session is done using
[xinit](https://wiki.archlinux.org/title/Xinit). For example, to use KDE Plasma,
you can create a file at `/etc/X11/xinit/xinitrc` or `~/.xinitrc` with the
following contents:
```
exec startplasma-x11
```
#### Debian, Ubuntu and other Debian-based distributions
In Debian-based distributions, the default desktop session is set using
[Debian's alternatives system](https://wiki.debian.org/DebianAlternatives).
To change the default desktop session, you can run:
```
update-alternatives --config x-session-manager
```

If you want to set a per-user default desktop session, you can configure
[Xsession](https://manpages.debian.org/trixie/x11-common/Xsession.5.en.html) by
creating a `.Xsession` file in the user's home directory.

#### Fedora and other Red Hat-based distributions
You can set the default desktop session by creating a file at
`/etc/sysconfig/desktop`, with the name of the desktop session you want to use.
For example, to use KDE Plasma, use:
```
DESKTOP="KDE"
```

## Desktop environment support
In general, any desktop environment that supports X11 properly should work.
That said, some environments have wrong assumptions or bugs that make using
xrdp_local_session awkward or buggy.

### KDE Plasma
KDE Plasma works fine and is fully supported. The only caveat is that you need
to make sure the workaround for the systemd-logind app.slice bug is enabled
(which it is by default) to auto-unlock the session, see
[The systemd-logind app.slice bug](#the-systemd-logind-appslice-bug) for more
details.

### GNOME
Modern GNOME has several issues which mean screen locking, and potentially
everything, is broken:
  - Screen locking doesn't work when GNOME is not launched by GDM. Since it's
    being launched by xrdp-sesman, screen locking is disabled, and clicking the
    screen lock button in the UI just switches the local display to the login
    screen VT (even when you're connected using RDP), but a user can just press
    CTRL-ALT-Fx to switch back. If you connect using RDP, the local
    xrdp_local will exit, which will effectively lock the session.
  - In recent versions of GNOME, when its locking implementation is combined
    with the [systemd-logind app.slice bug](#the-systemd-logind-appslice-bug),
    when you login initially locally (that is, using xrdp_local), GNOME will
    connect to the wrong session, and after you reconnect, the session will not
    accept any input because it won't get the dbus signal saying that the
    session was unlocked. This effectively makes the session unusable, and
    breaks the functionality provided by xrdp_local completely, unless you log
    in using RDP initially (which disables locking completely, so it is a
    workaround for this behavior).
  - Recent versions of GDM (which is used by default on most GNOME systems)
    assume there will only be just one session for any user at any given time,
    and will actually enforce it by not letting you login again once a session
    is active. The workaround is to use a different display manager, like
    [SDDM](https://github.com/sddm/sddm) or
    [LightDM](https://github.com/canonical/lightdm), which disables screen
    locking on GNOME.
  - The [systemd-logind app.slice bug](#the-systemd-logind-appslice-bug) also
    makes some applications (e.g. gnome-terminal) fail to launch sometimes after
    reconnecting if the original session is destroyed in the system dbus bus.

Some issues start with version 43, others in later versions.

If you don't need screen locking and you're ok with not using GDM, GNOME
__usually__ works fine as long as you login using RDP initially.

### XFCE
XFCE works fine by default with no workarounds.

### LXQt
LXQt uses XScreenSaver to handle the lock screen, which doesn't support the
logind dbus interface, so auto-unlock doesn't work. XScreenSaver also doesn't
handle screen resizing at all, so if you connect from a machine with a much
lower display resolution than where the screen saver was launched on, the screen
locker UI might be cut until the system is unlocked. Otherwise, LXQt works fine.
 
## The systemd-logind app.slice bug
In systemd-logind managed systems, each session runs in a cgroup
under `/user.slice/user-<uid>.slice/session-<sid>.slice`. In modern systemd
(since 247), systemd allows separating cgroups per-application, and each
application runs in its own cgroup under
`/user.slice/user-<uid>/user@<uid>.service/app.scope`.
Systemd assumes logind sessions are in their own cgroup, which breaks detecting
which session a process belongs to if there is more than one (see
cg_path_get_session() in systemd). Some modern desktops environments that are
integrated with systemd (like GNOME and KDE Plasma) launch every application and
even themselves under app.slice.

Since a system using xrdp_local_session initiates two sessions at the same time
(one by the display manager running xrdp_local_session, the other by xrdp-sesman
running the actual desktop session), programs that ask systemd which session
they belong to (using its dbus interface, at
org.freedesktop.login1.Manager.GetSession) will get the wrong session. For most
applications, this is meaningless, but both GNOME and KDE Plasma use this to
respond to lock screen requests. In GNOME, this completely breaks the lock screen
(making it unable to unlock once it's active), and in KDE Plasma, it breaks
unlocking the session automatically using dbus.

### The xrdp_local_session workarounds for auto-unlocking
For KDE Plasma, xrdp_local_session implements a workaround that sends unlock
requests to the wrong session too, which works. Since this is a hack, it's
surrounded by several checks to make sure it's not unlocking an unrelated
session, but if you're paranoid you might want to disable it anyway, and just
type your password twice. See [Configuration](#configuration) for more details.
