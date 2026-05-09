#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="image-desc-skill"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Color output ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC} $1"; }

# ─── Help ────────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
install.sh — Install $SKILL_NAME

Usage: ./install.sh [options]

Options:
  --platform NAME     Target platform (default: auto-detect)
                      Platforms: claude, cursor, copilot, windsurf, cline,
                                codex, gemini, kiro, trae, goose, opencode,
                                roo-code, universal
  --user              Install to user-level (default for claude)
  --project           Install to project-level (default for cursor, copilot)
  --all               Install to all detected platforms
  --dry-run           Show what would be done without copying
  --help, -h          Show this help message

Examples:
  ./install.sh                          # Auto-detect and install
  ./install.sh --platform cursor        # Install for Cursor
  ./install.sh --platform claude --user # Install for Claude Code
  ./install.sh --all --dry-run          # Preview all-platform install
EOF
    exit 0
}

# ─── Platform detection ──────────────────────────────────────────────────────
detect_platforms() {
    local platforms=()

    if [ -d "$HOME/.claude/skills" ]; then
        platforms+=("claude")
    fi
    if [ -d ".cursor/rules" ]; then
        platforms+=("cursor")
    fi
    if [ -d ".github/skills" ]; then
        platforms+=("copilot")
    fi
    if [ -d ".windsurf/rules" ]; then
        platforms+=("windsurf")
    fi
    if [ -d ".clinerules" ]; then
        platforms+=("cline")
    fi
    if [ -d "$HOME/.agents/skills" ]; then
        platforms+=("codex")
    fi
    if [ -d "$HOME/.gemini/skills" ]; then
        platforms+=("gemini")
    fi
    if [ -d ".kiro/skills" ]; then
        platforms+=("kiro")
    fi
    if [ -d ".trae/rules" ]; then
        platforms+=("trae")
    fi
    if [ -d "$HOME/.config/goose/skills" ]; then
        platforms+=("goose")
    fi
    if [ -d "$HOME/.config/opencode/skills" ]; then
        platforms+=("opencode")
    fi
    if [ -d ".roo/rules" ]; then
        platforms+=("roo-code")
    fi
    if [ -d "$HOME/.agents/skills" ]; then
        platforms+=("universal")
    fi

    echo "${platforms[@]}"
}

# ─── Platform install paths ──────────────────────────────────────────────────
get_install_path() {
    local platform="$1"

    case "$platform" in
        claude)     echo "$HOME/.claude/skills/$SKILL_NAME" ;;
        cursor)     echo ".cursor/rules/$SKILL_NAME" ;;
        copilot)    echo ".github/skills/$SKILL_NAME" ;;
        windsurf)   echo ".windsurf/rules/$SKILL_NAME" ;;
        cline)      echo ".clinerules/$SKILL_NAME" ;;
        codex)      echo "$HOME/.agents/skills/$SKILL_NAME" ;;
        gemini)     echo "$HOME/.gemini/skills/$SKILL_NAME" ;;
        kiro)       echo ".kiro/skills/$SKILL_NAME" ;;
        trae)       echo ".trae/rules/$SKILL_NAME" ;;
        goose)      echo "$HOME/.config/goose/skills/$SKILL_NAME" ;;
        opencode)   echo "$HOME/.config/opencode/skills/$SKILL_NAME" ;;
        roo-code)   echo ".roo/rules/$SKILL_NAME" ;;
        universal)  echo "$HOME/.agents/skills/$SKILL_NAME" ;;
        *)
            err "Unknown platform: $platform"
            return 1
            ;;
    esac
}

# ─── Install to a single platform ────────────────────────────────────────────
install_to_platform() {
    local platform="$1"
    local dest

    dest="$(get_install_path "$platform")" || return 1

    if [ "$DRY_RUN" = true ]; then
        info "[dry-run] Would install to: $dest"
        return 0
    fi

    mkdir -p "$(dirname "$dest")"

    if [ -d "$dest" ]; then
        warn "Overwriting existing installation at: $dest"
        rm -rf "$dest"
    fi

    cp -R "$SCRIPT_DIR" "$dest"
    chmod +x "$dest/install.sh" 2>/dev/null || true

    ok "Installed to: $dest"
    echo ""
    echo "  To use it, open a new session and type:"
    echo "    /$SKILL_NAME <your-request>"
    echo ""
    echo "  Examples:"
    echo "    /$SKILL_NAME Describe this image: photo.jpg"
    echo "    /$SKILL_NAME Extract text from scan.png"
    echo ""

    # Platform-specific activation notes
    case "$platform" in
        claude)
            echo "  Claude Code skills are loaded automatically."
            ;;
        cursor)
            echo "  Cursor rules require a restart to take effect."
            ;;
        copilot)
            echo "  GitHub Copilot skills are loaded automatically."
            ;;
    esac
}

# ─── Main ────────────────────────────────────────────────────────────────────
DRY_RUN=false
TARGET_PLATFORMS=()
INSTALL_MODE="auto"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --platform)
            if [ -n "${2:-}" ]; then
                TARGET_PLATFORMS+=("$2")
                INSTALL_MODE="manual"
                shift 2
            else
                err "--platform requires a value"
                exit 1
            fi
            ;;
        --user)     INSTALL_MODE="user" ;;
        --project)  INSTALL_MODE="project" ;;
        --all)      INSTALL_MODE="all" ;;
        --dry-run)  DRY_RUN=true; shift ;;
        --help|-h)  usage ;;
        *)
            err "Unknown option: $1"
            usage
            ;;
    esac
done

echo "=============================="
echo "  $SKILL_NAME Installer"
echo "=============================="
echo ""

if [ "$INSTALL_MODE" = "all" ]; then
    # Install to all known platform paths
    ALL_PLATFORMS=(
        "claude" "cursor" "copilot" "windsurf" "cline"
        "codex" "gemini" "kiro" "trae" "goose"
        "opencode" "roo-code" "universal"
    )
    for platform in "${ALL_PLATFORMS[@]}"; do
        install_to_platform "$platform"
    done

elif [ "$INSTALL_MODE" = "manual" ]; then
    for platform in "${TARGET_PLATFORMS[@]}"; do
        install_to_platform "$platform"
    done

elif [ "$INSTALL_MODE" = "auto" ]; then
    detected=($(detect_platforms))
    if [ ${#detected[@]} -eq 0 ]; then
        warn "No supported platforms detected."
        warn ""
        warn "Install manually by copying this directory to your platform's skill path:"
        warn ""
        warn "  Claude Code:    cp -R $SCRIPT_DIR \$HOME/.claude/skills/$SKILL_NAME"
        warn "  Cursor:         cp -R $SCRIPT_DIR .cursor/rules/$SKILL_NAME"
        warn "  GitHub Copilot: cp -R $SCRIPT_DIR .github/skills/$SKILL_NAME"
        warn ""
        warn "Or specify a platform: ./install.sh --platform claude"
        exit 1
    fi
    info "Detected platforms: ${detected[*]}"
    for platform in "${detected[@]}"; do
        install_to_platform "$platform"
    done
fi

echo ""
ok "Installation complete!"
echo "Open a new session and type: /$SKILL_NAME"
