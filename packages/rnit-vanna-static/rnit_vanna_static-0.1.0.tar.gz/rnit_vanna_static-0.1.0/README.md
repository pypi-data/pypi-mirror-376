# RNIT Vanna Static

A static snapshot of the Vanna SQL generation library. This package contains a frozen copy of Vanna code for specific use cases.

## ⚠️ Important Note

**For most users, we recommend using the main `rnit-vanna` package instead:**
```bash
pip install rnit-vanna  # Recommended - always uses latest Vanna
```

This static version is only for:
- Testing with a specific Vanna version
- Offline environments with dependency conflicts
- Educational purposes to understand Vanna internals

## Installation

```bash
pip install rnit-vanna-static
```

## Why Two Packages?

- **`rnit-vanna`** (Recommended): A wrapper that always uses the latest official Vanna
- **`rnit-vanna-static`** (This package): A frozen snapshot of Vanna code

## Usage

This package works exactly like the original Vanna:

```python
from rnit_vanna.openai import OpenAI_Chat
from rnit_vanna.chromadb import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn = MyVanna(config={'api_key': 'your-openai-key', 'model': 'gpt-4o-mini'})
```

## Limitations

- **No automatic updates** - Frozen at a specific Vanna version
- **May become outdated** - Missing new features and bug fixes
- **Larger package size** - Contains copied code

## License

MIT - Based on the original Vanna library