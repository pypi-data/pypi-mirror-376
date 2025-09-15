### ZPP

Fast C++ build/run, metrics, and optimization hints with a real-time terminal UI.

[CI badge](https://github.com/yourname/zpp/actions)

### Quickstart

```bash
pipx install zynpp  # or: pip install --user zynpp
zpp init
zpp main.cpp      # build + run
zpp ui main.cpp   # open two-pane UI
```

### Features
- Build/run defaults: `-std=c++17 -O2 -pipe -Wall -Wextra`
- Two-pane Textual UI: left code, right metrics and hints
- Rule-based hints (offline) + optional AI hints
- Bench and mem commands for performance
- Auto-install guidance for g++/clang++ on Linux/macOS/Windows

### CLI

- `zpp <file.cpp>`: build + run quickly
- `zpp build <file.cpp> [--release] [--debug] [--flags "..."]`
- `zpp run [binary | file.cpp] [--args "..."]`
- `zpp bench <file.cpp> [--repeat 10]`
- `zpp mem <file.cpp>`
- `zpp hint <file.cpp> [--ai]`
- `zpp ui <file.cpp>`
- `zpp doctor`
- `zpp install-gpp [--dry-run] [--yes]`
- `zpp init`
- `zpp config`
- `zpp selfcheck`

### Auto-update for clients

If installed via pipx:
```bash
pipx upgrade zynpp
```

Or use the built-in command:
```bash
zpp self-update
```

Admins can point to TestPyPI for canary:
```bash
zpp self-update --index-url https://test.pypi.org/simple/
```

### Release process

- Push to `main` publishes to TestPyPI automatically.
- Tag a release `vX.Y.Z` to publish to PyPI.

### Snippets (Hints)

Before:
```cpp
vector<int> a;
for (int i=0;i<n;i++) a.push_back(i);
```
After:
```cpp
vector<int> a;
a.reserve(n);
for (int i=0;i<n;i++) a.push_back(i);
```

Before:
```cpp
void f(std::string s);
```
After:
```cpp
void f(const std::string& s); // or std::string_view
```

Before:
```cpp
for(...) y += pow(x, 2);
```
After:
```cpp
y += x * x;
```

### Packaging

- `pyproject.toml` exposes `zpp` entrypoint
- Optional single-binary via PyInstaller

### License

MIT

