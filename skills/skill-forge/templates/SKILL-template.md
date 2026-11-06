---
name: your-skill-name
description: >-
  One-sentence summary of what this skill enforces or automates. Use when
  [specific user intents, file types, or trigger phrases]. Don't use for
  [explicit negative boundary naming the adjacent skill to use instead].
---

# [Skill Title] (`your-skill-name`)

[1–2 sentence overview stating the expert delta this skill provides beyond base model weights.]

---

## 1. Core Workflow / Protocol

1. **Step 1 — [Name]:** [Concrete, verifiable instruction]
2. **Step 2 — [Name]:** [Concrete, verifiable instruction]
3. **Step 3 — [Name]:** [Concrete, verifiable instruction]

```bash
# Example copy-pasteable CLI invocation using <skill-dir>
python3 <skill-dir>/scripts/helper.py --input path/to/file
```

---

## 2. Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "[Excuse the agent or human uses to skip a step]" | "[Why that shortcut fails and what to do instead]" |
| "[Second common excuse]" | "[Concrete reality check]" |

---

## 3. Red Flags

- [Observable anti-pattern 1 that signals the skill is being violated]
- [Observable anti-pattern 2]
- [Observable anti-pattern 3]

---

## 4. Verification

- [ ] [Deterministic check 1 — e.g. `verify_static.py --mode skill <dir>` exits 0]
- [ ] [Deterministic check 2]
- [ ] [Artifact completeness check]
