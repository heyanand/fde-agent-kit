---
name: google-oss
description: >-
  Prepares and audits repositories for Google Open Source release
  compliance: full 13-line Apache-2.0 license headers across languages, root
  LICENSE/CONTRIBUTING/SECURITY templates, internal path/shortlink sanitization,
  and pre-release hygiene gates. Use when open-sourcing code, publishing
  developer samples, or auditing a public GitHub repository. Don't use for
  strictly internal corp-only docs that will never be exported to GitHub.
---

# Google Open Source Publishing & Sanitization Standard (`google-oss`)

Enforces Google Open Source release hygiene ([opensource.google/documentation](https://opensource.google/documentation)) across public GitHub repositories, customer reference architectures, and DevRel sample code.

---

## 1. Mandatory Root Repository Files

Every open-source repository must include at its root:
1. **`LICENSE`:** Full Apache-2.0 license text (202 lines).
2. **`CONTRIBUTING.md`:** Copy from [templates/CONTRIBUTING.md](templates/CONTRIBUTING.md) (links to `https://cla.developers.google.com/` and `https://opensource.google/conduct/`).
3. **`SECURITY.md`:** Copy from [templates/SECURITY.md](templates/SECURITY.md) (directs vulnerability disclosures to `https://g.co/vulnz`).
4. **`README.md`:** Project overview, prerequisites, quick start commands, and support disclaimer.

---

## 2. Complete 13-Line Apache-2.0 License Headers

Every source code file (`.py`, `.sh`, `.tf`, `.go`, `.ts`, `.js`, `.java`, `.rs`) must begin with the complete 13-line Apache-2.0 boilerplate (including the `WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND` clause — never truncate after `Unless required by applicable law`).

### Python / Shell / Terraform / YAML (`#` Comments)
```python
# Copyright 2026 Google LLC
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
```
*(Note: For personal open-source projects not owned by Google LLC, replace `Copyright 2026 Google LLC` with `Copyright 2026 <Author Name>`).*

### Go / TypeScript / JavaScript / Java / C++ (`//` Comments)
```ts
// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
```

### HTML / XML / Markdown Templates (`<!-- -->` Comments)
```html
<!--
 Copyright 2026 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->
```

---

## 3. Pre-Release Sanitization Gate (Zero Internal Leaks)

Before pushing any commit to a public GitHub remote, run the sanitization scan across all tracked files (excluding this skill documentation file, wherever it is vendored):

```bash
# Must return 0 matches (exit code 1 from git grep means clean / no matches found)
git grep -nI -iE "(google3|/google/src|g4d|citc|blaze|moma|buganizer|jetski|googlers\.com|\bb/[0-9]{6,}|\bcl/[0-9]{6,}|\bgo/[a-z0-9-]+)" \
  -- . ':(exclude,glob)**/google-oss/SKILL.md'
```
Also scan for leaked personal hostnames and usernames specific to your environment (e.g. `git grep -nI -i "$USER"`), and treat every match as a blocker until it is removed or replaced with a public URL.

### Rules for Dual On-Corp / Off-Corp Repositories
- **Never hardcode internal filesystem mounts** in tracked manifests or Python scripts.
- Store corp-only mount paths in a gitignored local override file (`skills.manifest.local.json`) accompanied by a sanitized `skills.manifest.local.example.json` template using generic `/path/to/corp/mount` placeholders.
- Replace internal shortlinks with public documentation URLs (`https://cloud.google.com/...` or `https://google.github.io/adk-docs/`).

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "A 4-line shortened Apache header is good enough" | Automated open-source compliance scanners (`addlicense` / `license-eye`) reject truncated headers missing the warranty disclaimer. |
| "I'll keep the internal path in `skills.manifest.json` since it's just a string" | Internal depot paths reveal internal directory structures and fail open-source release audits. Move them to a gitignored `.local.json`. |
| "I'll add `CONTRIBUTING.md` and `SECURITY.md` after v1.0 launches" | Public repositories require CLA and vulnerability reporting instructions before accepting external traffic or PRs. |

## Red Flags

- Source files missing the 13-line Apache-2.0 header or using a truncated 7-line header
- Missing root `LICENSE`, `CONTRIBUTING.md`, or `SECURITY.md`
- Any match from the `git grep` internal-identifier sanitization scan in tracked files
- Hardcoded internal project IDs, LDAP usernames, or `.c.googlers.com` hostnames in tracked code

## Verification

- [ ] Root `LICENSE` (Apache-2.0) is present and complete
- [ ] All source files contain the full 13-line Apache-2.0 header
- [ ] The `git grep` sanitization scan returns 0 matches across all tracked files
- [ ] `git diff --staged -i -G'(password|secret|api_key|token|PRIVATE KEY)' --name-only` returns empty
