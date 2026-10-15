#!/bin/sh
# Adds "Characterization" to the application menu and puts a launcher on the
# desktop; both start the program in this folder. Run it again after moving
# the folder somewhere else.
set -e
dir="$(cd "$(dirname "$0")" && pwd)"
exe="$dir/Characterization"
if [ ! -x "$exe" ]; then
    echo "Characterization was not found next to this file."
    echo "Download Characterization-VERSION-linux-x86_64.tar.gz from the GitHub"
    echo "Releases page (not \"Source code\"), extract it and run this file there."
    exit 1
fi

icon="$dir/_internal/static/icon.svg"
apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$apps"
entry="$apps/characterization.desktop"
cat > "$entry" <<EOF
[Desktop Entry]
Type=Application
Name=Characterization
Comment=Characterization data for synthetic organic chemistry
Exec="$exe"
Path=$dir
Icon=$icon
Terminal=false
Categories=Science;Chemistry;Education;
EOF
chmod +x "$entry"

desktop="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
if [ -d "$desktop" ]; then
    cp "$entry" "$desktop/characterization.desktop"
    chmod +x "$desktop/characterization.desktop"
    # GNOME: mark the launcher as trusted so it starts on double-click
    gio set "$desktop/characterization.desktop" metadata::trusted true 2>/dev/null || true
fi
echo "Characterization is now in your application menu (and on the desktop)."
