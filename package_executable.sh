#!/bin/sh

# Build with PyInstaller
pyinstaller run.py --noconfirm --icon="data/resources/icon.ico" --name xeupiu

# Copy data files
mkdir -p dist/xeupiu/data
mkdir -p dist/xeupiu/data/tmp
mkdir -p dist/xeupiu/data/log
cp -r data/characters dist/xeupiu/data/characters
cp -r data/backgrounds dist/xeupiu/data/backgrounds
cp -r data/resources dist/xeupiu/data/resources
cp -r data/texts dist/xeupiu/data/texts
cp config_generic.json dist/xeupiu/config.json

# Build AppImage
build_appimage() {
    # Get version from pyproject.toml
    version=$(grep '^version' pyproject.toml | cut -d'"' -f2)
    if [ -z "$version" ]; then
        version="dev"
    fi
    
    local appdir="dist/AppDir"
    
    # Clean/create AppDir
    rm -rf "$appdir"
    mkdir -p "$appdir/usr/bin"
    mkdir -p "$appdir/usr/share/applications"
    mkdir -p "$appdir/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$appdir/usr/share/xeupiu"
    
    # Copy binary
    cp "dist/xeupiu/xeupiu" "$appdir/usr/bin/"
    
    # Copy data files
    cp -r data "$appdir/usr/share/xeupiu/"
    cp config_generic.json "$appdir/usr/share/xeupiu/"
    
    # Create .desktop file for AppImage
    cat > "$appdir/usr/share/applications/xeupiu.desktop" <<EOF
[Desktop Entry]
Name=XEUPIU
Exec=xeupiu
Icon=xeupiu
Type=Application
Categories=Game;
Terminal=false
X-AppImage-Version=$version
EOF
    
    # Copy icon
    cp data/resources/logo.png "$appdir/usr/share/icons/hicolor/256x256/apps/xeupiu.png"
    
    # Create AppRun entry point
    cat > "$appdir/AppRun" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")/usr/bin"
exec ./xeupiu "$@"
EOF
    chmod +x "$appdir/AppRun"
    
    # Download appimagetool if needed
    local tool="appimagetool-x86_64.AppImage"
    if [ ! -f "$tool" ]; then
        echo "Downloading appimagetool..."
        wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/$tool" || {
            echo "Failed to download appimagetool"
            return 1
        }
        chmod +x "$tool"
    fi
    
    # Build AppImage
    ARCH=x86_64 "./$tool" "$appdir" "XEUPIU-${version}-x86_64.AppImage" && {
        echo "AppImage created: XEUPIU-${version}-x86_64.AppImage"
    } || {
        echo "Failed to create AppImage"
        return 1
    }
}

build_appimage
