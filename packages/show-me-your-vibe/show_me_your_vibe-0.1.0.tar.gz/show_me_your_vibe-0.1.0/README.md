# ✨ `vibe` — generate structured LLM context from your codebase in one command

Instead of manually opening files, copy-pasting their contents one by one, adding markdown formating,
describing every file, and stitching them into a prompt, `vibe` does it for you in a single command.
`vibe` collects files from a given directory, processes their contents, and forms a structured markdown context.

By default, the generated context is copied directly into your clipboard, so you can simply **Ctrl+V it into your LLM prompt** without any extra steps.
It respects git and considers `.gitignore` file.

## Usage

Run `vibe path/to/codedir/you/wanna/discuss/with/AI` and the full structured description of all files and folders will be ready in your clipboard;)

![demo](/demo/screencast.gif)

The help reference:

```
$ vibe --help
                                                                                
 Usage: vibe [OPTIONS] [PATH]                                                   
                                                                                
 Form LLM context from a specified directory or file.                           
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   path      [PATH]  Path to dir/file you want to make the context from.      │
│                     [default: /home/sky/Github/vibe]                         │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --print               -P        Print the context instead of copying it to   │
│                                 the clipboard.                               │
│ --version             -V        Show version and exit.                       │
│ --install-completion            Install completion for the current shell.    │
│ --show-completion               Show completion for the current shell, to    │
│                                 copy it or customize the installation.       │
│ --help                          Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Installation

Just `pip install show-me-your-vibe`.

For **MacOS** and **Windows** it will work right out of the box.

For **Linux** (for accessing your clipboard) install a support lib accrding to the table below:

<table>
  <thead>
    <tr>
      <th>Display Server</th>
      <th>Family / Distribution</th>
      <th>Command</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="8" align="center"><b>Wayland</b></br>(Commonly default)</td>
      <td>Ubuntu | Debian | Linux Mint | Pop!_OS | KDE Neon | elementary</td>
      <td><code>sudo apt install wl-clipboard</code></td>
    </tr>
    <tr>
      <td>Fedora | RHEL | CentOS | Rocky | AlmaLinux | Oracle Linux</td>
      <td><code>sudo dnf install wl-clipboard</code></td>
    </tr>
    <tr>
      <td>Arch | Manjaro | EndeavourOS | Garuda</td>
      <td><code>sudo pacman -S --needed wl-clipboard</code></td>
    </tr>
    <tr>
      <td>openSUSE Leap | Tumbleweed | SLES</td>
      <td><code>sudo zypper install wl-clipboard</code></td>
    </tr>
    <tr>
      <td>Alpine</td>
      <td><code>sudo apk add wl-clipboard</code></td>
    </tr>
    <tr>
      <td>Void</td>
      <td><code>sudo xbps-install -S wl-clipboard</code></td>
    </tr>
    <tr>
      <td>Gentoo</td>
      <td><code>sudo emerge wl-clipboard</code></td>
    </tr>
    <tr>
      <td>NixOS | Nix</td>
      <td><code>nix-env -iA nixpkgs.wl-clipboard</code></td>
    </tr>
    <tr>
      <td rowspan="8" align="center"><b>X11</b></td>
      <td>Ubuntu | Debian | Linux Mint | Pop!_OS | KDE Neon | elementary</td>
      <td><code>sudo apt install xclip</code> or <code>sudo apt install xsel</code></td>
    </tr>
    <tr>
      <td>Fedora | RHEL | CentOS | Rocky | AlmaLinux | Oracle Linux</td>
      <td><code>sudo dnf install xclip</code> or <code>sudo dnf install xsel</code></td>
    </tr>
    <tr>
      <td>Arch | Manjaro | EndeavourOS | Garuda</td>
      <td><code>sudo pacman -S --needed xclip</code> or <code>sudo pacman -S --needed xsel</code></td>
    </tr>
    <tr>
      <td>openSUSE Leap | Tumbleweed | SLES</td>
      <td><code>sudo zypper install xclip</code> or <code>sudo zypper install xsel</code></td>
    </tr>
    <tr>
      <td>Alpine</td>
      <td><code>sudo apk add xclip</code> or <code>sudo apk add xsel</code></td>
    </tr>
    <tr>
      <td>Void</td>
      <td><code>sudo xbps-install -S xclip</code> or <code>sudo xbps-install -S xsel</code></td>
    </tr>
    <tr>
      <td>Gentoo</td>
      <td><code>sudo emerge xclip</code> or <code>sudo emerge xsel</code></td>
    </tr>
    <tr>
      <td>NixOS | Nix</td>
      <td><code>nix-env -iA nixpkgs.xclip</code> or <code>nix-env -iA nixpkgs.xsel</code></td>
    </tr>
    <tr>
      <td align="center"><b>No GUI</b></td>
      <td></td>
      <td>No system clipboard available - use <code>xvfb</code>, or write to file, or just print.</td>
    </tr>
  </tbody>
</table>
