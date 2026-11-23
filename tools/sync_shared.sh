#!/bin/sh
# Copies the files every Sebayt Labs tool shares from this repo (learning-kit, the one place they're edited)
# into the sibling checkouts next to it, then shows what changed there. Commit and push each repo afterwards.
#   tools/sync_shared.sh            copy and show the changes
#   tools/sync_shared.sh --check    only report repos whose copies differ (exit 1 if any do)
set -eu
cd "$(dirname "$0")/.."
SHARED="appkit.py make_icon.py packaging/build.py .github/workflows/ci.yml"
REPOS="day-blocks drive-kit clip-pipeline transcribe-folder"
status=0
for repo in $REPOS; do
  dir="../$repo"
  [ -d "$dir/.git" ] || { echo "skip $repo (no checkout at $dir)"; continue; }
  for f in $SHARED; do
    if ! cmp -s "$f" "$dir/$f"; then
      if [ "${1:-}" = "--check" ]; then
        echo "differs: $repo/$f"; status=1
      else
        mkdir -p "$dir/$(dirname "$f")" && cp "$f" "$dir/$f" && echo "updated: $repo/$f"
      fi
    fi
  done
done
exit $status
