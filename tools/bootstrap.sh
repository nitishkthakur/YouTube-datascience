#!/usr/bin/env bash
# One-time machine setup for rendering (macOS, Homebrew). Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Homebrew packages"
brew install cairo pango pkg-config ffmpeg espeak-ng uv 2>/dev/null || true
brew install --cask font-inter font-jetbrains-mono font-stix-two-math font-stix-two-text 2>/dev/null || true
brew install --cask inkscape kdenlive 2>/dev/null || true   # GUI tools; optional for agents

echo "== TinyTeX (per-user LaTeX)"
TT="$HOME/Library/TinyTeX/bin/universal-darwin"
if [ ! -x "$TT/xelatex" ]; then
  curl -sL "https://yihui.org/tinytex/install-bin-unix.sh" | sh
fi
export PATH="$PATH:$TT"
tlmgr install standalone preview dvisvgm cm-super doublestroke dsfont physics unicode-math \
  fontspec xetex amsmath amsfonts xcolor babel-english microtype ragged2e setspace relsize rsfs \
  >/dev/null 2>&1 || echo "   (tlmgr reported an error; xelatex itself is usually fine — run the tests)"
grep -q "TinyTeX/bin" "$HOME/.zshrc" 2>/dev/null || \
  printf '\n# TinyTeX (LaTeX for Manim)\nexport PATH="$PATH:$HOME/Library/TinyTeX/bin/universal-darwin"\n' >> "$HOME/.zshrc"

echo "== Python environment (uv)"
uv python install 3.12 >/dev/null
uv sync --extra tts

echo "== Verify"
uv run python -c "import manim, kokoro; print('manim', manim.__version__, '/ kokoro ok')"
uv run manim --version
xelatex --version | head -1
ffmpeg -version | head -1
echo "== Done. Now: uv run pytest -m 'not slow'"
