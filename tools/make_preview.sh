#!/usr/bin/env bash
# Copy the part of the built site (dist/) that a pull request preview and the beta site hold into
# the folder given as the only argument.
# Part only: the whole site has about 89 thousand files and the Cloudflare Pages free plan takes
# 20,000 per deployment (.claude/rules/previews.md). It holds every top-level page and data file,
# map/, data/, components/, stats/, sources/ and the record pages of afro-asiatic/; record links into other
# families do not open in it.
set -euo pipefail
out=$1
cd "$(dirname "$0")/.."
mkdir "$out"
parts=()
for e in dist/*; do
  name=${e#dist/}
  case $name in
    map | data | components | afro-asiatic | stats | sources) parts+=("$name") ;;
    *) [ -d "$e" ] || parts+=("$name") ;;
  esac
done
tar -C dist -cf - "${parts[@]}" | tar -C "$out" -xf -
du -sh "$out"
find "$out" -type f | wc -l
