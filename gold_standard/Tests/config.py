import os
from glob import glob

# --- Sample sizes
ACCURACY_SAMPLE    = 20   # questions per subject for accuracy test
DISTRACTOR_SAMPLE  = 10   # questions per subject for distractor test
CONSISTENCY_SAMPLE = 10   # questions per subject for consistency test
CONSISTENCY_RUNS   = 5    # how many times to ask the same question

# --- Claude Code CLI path
CLAUDE_BIN = "/home/kokonoe/.vscode/extensions/anthropic.claude-code-2.1.126-linux-x64/resources/native-binary/claude"

# --- Paths
GOLD_DIR      = os.path.join(os.path.dirname(__file__), "..")
OUTPUT_DIR    = os.path.dirname(__file__)
SUBJECT_FILES = sorted(glob(os.path.join(GOLD_DIR, "*.json")))
