# tibet-forge

**Zero-friction provenance. Built-in trust.**

Turn any Python project into a certified, auditable tool with one command. Cryptographic provenance baked in, not bolted on.

## Quick Start

```bash
pip install tibet-forge

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

## What You Get

### Trust Scoring
Gamified quality metrics. See exactly where your code stands:

```
Humotica Trust Score: 87/100 (B+)
├── Code Quality: 85/100 (weight: 25%)
├── Security: 95/100 (weight: 25%)
├── Efficiency: 80/100 (weight: 20%)
├── Uniqueness: 70/100 (weight: 15%)
└── Provenance: 100/100 (weight: 15%)
```

### Zero-Friction Provenance
TIBET audit trails injected automatically. Every function call tracked, every decision logged:

```python
# Your code stays clean
def login(user, password):
    ...

# tibet-forge adds provenance invisibly
@tibet_audit(action="login", erachter="User authentication")
def login(user, password):
    ...
```

### Hyper-Optimized Execution
Bloat detection powered by AST analysis. Know exactly what's slowing you down:

```
Efficiency Analysis:
  ✓ No heavy dependencies detected
  • Consider: httpx instead of requests (3x faster, async-native)
  • Unused import: 'os' in utils.py
```

### Smart Deduplication
Intent hashing finds existing tools that do what you're building:

```
Similar Projects Found:
  • rapid-rag (65% similar)
    Production-ready RAG with TIBET integration
    https://pypi.org/project/rapid-rag/
```

## Commands

```bash
# Full certification with badge
tibet-forge certify .

# Quick scan
tibet-forge scan .

# Just the score
tibet-forge score .

# Preview TIBET injection
tibet-forge wrap --dry-run .

# Initialize config
tibet-forge init
```

## Trust Score Components

| Component | Weight | Measures |
|-----------|--------|----------|
| Code Quality | 25% | README, tests, docs, types |
| Security | 25% | No vulns, no hardcoded secrets |
| Efficiency | 20% | No bloat, minimal dependencies |
| Uniqueness | 15% | Novel contribution, not reinventing |
| Provenance | 15% | TIBET integration, audit readiness |

## The Badge

Projects scoring 70+ earn the Humotica Trust badge:

[![Humotica Trust Score](https://img.shields.io/badge/Humotica_Trust-87%2F100-brightgreen)](https://humotica.com/trust)

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

## Why "Forge"?

Raw code goes in. Trusted tool comes out.

Like a blacksmith's forge - heat, hammer, harden. Your vibe code becomes production steel.

## Part of the Humotica Suite

| Package | Focus |
|---------|-------|
| [tibet-core](https://pypi.org/project/tibet-core/) | Provenance foundation |
| [rapid-rag](https://pypi.org/project/rapid-rag/) | RAG in 3 lines |
| [oomllama](https://pypi.org/project/oomllama/) | Smart LLM routing |
| **tibet-forge** | Zero-friction certification |

## License

MIT - Humotica
