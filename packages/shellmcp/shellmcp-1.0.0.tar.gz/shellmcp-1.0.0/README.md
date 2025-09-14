# ShellMCP

**Expose Shell Commands as MCP Tools**

ShellMCP is a powerful tool that allows you to easily create Model Context Protocol (MCP) servers by exposing shell commands as structured tools. Instead of granting AI agents full shell access (which poses security risks), ShellMCP enables you to expose only the specific commands you trust, allowing agents to work autonomously with a predefined set of safe operations.

Define your tools in YAML, and ShellMCP generates a complete FastMCP server for you.

## Quick Start

```bash
# Install ShellMCP
pip install shellmcp

# Create a new server configuration
shellmcp new --name "my-server" --desc "My custom MCP server"

# Add a tool interactively
shellmcp add-tool my-server.yml

# Validate the configuration
shellmcp validate my-server.yml

# Generate the FastMCP server
shellmcp generate my-server.yml
```

## Features

- 🚀 **Simple YAML Configuration**: Define tools, resources, and prompts in clean YAML
- 🔧 **Interactive CLI**: Add tools and resources with guided prompts
- 📝 **Template Support**: Use Jinja2 templates for dynamic command generation
- ✅ **Validation**: Built-in configuration validation and error checking
- 🎯 **FastMCP Integration**: Generates production-ready FastMCP servers
- 📦 **Complete Output**: Includes server code, requirements, and documentation
- 🔒 **Security-First**: Expose only trusted commands to AI agents
- 🎨 **Flexible**: Support for tools, resources, and prompts with reusable arguments

## Example

```yaml
server:
  name: "file-manager"
  desc: "File system operations"
  version: "1.0.0"

args:
  path_arg:
    help: "Directory path"
    type: string
    default: "."
  pattern_arg:
    help: "Search pattern"
    type: string

tools:
  list_files:
    cmd: "ls -la {{path}}"
    desc: "List files in a directory"
    args:
      - name: path
        ref: path_arg
  
  search_files:
    cmd: "find {{path}} -name '{{pattern}}' -type f"
    desc: "Search for files matching a pattern"
    args:
      - name: path
        ref: path_arg
      - name: pattern
        ref: pattern_arg

resources:
  system_info:
    uri: "file:///tmp/system-info.txt"
    name: "System Information"
    description: "Current system status and info"
    cmd: "uname -a && df -h"
    mime_type: "text/plain"

prompts:
  file_analysis:
    name: "File Analysis Assistant"
    description: "Helps analyze file system contents"
    template: |
      Analyze the following file system information:
      
      Current directory: {{path}}
      Files: {{file_list}}
      
      Provide insights about the file structure and suggest any organization improvements.
    args:
      - name: path
        help: "Directory path to analyze"
        type: string
        default: "."
      - name: file_list
        help: "List of files to analyze"
        type: string
```

## CLI Commands

ShellMCP provides several commands to help you create and manage MCP servers:

### `shellmcp new`
Create a new server configuration file.

```bash
shellmcp new --name "my-server" --desc "My custom MCP server" --version "1.0.0"
```

### `shellmcp add-tool`
Add a new tool to an existing configuration.

```bash
shellmcp add-tool my-server.yml --name "list-files" --cmd "ls -la {{path}}" --desc "List files in directory"
```

### `shellmcp add-resource`
Add a new resource to an existing configuration.

```bash
shellmcp add-resource my-server.yml --name "system-info" --uri "file:///tmp/system-info.txt" --resource-name "System Information"
```

### `shellmcp add-prompt`
Add a new prompt to an existing configuration.

```bash
shellmcp add-prompt my-server.yml --name "file-analysis" --prompt-name "File Analysis Assistant"
```

### `shellmcp validate`
Validate a YAML configuration file.

```bash
shellmcp validate my-server.yml --verbose
```

### `shellmcp generate`
Generate a FastMCP server from YAML configuration.

```bash
shellmcp generate my-server.yml --output-dir ./output --verbose
```

## Documentation

- [YAML Specification](docs/yml-specification.md)

## License

MIT License - see [LICENSE](LICENSE) for details.