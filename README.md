# tibet-forge

**From vibe code to trusted tool.**

The Let's Encrypt of AI provenance. Automatic TIBET integration, bloat detection, duplicate checking, and trust scoring.

## The Problem

Vibe coding is loose:
- No tests
- No provenance
- Duplicate of 50 other tools
- Bloated dependencies
- Trust = 0

## The Solution

```bash
tibet-forge certify ./my-project
```

```
╔════════════════════════════════════════════════════════╗
║         Humotica Trust Score: 87/100 (B+)              ║
║         ✓ CERTIFIED                                     ║
╚════════════════════════════════════════════════════════╝

Badge markdown:
[![Humotica Trust Score](https://img.shields.io/badge/...)]
```

## Installation

```bash
pip install tibet-forge
```

## Quick Start

```bash
# Scan your project
tibet-forge scan .

# Full certification
tibet-forge certify .

# Just the score
tibet-forge score .

# See what would be wrapped
tibet-forge wrap --dry-run .
```

## What It Does

### 1. SCAN

Analyzes your code:

- **Bloat Check** - "You import `requests` but only do GET calls"
- **Duplicate Detection** - "Your RAG parser exists as `rapid-rag`"
- **Security Scan** - "Hardcoded API key detected"
- **Quality Check** - README? Tests? Docstrings?

### 2. WRAP

Auto-injects TIBET provenance:

```python
# Before
def login(user, password):
    ...

# After
@tibet_audit(action="login", erachter="User authentication")
def login(user, password):
    ...
```

### 3. CONNECT

Matches you with similar projects:

```
Similar Projects Found:
  • rapid-rag (65% similar)
    Consider using rapid-rag instead of building your own RAG
    https://pypi.org/project/rapid-rag/
```

### 4. CERTIFY

Generates trust score and badge:

```
Humotica Trust Score: 87/100 (B+)
├── Code Quality: 85/100 (weight: 25%)
├── Security: 95/100 (weight: 25%)
├── Efficiency: 80/100 (weight: 20%)
├── Uniqueness: 70/100 (weight: 15%)
└── Provenance: 100/100 (weight: 15%)

✓ CERTIFIED
```

## Trust Score Components

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| Code Quality | 25% | README, tests, docs, types |
| Security | 25% | No vulns, no hardcoded secrets |
| Efficiency | 20% | No bloat, no unused imports |
| Uniqueness | 15% | Not reinventing the wheel |
| Provenance | 15% | TIBET integration readiness |

## Configuration

Create `tibet-forge.json`:

```json
{
  "name": "my-project",
  "scan_bloat": true,
  "scan_duplicates": true,
  "scan_security": true,
  "auto_wrap": true,
  "min_score_for_badge": 70
}
```

Or in `pyproject.toml`:

```toml
[tool.tibet-forge]
scan_bloat = true
min_score_for_badge = 70
```

## The Badge

Projects scoring 70+ get the Humotica Trust badge:

[![Humotica Trust Score](https://img.shields.io/badge/Humotica_Trust_Score-87%2F100-green)](https://humotica.com/trust)

## Why "Forge"?

Like a blacksmith's forge:
- Takes raw ore (vibe code)
- Heats it up (analysis)
- Hammers it (wrapping)
- Produces strong steel (trusted tool)

## Enterprise Use

"Internal AI scripts must pass tibet-forge with 90+ to reach production."

The gamification works:
- Developers hate security
- Developers love high scores
- → Voluntary code improvement

## Links

- [tibet-core](https://github.com/Humotica/tibet-core)
- [rapid-rag](https://github.com/Humotica/rapid-rag)
- [oomllama](https://github.com/Humotica/oomllama)
- [Humotica](https://humotica.com)

## License

MIT - Humotica
