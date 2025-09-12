---
layout: page
title: CLI Reference
permalink: /docs/cli-reference/
---

The MDL command-line interface provides tools for building and managing Minecraft datapacks.

## Installation

Install MDL using pipx:

```bash
pipx install minecraft-datapack-language
```

## Basic Commands

### Build Command

Build MDL files into Minecraft datapacks. Defaults: `--mdl .` and `-o dist`.

```bash
# Simplest
mdl build

# Explicit
mdl build --mdl <path> -o <output_dir>
# Zips by default -> creates <output_dir>.zip
# Use --no-zip to skip archive creation
```

**Examples:**
```bash
# Build single file (output defaults to dist)
mdl build --mdl hello.mdl

# Build entire directory (both default)
mdl build

# Build with custom output
mdl build --mdl myproject/ -o out
```

**Options:**
- `--mdl <path>`: Path to a single `.mdl` file or a directory to build (default: `.`)
- `-o <output_dir>`: Output directory for compiled datapack (default: `dist`)
- `--verbose`: Show detailed build information
- `--wrapper <name>`: Custom wrapper name for the datapack

### Check Command

Validate MDL files for syntax and semantic errors. If no paths are given, it scans the current directory for `**/*.mdl`.

```bash
# Simplest
mdl check

# Explicit
mdl check <files_or_directories>
```

**Examples:**
```bash
# Check single file
mdl check hello.mdl

# Check current directory (implicit)
mdl check

# Check a specific directory
mdl check myproject/

# Check with warnings suppressed
mdl check myproject/ --ignore-warnings
```

**Output and Error Reporting:**
The check command provides comprehensive error reporting with:
- Exact file location (line, column)
- Context lines showing the problematic code
- Helpful suggestions for fixing issues
- Multiple error collection (reports all errors, not just the first)

**Example Error Output:**
```
Error 1: MDLSyntaxError in test.mdl:15:8
Missing closing brace for if statement
Context:
  13:   if $score<@s>$ > 10 {
  14:     say "High score!"
  15:     score<@s> = 0
  16:   }

Suggestion: Add closing brace '}' after line 15

Error 2: MDLLexerError in test.mdl:22:12
Unterminated string literal
Context:
  20:   say "Hello world
  21:   score<@s> = 10
  22:   say "Goodbye

Suggestion: Add closing quote '"' at the end of line 20
```

### New Command

Create a new MDL project with template files:

```bash
mdl new <project_name>
```

**Examples:**
```bash
# Create a new project in current directory
mdl new my_awesome_pack

# Create a project with specific name
mdl new adventure_map

# Create a project in a subdirectory
mdl new projects/survival_plus
```

**What it creates (by default):**
The new command generates a project structure with:
- `README.md` - Quick start with build instructions
- `main.mdl` - Hello world (pack, namespace, simple function, on_load)
- `docs/` - A literal copy of the MDL documentation for offline/local browsing
- `serve_docs.sh` and `serve_docs.ps1` - Convenience scripts to serve docs locally

**Generated project structure (default):**
```
my_awesome_pack/
├── README.md
├── main.mdl
├── docs/
│   ├── index.md
│   ├── _config.yml
│   └── ...
├── serve_docs.sh
└── serve_docs.ps1
```

**Template content includes:**
- Pack metadata (name, description, format)
- Namespace declaration
- One function that says hello
- on_load hook

## Command Options

### Build Options

| Option | Description | Example |
|--------|-------------|---------|
| `--mdl <path>` | .mdl file or directory to build (default: `.`) | `--mdl .` |
| `-o <dir>` | Output directory (default: `dist`) | `-o dist` |
| `--verbose` | Show detailed output | `--verbose` |
| `--wrapper <name>` | Custom wrapper name | `--wrapper mypack` |
| `--no-zip` | Skip creating zip archive (zip is default) | `--no-zip` |
| `--ignore-warnings` | Suppress warning messages | `--ignore-warnings` |

### Check Options

| Option | Description | Example |
|--------|-------------|---------|
| `--verbose` | Show detailed validation information | `--verbose` |
| `--ignore-warnings` | Suppress warning messages | `--ignore-warnings` |

### New Options

| Option | Description | Example |
|--------|-------------|---------|
| `<project_name>` | Name of the new project to create | `mdl new my_pack` |
| `--pack-name <name>` | Override datapack name used in `pack.mcmeta` | `--pack-name Adventure` |
| `--pack-format <num>` | Pack format number (defaults to modern value) | `--pack-format 82` |
| `--output <dir>` | Directory to create the project in | `--output ./projects` |
| `--exclude-local-docs` | Do not copy the MDL docs into `docs/` | `--exclude-local-docs` |

By default, `mdl new` includes a full `docs/` folder in your project so new users have local docs offline. Use `--exclude-local-docs` to skip this step.

Serve the docs quickly with the generated scripts:

```bash
# Bash/Git Bash
./serve_docs.sh

# PowerShell
./serve_docs.ps1
```

Both scripts prefer Jekyll (if `bundle` and a `Gemfile` are present), otherwise they fall back to a simple Python web server.

You can open the docs site in your browser via the CLI:

```bash
mdl docs            # opens Getting Started in your default browser
mdl docs open       # same as above
mdl docs serve --dir docs --port 8000   # optional: serve local docs (if you prefer)
```

When running `mdl new`, the output will list all generated files:

```
my_awesome_pack/
├── README.md
├── main.mdl
├── docs/
├── docs_site/          # present when packaged HTML is available
├── serve_docs.sh
└── serve_docs.ps1
```

## Completion Command

Install shell autocompletion so you can type `mdl bui<Tab>` and get `build`:

```bash
mdl completion install           # auto-detects your shell
mdl completion install bash      # explicit shell
mdl completion uninstall zsh     # remove
mdl completion print fish        # print script for manual use/CI
mdl completion doctor            # basic diagnostics
```

Supported shells: Bash (incl. Git Bash), Zsh, Fish, and PowerShell.

## Error Handling

MDL provides comprehensive error handling and reporting:

### Error Types

- **MDLSyntaxError**: Basic syntax violations (missing semicolons, braces)
- **MDLLexerError**: Token recognition issues (unterminated strings, invalid characters)
- **MDLParserError**: Parsing and structure problems (malformed statements)
- **MDLValidationError**: Semantic validation failures (undefined variables, invalid references)
- **MDLFileError**: File access and I/O issues
- **MDLBuildError**: Build process failures
- **MDLCompilationError**: Compilation and linking issues
- **MDLConfigurationError**: CLI configuration and argument errors

### Error Features

- **Exact Location**: Errors include precise line and column numbers
- **Context Lines**: Shows surrounding code for better debugging
- **Helpful Suggestions**: Provides specific fix recommendations
- **Multiple Error Collection**: Reports all errors, not just the first one
- **Error Summaries**: Shows total error and warning counts
- **Verbose Mode**: Detailed error information with additional context
- **Warning Suppression**: Use `--ignore-warnings` to hide warning messages and show only errors

### Example Error Output

```
🔍 Checking test.mdl...

Error 1: MDLSyntaxError in test.mdl:15:8
Missing closing brace for if statement
Context:
  13:   if "$score<@s>$ > 10" {
  14:     say "High score!"
  15:     score<@s> = 0
  16:   }

Suggestion: Add closing brace '}' after line 15

Error 2: MDLLexerError in test.mdl:22:12
Unterminated string literal
Context:
  20:   say "Hello world
  21:   score<@s> = 10
  22:   say "Goodbye

Suggestion: Add closing quote '"' at the end of line 20

Error 3: MDLValidationError in test.mdl:8:5
Undefined variable 'player_score'
Context:
   6:   score<@s> = 10
   7:   lives<@s> = 3
   8:   player_score<@s> = 5
   9:   say "Score: $score<@s>$"

Suggestion: Declare the variable first with 'variable player_score = 0'

Summary: 3 errors found
```
| `--verbose` | Show detailed output | `--verbose` |

## Examples

### Basic Workflow

1. **Create a new project:**
```bash
mdl new hello_world
```

2. **Check the generated file:**
```bash
mdl check hello_world/main.mdl
```

3. **Build the datapack:**
```bash
mdl build --mdl hello_world/main.mdl
```

4. **Install in Minecraft:**
- Copy `dist/hello_world/` to your world's `datapacks/` folder
- Run `/reload` in-game

**Alternative: Manual file creation**
If you prefer to create files manually, you can start with:
```mdl
// hello.mdl
pack "hello" "My first datapack" 82;
namespace "hello";

function hello:main {
    say "Hello, Minecraft!";
}

on_load hello:main<@s>;
```

2. **Check the file:**
```bash
mdl check hello.mdl
```

3. **Build the datapack:**
```bash
mdl build --mdl hello.mdl
```

4. **Install in Minecraft:**
- Copy `dist/hello/` to your world's `datapacks/` folder
- Run `/reload` in-game

### Multi-File Project

**Project structure:**
```
my_project/
├── main.mdl
├── ui.mdl
└── game.mdl
```

**Build command:**
```bash
mdl build
```

### Explicit Scopes in Conditions

MDL supports explicit scope selectors in if/while conditions, allowing you to override declared variable scopes:

```mdl
// Variables with different scopes
var num playerScore<@s> = 0;                    // Defaults to @s
var num globalCounter<@a> = 0;                  // Global scope
var num teamScore<@a[team=red]> = 0;            // Team scope

function hello:main {
    // Use explicit scope in conditions
    if $playerScore<@s>$ > 10 {
        say "Current player score is high!";
    }
    
    if $globalCounter<@a>$ > 100 {
        say "Global counter reached milestone!";
    }
    
    if $teamScore<@a[team=red]>$ > 50 {
        say "Red team is winning!";
    }
    
    // Check another player's score
    if $playerScore<@p[name=Steve]>$ > 5 {
        say "Steve has a good score!";
    }
}
```

**Benefits:**
- **Override declared scopes**: Use different scopes than what was declared
- **Check other entities**: Compare scores across different players/teams
- **Flexible conditions**: Mix and match scopes as needed
- **Clear intent**: Explicit scope makes code more readable

### Verbose Build

Get detailed information about the build process:

```bash
mdl build --mdl hello.mdl --verbose
```

Output includes:
- Files being processed
- Functions being generated
- Variables being initialized
- Any warnings or errors
 - Per-file status lines in the form `[OK] <file>` when a file is parsed successfully

## Error Handling

### Common Errors

**"No .mdl files found"**
```bash
# Make sure you're in the right directory
ls *.mdl

# Use explicit file paths
mdl build --mdl ./myfile.mdl

# or build the directory itself
mdl build
```

**"Failed to parse MDL files"**
```bash
# Check syntax
mdl check myfile.mdl

# Look for missing semicolons, brackets, etc.
```

**"Duplicate function name"**
```bash
# Check for duplicate function names in the same namespace
mdl check myproject/
```

### Debugging

Use verbose mode to get more information:

```bash
mdl build --mdl myfile.mdl --verbose
mdl check myfile.mdl --verbose
```

## Output Structure

The build command creates a datapack with this structure:

```
dist/
└── pack_name/
    ├── pack.mcmeta
    └── data/
        └── namespace/
            ├── function/
            │   ├── main.mcfunction
            │   └── other.mcfunction
            └── tags/
                └── function/
                    ├── load.json
                    └── tick.json
```

## Integration

### With Build Tools

**Makefile example:**
```makefile
.PHONY: build clean

build:
	mdl build

clean:
	rm -rf dist/

check:
	mdl check .
```

**npm scripts example:**
```json
{
  "scripts": {
    "build": "mdl build",
    "check": "mdl check .",
    "clean": "rm -rf dist/"
  }
}
```

### With CI/CD

**GitHub Actions example:**
```yaml
name: Build Datapack
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install minecraft-datapack-language
      - run: mdl check .
      - run: mdl build
      - run: mdl check .
```
