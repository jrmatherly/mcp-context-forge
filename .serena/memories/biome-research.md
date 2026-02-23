# Biome Configuration and Formatter Research

## File Locations (Local Documentation)
- Configuration reference: `/Users/jason/dev/mcp-context-forge/.scratchpad/.local_docs/biome-docs/reference/configuration.mdx`
- Formatter overview: `/Users/jason/dev/mcp-context-forge/.scratchpad/.local_docs/biome-docs/formatter/index.mdx`
- Prettier comparison: `/Users/jason/dev/mcp-context-forge/.scratchpad/.local_docs/biome-docs/formatter/differences-with-prettier.md`
- CSS linter rules: `/Users/jason/dev/mcp-context-forge/.scratchpad/.local_docs/biome-docs/linter/css/rules.mdx`
- CSS sources mapping: `/Users/jason/dev/mcp-context-forge/.scratchpad/.local_docs/biome-docs/linter/css/sources.mdx`
- Migration guide: `/Users/jason/dev/mcp-context-forge/.scratchpad/.local_docs/biome-docs/guides/migrate-eslint-prettier.mdx`
- CLI reference: `/Users/jason/dev/mcp-context-forge/.scratchpad/.local_docs/biome-docs/reference/cli.mdx`

## 1. Biome.json Configuration Structure

### Top-Level Keys
- `$schema`: JSON schema file path
- `extends`: List of paths to extend configurations (supports "//" for monorepos)
- `root`: Whether this is a root config (default: true)
- `files`: File inclusion/exclusion patterns
- `vcs`: VCS integration settings
- `linter`: Linting configuration
- `assist`: Code assist configuration
- `formatter`: Generic formatting options
- `javascript`: JavaScript/TypeScript specific options
- `json`: JSON specific options
- `css`: CSS specific options
- `graphql`: GraphQL specific options
- `grit`: Grit specific options
- `html`: HTML specific options
- `overrides`: Per-file pattern configuration overrides

### Files Configuration
```
files.includes: [glob patterns]      # Which files to process
files.ignore: [patterns]             # Files to ignore (deprecated, use includes with negation)
files.ignoreUnknown: boolean         # Suppress diagnostics for unknown file types
files.maxSize: number                # Max file size in bytes (default: 1MB = 1048576)
```

**Glob Pattern Syntax:**
- `*` matches zero or more chars (not `/`)
- `**` recursively matches all files/folders (must be entire path component)
- `[...]` character ranges
- `!` negation (in includes, can exclude files)
- `!!` force-ignore (prevents indexing, used for output dirs like dist/, build/)

**Example:**
```json
{
  "files": {
    "includes": ["src/**/*.js", "!**/*.test.js", "**/special.test.js"],
    "maxSize": 2097152
  }
}
```

## 2. Formatter Configuration (Prettier-compatible)

### Global/Language-Agnostic Options
```json
{
  "formatter": {
    "enabled": true,
    "formatWithErrors": false,
    "indentStyle": "tab",           // "tab" or "space" (default: "tab")
    "indentWidth": 2,               // spaces per indent level (default: 2)
    "lineWidth": 80,                // column width (default: 80)
    "lineEnding": "lf",             // "lf", "crlf", or "cr" (default: "lf")
    "bracketSpacing": true,         // spaces in { } (default: true)
    "expand": "auto",               // "auto", "always", or "never" (default: "auto")
    "attributePosition": "auto",    // "auto" or "multiline" (default: "auto")
    "trailingNewline": true         // trailing newline (default: true)
  }
}
```

### JavaScript/TypeScript Specific Options
```json
{
  "javascript": {
    "formatter": {
      "semicolons": "always",            // "always" or "asNeeded" (default: "always")
      "quoteStyle": "double",            // "single" or "double" (default: "double")
      "jsxQuoteStyle": "double",         // "single" or "double" (default: "double")
      "quoteProperties": "asNeeded",     // "asNeeded" or "preserve" (default: "asNeeded")
      "trailingCommas": "all",           // "all", "es5", or "none" (default: "all")
      "arrowParentheses": "always",      // "always" or "asNeeded" (default: "always")
      "bracketSameLine": false,          // JSX closing bracket on same line
      "bracketSpacing": true,
      "attributePosition": "auto",
      "expand": "auto",
      "operatorLinebreak": "after",      // "after" or "before" (default: "after")
      "indentStyle": "tab",              // override global
      "indentWidth": 2,                  // override global
      "lineWidth": 80,                   // override global
      "lineEnding": "lf"                 // override global
    }
  }
}
```

### CSS Specific Options
```json
{
  "css": {
    "formatter": {
      "enabled": false,              // CSS formatter disabled by default
      "indentStyle": "tab",
      "indentWidth": 2,
      "lineWidth": 80,
      "lineEnding": "lf",
      "quoteStyle": "double",        // "single" or "double"
      "trailingNewline": true
    }
  }
}
```

### Prettier Migration Key Differences
- **Default indentation**: Prettier uses spaces, Biome defaults to tabs
- **Semicolons**: Prettier default "always", Biome default "always" (compatible)
- **Quote style**: Prettier default double, Biome default double (compatible)
- **Trailing commas**: Prettier default "es5", Biome default "all"

### Match Prettier Settings in Biome
```json
{
  "formatter": {
    "indentStyle": "space",      // Match Prettier's spaces
    "indentWidth": 2
  },
  "javascript": {
    "formatter": {
      "semicolons": "always",
      "quoteStyle": "double",
      "trailingCommas": "es5"     // Match Prettier default
    }
  }
}
```

## 3. CSS Support

### CSS Linting Rules (Stylelint-compatible)
Biome covers 30+ CSS linter rules mapped from Stylelint:

**Correctness Rules (recommended):**
- `noInvalidDirectionInLinearGradient` (stylelint: function-linear-gradient-no-nonstandard-direction)
- `noInvalidGridAreas` (stylelint: named-grid-areas-no-invalid)
- `noUnknownProperty` (stylelint: property-no-unknown)
- `noUnknownUnit` (stylelint: unit-no-unknown)
- `noUnknownFunction` (stylelint: function-no-unknown)
- `noMissingVarFunction` (stylelint: custom-property-no-missing-var-function)
- Plus 6 more

**Suspicious Rules (recommended):**
- `noDuplicateProperties` (stylelint: declaration-block-no-duplicate-properties)
- `noDuplicateCustomProperties` (stylelint: declaration-block-no-duplicate-custom-properties)
- `noDuplicateSelectorsKeyframeBlock` (stylelint: keyframe-block-no-duplicate-selectors)
- `noEmptyBlock` (stylelint: block-no-empty)
- Plus 6 more

**Style Rules:**
- `noDescendingSpecificity` (stylelint: no-descending-specificity)
- `noValueAtRule` (stylelint: none)

**Biome Exclusive Rules:**
- `noExcessiveLinesPerFile`
- `noUselessEscapeInString`
- `noValueAtRule`

### CSS Formatter
- **Status**: Disabled by default (experimental)
- **Enable with**: `"css": { "formatter": { "enabled": true } }`
- **Supports**: Basic formatting (indentation, line width, quote style)
- **Limitations**: Not all CSS patterns supported in early versions

### CSS Parser Options
```json
{
  "css": {
    "parser": {
      "cssModules": false,           // CSS modules support
      "tailwindDirectives": false    // Tailwind @theme, @utility, @apply syntax
    }
  }
}
```

## 4. Migration Tooling

### Commands Available
```bash
biome migrate prettier [--write]    # Migrate Prettier config to Biome
biome migrate eslint [--write] [--include-inspired] [--include-nursery]
```

### Prettier Migration (`biome migrate prettier`)
- **Reads**: `.prettierrc`, `prettier.json`, `.prettierignore`
- **Creates**: `biome.json` with equivalent settings
- **Maps**: All common Prettier options to Biome equivalents
- **Supports**: JSON, JSONC formats only (not YAML, TOML, JSON5)
- **Requires**: Node.js to load `.prettierrc.js`
- **Output example**:
  - `useTabs: false` → `indentStyle: "space"`
  - `singleQuote: true` → `quoteStyle: "single"`
  - `tabWidth: 2` → `indentWidth: 2`

### ESLint Migration (`biome migrate eslint`)
- **Reads**: `.eslintrc.*`, `.eslintignore`, flat config `eslint.config.js`
- **Creates**: `biome.json` with equivalent linting rules
- **Maps**: ESLint rules to Biome equivalents using naming convention (kebab-case → camelCase)
- **Supported Plugins**: TypeScript ESLint, JSX A11y, React, Unicorn
- **Flags**:
  - `--include-inspired`: Include rules inspired by ESLint (off by default)
  - `--include-nursery`: Include experimental nursery rules
- **Limitations**: No YAML config support, doesn't migrate all options exactly
- **Note**: Plugin configurations require Node.js to load and resolve

## 5. Key Configuration Patterns

### Monorepo Setup
```json
{
  "extends": ["/"],          // Extend root config
  "root": false,             // Nested config (important!)
  "overrides": [
    {
      "includes": ["packages/*/src/**"],
      "formatter": { "indentWidth": 4 }
    }
  ]
}
```

### Overrides Pattern
```json
{
  "formatter": { "lineWidth": 100 },
  "overrides": [
    {
      "includes": ["generated/**"],
      "formatter": { "lineWidth": 160, "indentStyle": "space" }
    },
    {
      "includes": ["src/**"],
      "javascript": { "formatter": { "quoteStyle": "single" } }
    }
  ]
}
```

### Ignore Files
```json
{
  "files": {
    "includes": ["**", "!node_modules", "!!dist/**", "!!build/**"]
  }
}
```

Note: Use `!!` (force-ignore) for output directories to prevent indexing dependencies.

## 6. Known Differences from Prettier

1. **Identifier Unquoting**: Biome unquotes ES2015+ valid identifiers; Prettier only ES5
2. **Computed Keys**: Biome consistently omits parentheses in computed keys
3. **Type Parameter Trailing Commas**: Biome omits unnecessary trailing commas on arrow functions
4. **Parsing Strictness**: Biome rejects invalid syntax that Prettier tolerates (duplicate modifiers, abstract in non-abstract classes, etc.)
5. **TypeScript vs Babel Parsing**: Biome uses consistent parser; Prettier may differ between TypeScript and Babel parsers

## Default Configuration
```json
{
  "formatter": {
    "enabled": true,
    "formatWithErrors": false,
    "indentStyle": "tab",
    "indentWidth": 2,
    "lineWidth": 80,
    "lineEnding": "lf"
  },
  "javascript": {
    "formatter": {
      "arrowParentheses": "always",
      "bracketSameLine": false,
      "bracketSpacing": true,
      "jsxQuoteStyle": "double",
      "quoteProperties": "asNeeded",
      "semicolons": "always",
      "trailingCommas": "all"
    }
  },
  "json": {
    "formatter": {
      "trailingCommas": "none"
    }
  }
}
```
