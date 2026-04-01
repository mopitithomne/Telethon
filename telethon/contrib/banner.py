"""
ASCII startup banner for Telethon bots.

The banner is printed to stdout the first time the client successfully
connects.  Set ``client.show_banner = False`` before calling
``client.start()`` to suppress it.

You can also call :func:`print_banner` directly at any time.
"""

from .. import version as _version_mod

_BANNER = r"""
  ████████╗███████╗██╗     ███████╗████████╗██╗  ██╗ ██████╗ ███╗   ██╗
  ╚══██╔══╝██╔════╝██║     ██╔════╝╚══██╔══╝██║  ██║██╔═══██╗████╗  ██║
     ██║   █████╗  ██║     █████╗     ██║   ███████║██║   ██║██╔██╗ ██║
     ██║   ██╔══╝  ██║     ██╔══╝     ██║   ██╔══██║██║   ██║██║╚██╗██║
     ██║   ███████╗███████╗███████╗   ██║   ██║  ██║╚██████╔╝██║ ╚████║
     ╚═╝   ╚══════╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
"""

_SUBTITLE = "  Async MTProto API framework  •  Python Telegram Library"


def print_banner() -> None:
    """Print the Telethon ASCII banner with the current version to stdout."""
    try:
        ver = _version_mod.__version__
    except Exception:
        ver = "?"

    width = 70
    print(_BANNER)
    print(_SUBTITLE.center(width))
    print(f"  v{ver}".center(width))
    print()
