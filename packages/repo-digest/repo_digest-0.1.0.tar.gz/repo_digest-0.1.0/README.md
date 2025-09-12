# repo-digest

Turn any repository into an AI-ready text bundle with safe defaults and rich analytics.

Who is this for?
- Anyone who wants to paste a project into ChatGPT/Claude or create a quick, comprehensive repo digest.
- Works out-of-the-box on macOS, Linux, Windows.

Quickstart (60 seconds)
1) Install
   - pip install repo-digest
   - For precise token counts (optional): pip install "repo-digest[tiktoken]"

2) Export your repo
   - repo-digest . -o repo.txt

3) Preview first (optional)
   - repo-digest . -o repo.txt --preview

Safety first (defaults)
- Secrets are blocked by default (e.g., .env, *secret*, *.key, *.pem)
- Binary/large data files are excluded
- .gitignore respected by default
- To override secrets blocking (NOT recommended): --allow-secrets

Examples
- Export current repo: repo-digest . -o repo.txt
- Preview and check size: repo-digest . -o repo.txt --preview
- Enforce a size limit (bytes): repo-digest . -o repo.txt --max-bytes 5000000
- Ignore .gitignore: repo-digest . -o repo.txt --no-gitignore

Exit codes
- 0 success
- 1 runtime error (bad path, permission)
- 2 safety violation (secrets detected and not allowed)
- 3 exceeded size/limits

Troubleshooting
- Windows long paths: try running from a shorter path (e.g., C:\src)
- Encoding issues: files are read as UTF-8 with errors ignored
- Large repos: use --preview to estimate and --max-bytes to cap

FAQ
- Why are some files missing? They’re excluded by default to keep the export safe and useful. Use --no-gitignore or tweak locally if needed.
- Why token counts differ from my model? Install tiktoken for tokenizer parity; fallback uses an approximate word count.
- Can I include secrets? Not recommended. If you must: --allow-secrets (and understand the risk).

Roadmap (post-MVP)
- Markdown/JSON outputs, config file support
- GitHub URL input, chunking for huge repos
- Simple GUI if user demand is strong

License
- MIT
