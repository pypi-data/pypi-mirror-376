from importlib.metadata import version
import os
from pathlib import Path
import platform
import subprocess

import pyperclip
import typer

from .form_context import form_str_context
from .ir import make_ir

app = typer.Typer()


def _pkg_cmd() -> tuple[str, str, str]:  # pylint: disable=too-many-return-statements
    """
    Return (install_cmd, family, os_id) from /etc/os-release.
    families: apt | dnf | pacman | zypper | apk | xbps | emerge | nix
    """
    os_id = "unknown"
    os_like = ""

    txt = subprocess.check_output(
        ["bash", "-lc", "source /etc/os-release 2>/dev/null; echo ${ID:-unknown}; echo ${ID_LIKE:-}"],
        text=True,
    )
    parts = [p.strip() for p in txt.splitlines()]

    if parts:
        os_id = parts[0].strip().strip('"')

    if len(parts) > 1:
        os_like = parts[1].strip().strip('"')

    def fam(*names):
        return os_id in names or any(n in os_like.split() for n in names)

    if fam("ubuntu", "debian", "linuxmint", "pop", "neon", "elementary"):
        return ("sudo apt install", "apt", os_id)
    if fam("fedora", "rhel", "centos", "rocky", "almalinux", "ol"):
        return ("sudo dnf install", "dnf", os_id)
    if fam("arch", "manjaro", "endeavouros", "garuda"):
        return ("sudo pacman -S --needed", "pacman", os_id)
    if fam("opensuse-leap", "opensuse-tumbleweed", "sles", "opensuse"):
        return ("sudo zypper install", "zypper", os_id)
    if fam("alpine"):
        return ("sudo apk add", "apk", os_id)
    if fam("void"):
        return ("sudo xbps-install -S", "xbps", os_id)
    if fam("gentoo"):
        return ("sudo emerge", "emerge", os_id)
    if fam("nixos", "nix"):
        return ("nix-env -iA", "nix", os_id)
    return ("sudo apt install", "apt", os_id)


def clipboard_fix_hint() -> str:
    """Print a one-liner fix hint based on OS/env."""
    sysname = platform.system()
    wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
    x11 = bool(os.environ.get("DISPLAY"))

    if sysname == "Darwin":
        pre = "For MacOS with tmux install reattach-to-user-namespace: `"
        cmd = "brew install reattach-to-user-namespace"
        typer.secho(pre, fg=typer.colors.WHITE, nl=False, err=True)
        typer.secho(cmd, fg=typer.colors.YELLOW, nl=False, err=True)
        typer.secho("`.", fg=typer.colors.WHITE, err=True)
        return

    if sysname in ("Linux", "FreeBSD"):
        cmd, family, os_id = _pkg_cmd()

        if wayland:
            if family == "nix":
                pre = f"For Wayland on {os_id.capitalize()} install nixpkgs.wl-clipboard: `"
                full_cmd = f"{cmd} nixpkgs.wl-clipboard"
            else:
                pre = f"For Wayland on {os_id.capitalize()} install wl-clipboard: `"
                full_cmd = f"{cmd} wl-clipboard"
            typer.secho(pre, fg=typer.colors.WHITE, nl=False, err=True)
            typer.secho(full_cmd, fg=typer.colors.YELLOW, nl=False, err=True)
            typer.secho("`.", fg=typer.colors.WHITE, err=True)
            return

        if x11:
            if family == "nix":
                pre = f"For X11 on {os_id.capitalize()} install nixpkgs.xclip or nixpkgs.xsel: `"
                cmd1 = f"{cmd} nixpkgs.xclip"
                cmd2 = f"{cmd} nixpkgs.xsel"
            else:
                pre = f"For X11 on {os_id.capitalize()} install xclip or xsel: `"
                cmd1 = f"{cmd} xclip"
                cmd2 = f"{cmd} xsel"
            typer.secho(pre, fg=typer.colors.WHITE, nl=False, err=True)
            typer.secho(cmd1, fg=typer.colors.YELLOW, nl=False, err=True)
            typer.secho("` / `", fg=typer.colors.WHITE, nl=False, err=True)
            typer.secho(cmd2, fg=typer.colors.YELLOW, nl=False, err=True)
            typer.secho("`.", fg=typer.colors.WHITE, err=True)
            return

        msg = f"Linux ({os_id.capitalize()}, no GUI): no system clipboard; use `xvfb` or write to file or just print."
        typer.secho(msg, fg=typer.colors.WHITE, err=True)
        return

    msg = "Unknown OS: If you use Wayland, then install 'wl-clipboard', if you use X11, then install 'xclip'/'xsel'."
    typer.secho(msg, fg=typer.colors.WHITE, err=True)


def copy(text: str):
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException:
        typer.secho("Failed to copy text to clipboard. Error: Clipboard access failed.", err=True, fg=typer.colors.RED)
        clipboard_fix_hint()


def version_callback(value: bool):
    if value:
        typer.echo(f"vibe (show-me-your-vibe), {version('show-me-your-vibe')}")
        raise typer.Exit()


@app.command()
def main(
    path: Path = typer.Argument(
        default=Path.cwd(),
        exists=True,
        file_okay=True,
        dir_okay=True,
        help="Path to dir/file you want to make the context from.",
    ),
    print_context: bool = typer.Option(
        False,
        "--print",
        "-P",
        help="Print the context instead of copying it to the clipboard.",
    ),
    _: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    )
):
    """Form LLM context from a specified directory or file."""
    ir = make_ir(path, consider_git=True)
    context = form_str_context(ir)
    if print_context:
        typer.echo(context)
    else:
        copy(context)


if __name__ == "__main__":
    app()
