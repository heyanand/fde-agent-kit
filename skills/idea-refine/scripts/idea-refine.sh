#!/bin/bash
# Copyright 2026 Hemanand Rajendran
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
set -euo pipefail

# Initializes the ideas directory for the idea-refine skill.
# Usage: bash idea-refine.sh [ideas-dir]   (default: docs/ideas, relative to the current directory)
IDEAS_DIR="${1:-docs/ideas}"

if [ -e "$IDEAS_DIR" ] && [ ! -d "$IDEAS_DIR" ]; then
  echo "Error: $IDEAS_DIR exists and is not a directory" >&2
  exit 1
fi

if [ ! -d "$IDEAS_DIR" ]; then
  mkdir -p "$IDEAS_DIR"
  echo "Created directory: $IDEAS_DIR" >&2
else
  echo "Directory already exists: $IDEAS_DIR" >&2
fi

# Escape backslashes and double quotes so the JSON stays valid for any path.
ESCAPED_DIR="${IDEAS_DIR//\\/\\\\}"
ESCAPED_DIR="${ESCAPED_DIR//\"/\\\"}"
echo "{\"status\": \"ready\", \"directory\": \"$ESCAPED_DIR\"}"
