import os
import fnmatch
from collections import defaultdict, Counter
from datetime import datetime

try:
    import tiktoken
except ImportError:
    tiktoken = None

# Comprehensive list of directories and files to exclude
EXCLUDES = [
    # Version control
    '.git', '.svn', '.hg', '.bzr',
    
    # OS generated files
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    
    # Python
    '__pycache__', '*.pyc', '*.pyo', '*.pyd', '.Python',
    'pip-log.txt', 'pip-delete-this-directory.txt',
    '.venv', 'venv', 'ENV', 'env', '.env',
    '.pytest_cache', '.mypy_cache', '.tox',
    'htmlcov', '.coverage', '.coverage.*',
    '*.egg-info', 'dist', 'build', 'wheels',
    '.eggs', '*.egg',
    
    # Node.js / JavaScript
    'node_modules', 'npm-debug.log*', 'yarn-debug.log*', 'yarn-error.log*',
    '.npm', '.yarn', '.pnp', '.pnp.js',
    'bower_components', 'jspm_packages',
    
    # IDE and editors
    '.idea', '.vscode', '*.swp', '*.swo', '*~',
    '.project', '.classpath', '.settings',
    '*.sublime-project', '*.sublime-workspace',
    
    # Build outputs
    'target', 'out', 'bin', 'obj',
    '*.class', '*.jar', '*.war', '*.ear',
    '*.dll', '*.exe', '*.o', '*.so', '*.dylib',
    
    # Logs and databases
    '*.log', '*.sql', '*.sqlite', '*.db',
    'logs', 'log',
    
    # Temporary files
    '*.tmp', '*.temp', '*.bak', '*.backup', '*.cache',
    '.cache', 'tmp', 'temp',
    
    # Security sensitive files
    '*.key', '*.pem', '*.p12', '*.pfx',
    '.env', '.env.*', '*.env',
    'secrets', 'credentials',
    
    # Documentation builds
    '_build', 'site', 'docs/_build',
    
    # Package manager locks (usually not needed for understanding code)
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'Pipfile.lock', 'poetry.lock', 'composer.lock',
    
    # Other
    '.sass-cache', '.next', '.nuxt', '.turbo',
    '.docusaurus', '.cache-loader',
    'vendor', 'vendors',
]

# File extensions to exclude
EXCLUDE_EXTENSIONS = [
    # Binary files
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
    '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    
    # Compiled files
    '.pyc', '.pyo', '.class', '.o', '.so', '.dll', '.exe',
    
    # Lock files
    '.lock',
    
    # Large data files
    '.csv', '.tsv', '.parquet', '.feather', '.h5', '.hdf5',
    
    # Font files
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    
    # Map files
    '.map', '.min.js.map', '.css.map',
]

# Patterns for files that might contain sensitive information
SENSITIVE_PATTERNS = [
    '*secret*', '*password*', '*token*', '*key*',
    '*.pem', '*.key', '*.cert', '*.crt',
    '.env*', '*.env',
]

GITIGNORE = '.gitignore'

def load_gitignore(root_dir):
    patterns = []
    gitignore_path = os.path.join(root_dir, GITIGNORE)
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    return patterns

def is_ignored(path, patterns):
    # Check against gitignore patterns
    for pat in patterns:
        if fnmatch.fnmatch(path, pat):
            return True
    
    # Check file extension
    _, ext = os.path.splitext(path)
    if ext.lower() in EXCLUDE_EXTENSIONS:
        return True
    
    # Check sensitive patterns
    for pat in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(path.lower(), pat.lower()):
            return True
    
    # Check if any part of the path contains excluded patterns
    path_parts = path.split(os.sep)
    for part in path_parts:
        for exclude in EXCLUDES:
            if fnmatch.fnmatch(part, exclude):
                return True
    
    return False

def count_tokens(text, encoder=None):
    if encoder:
        return len(encoder.encode(text))
    return len(text.split())

def iter_files(root_dir, patterns):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter out excluded directories
        dirnames[:] = [d for d in dirnames if not any(fnmatch.fnmatch(d, exc) for exc in EXCLUDES)]
        
        for filename in sorted(filenames):
            # Skip files matching exclude patterns
            if any(fnmatch.fnmatch(filename, exc) for exc in EXCLUDES):
                continue
                
            rel_path = os.path.relpath(os.path.join(dirpath, filename), root_dir)
            
            # Skip if ignored by any rule
            if is_ignored(rel_path, patterns):
                continue
                
            # Skip minified files
            if '.min.' in filename or filename.endswith('.min.js') or filename.endswith('.min.css'):
                continue
                
            yield rel_path

def build_dir_aggregates(file_infos):
    aggregates = defaultdict(lambda: {"files": 0, "tokens": 0, "bytes": 0})
    children = defaultdict(set)
    for info in file_infos:
        rel_path = info["path"]
        tokens = info["tokens"]
        size = info["bytes"]
        # accumulate for this file's directory and all ancestors
        dir_path = os.path.dirname(rel_path) or "."
        parts = [] if dir_path == "." else dir_path.split(os.sep)
        for i in range(len(parts) + 1):
            d = "." if i == 0 else os.sep.join(parts[:i])
            # Count file for all ancestor directories including root (represents total files under dir)
            aggregates[d]["files"] += 1
            aggregates[d]["tokens"] += tokens
            aggregates[d]["bytes"] += size
        # children map
        if dir_path != ".":
            parent = os.path.dirname(dir_path) or "."
            children[parent].add(dir_path)
        else:
            children["."].add(".")  # ensure root exists
    # ensure sets converted to sorted lists
    children = {k: sorted(v - {k}) for k, v in children.items()}
    return aggregates, children

def print_dir_tree(out, aggregates, children, current=".", prefix=""):
    # Print current directory line (skip printing for root at first call)
    if prefix == "":
        # root header printed separately by caller
        pass
    else:
        data = aggregates.get(current, {"files": 0, "tokens": 0, "bytes": 0})
        out.write(f"{prefix}{os.path.basename(current) or '.'}/ (files: {data['files']}, tokens: {data['tokens']}, bytes: {data['bytes']})\n")
    # children dirs
    dirs = sorted([d for d in children.get(current, []) if d != current])
    for idx, child in enumerate(dirs):
        is_last = idx == len(dirs) - 1
        branch = "└── " if is_last else "├── "
        next_prefix = (prefix.replace("└── ", "    ").replace("├── ", "│   ") if prefix else "") + branch
        print_dir_tree(out, aggregates, children, child, next_prefix)

def export_repo_as_text(root_dir, output_file):
    patterns = load_gitignore(root_dir)
    encoder = tiktoken.get_encoding('cl100k_base') if tiktoken else None
    tokenizer_name = 'cl100k_base' if encoder else 'words_approx'
    file_infos = []
    total_tokens = 0
    total_bytes = 0
    by_ext_tokens = Counter()
    by_ext_bytes = Counter()
    by_ext_files = Counter()
    with open(output_file, 'w', encoding='utf-8') as out:
        # Collect file infos first
        for rel_path in iter_files(root_dir, patterns):
            abs_path = os.path.join(root_dir, rel_path)
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                tokens = count_tokens(content, encoder)
                lines = content.count('\n') + (1 if content and not content.endswith('\n') else 0)
                size = os.path.getsize(abs_path)
                file_infos.append({"path": rel_path, "tokens": tokens, "lines": lines, "bytes": size, "content": content})
                total_tokens += tokens
                total_bytes += size
                ext = os.path.splitext(rel_path)[1].lower() or "<no-ext>"
                by_ext_tokens[ext] += tokens
                by_ext_bytes[ext] += size
                by_ext_files[ext] += 1
            except Exception as e:
                print(f"[skip] {rel_path}: {e}")

        # Build aggregates and tree
        aggregates, children = build_dir_aggregates(file_infos)

        # Summary
        out.write('===== REPO SUMMARY =====\n')
        out.write(f"Generated: {datetime.now().isoformat()}\n")
        out.write(f"Tokenizer: {tokenizer_name}\n")
        out.write(f"Total files: {len(file_infos)}\n")
        out.write(f"Total tokens: {total_tokens}\n")
        out.write(f"Total bytes: {total_bytes}\n")

        # Extension breakdown
        out.write('\n===== SUMMARY BY EXTENSION =====\n')
        for ext in sorted(by_ext_files.keys()):
            out.write(f"{ext}: files={by_ext_files[ext]}, tokens={by_ext_tokens[ext]}, bytes={by_ext_bytes[ext]}\n")

        # Directory tree
        out.write('\n===== DIRECTORY TREE =====\n')
        root_data = aggregates.get('.', {"files": 0, "tokens": 0, "bytes": 0})
        out.write(f"./ (files: {root_data['files']}, tokens: {root_data['tokens']}, bytes: {root_data['bytes']})\n")
        print_dir_tree(out, aggregates, children, current='.', prefix='')

        # Files
        out.write('\n===== FILES =====\n')
        for info in sorted(file_infos, key=lambda x: x["path"]):
            out.write(f"\n===== FILE: {info['path']} =====\n")
            out.write(f"[TOKENS: {info['tokens']} | LINES: {info['lines']} | BYTES: {info['bytes']}]\n")
            out.write(info['content'])
            out.write('\n')

        # Detailed summary by file
        out.write(f"\n===== SUMMARY BY FILE =====\n")
        for info in sorted(file_infos, key=lambda x: x['tokens'], reverse=True):
            out.write(f"{info['path']} : {info['tokens']} tokens, {info['lines']} lines, {info['bytes']} bytes\n")

        # Top files
        out.write(f"\n===== TOP 20 BY TOKENS =====\n")
        for info in sorted(file_infos, key=lambda x: x['tokens'], reverse=True)[:20]:
            out.write(f"{info['path']} : {info['tokens']} tokens\n")
        out.write(f"\n===== TOP 20 BY BYTES =====\n")
        for info in sorted(file_infos, key=lambda x: x['bytes'], reverse=True)[:20]:
            out.write(f"{info['path']} : {info['bytes']} bytes\n")

if __name__ == "__main__":
    export_repo_as_text(os.path.dirname(os.path.abspath(__file__)), "repo_export.txt")