#!/usr/bin/env bash
# Records demo/out/demo.{mp4,gif}: rebuilds the demo directory, runs vhs, then stops the
# programs vhs started whether or not it succeeded. Needs vhs, ttyd, ffmpeg and a signed-in
# Claude Code; every run spends Claude tokens.
set -u
cd "$(dirname "$0")/.."

cleanup() {
  pkill -x ttyd 2>/dev/null
  pkill -f "\.cache/rod/browser" 2>/dev/null
}
trap cleanup EXIT

# Run from inside a Claude Code session, the demo session would inherit that session's
# markers and show a "Transcript saving is off" warning.
for name in $(compgen -e | grep -E '^(CLAUDECODE|CLAUDE_CODE_|CLAUDE_PID)'); do unset "$name"; done

demo/setup.sh
mkdir -p demo/out
timeout "${RECORD_TIMEOUT:-1500}" vhs demo/demo.tape || exit $?

# One palette for the whole clip keeps the text crisp; 10 fps is enough for a terminal.
ffmpeg -loglevel error -y -i demo/out/demo.mp4 \
  -vf "fps=10,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=none" \
  demo/out/demo.gif
