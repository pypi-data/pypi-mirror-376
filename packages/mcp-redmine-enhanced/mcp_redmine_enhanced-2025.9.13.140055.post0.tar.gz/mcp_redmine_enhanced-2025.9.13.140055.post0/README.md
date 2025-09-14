# MCP Redmine Enhanced (Active Fork)

**Fork Notice: This is an active fork of [runekaagaard/mcp-redmine](https://github.com/runekaagaard/mcp-redmine) maintained to ensure stability and availability when upstream development is limited.**

## Enhanced Features

This fork adds several powerful enhancements over the original:

- **🎯 Advanced Response Filtering**: Intelligent filtering with preset configurations (`minimal`, `clean`, `essential_issues`)
- **📝 Journal Filtering**: Filter Gerrit/code review entries from issue journals for cleaner output
- **🔒 Enhanced Security**: ReDoS protection and comprehensive input validation
- **⚡ MCP Capabilities**: Dynamic capability reporting based on API paths
- **🧪 Comprehensive Testing**: 106+ tests covering security and edge cases
- **🚀 Automated Publication**: Complete PyPI publication workflow with pre-checks

## Core Functionality

Let Claude be your Redmine assistant! MCP Redmine connects your MCP client to your Redmine instance, allowing it to:

- Search and browse projects and issues
- Create and update issues with full markdown support
- Upload and download file attachments
- Manage and track time entries
- Update issue statuses and fields
- Access comprehensive Redmine API functionality

Uses httpx for API requests and integrates with the Redmine OpenAPI specification for comprehensive API coverage.

![MCP Redmine in action](https://raw.githubusercontent.com/runekaagaard/mcp-redmine/refs/heads/main/screenshot.png)


## Usage with Claude Desktop
### 1. Installation using `uv`

Ensure you have uv installed.
```bash
uv --version
```

Install uv if you haven't already.

- Linux
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- macOS
  ```zsh
  brew install uv
  ```

- windows
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

Add to your `claude_desktop_config.json`:
```json
  {
    "mcpServers": {
      "redmine": {
        "command": "uvx",
        "args": ["--from", "mcp-redmine-enhanced==2025.09.13.140055.post0",
                "--refresh-package", "mcp-redmine-enhanced", "mcp-redmine"],
        "env": {
          "REDMINE_URL": "https://your-redmine-instance.example.com",
          "REDMINE_API_KEY": "your-api-key",
          "REDMINE_REQUEST_INSTRUCTIONS": "/path/to/instructions.md"
        }
      }
    }
  }
```

### Alternative: Use Latest Git Version (Development)

For the latest features and automatic updates, you can configure your MCP client to use the Git repository directly:

```json
{
  "mcpServers": {
    "redmine": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/olssonsten/mcp-redmine.git",
               "--refresh-package", "mcp-redmine-enhanced", "mcp-redmine"],
      "env": {
        "REDMINE_URL": "https://your-redmine-instance.example.com",
        "REDMINE_API_KEY": "your-api-key",
        "REDMINE_REQUEST_INSTRUCTIONS": "/path/to/instructions.md"
      }
    }
  }
}
```

This automatically uses the latest version from the main branch without needing PyPI updates. Perfect for development and testing new features.

**Note**: The package name is `mcp-redmine-enhanced` but the console script remains `mcp-redmine` for compatibility.

### 2. Installation using `docker`

Ensure you have docker installed. 
```bash
docker --version
```

Build docker image:
```bash
git clone git@github.com:runekaagaard/mcp-redmine.git
cd mcp-redmine
docker build -t mcp-redmine .
```
Add to your `claude_desktop_config.json`:
  ```json
  {
    "mcpServers": {
      "redmine": {
        "command": "docker",
        "args":  [
            "run",
            "-i",
            "--rm",
            "-e", "REDMINE_URL",
            "-e", "REDMINE_API_KEY",
            "-e", "REDMINE_REQUEST_INSTRUCTIONS",
            "-v", "/path/to/instructions.md:/app/INSTRUCTIONS.md",
            "mcp-redmine"
        ],
        "env": {
          "REDMINE_URL": "https://your-redmine-instance.example.com",
          "REDMINE_API_KEY": "your-api-key",
          "REDMINE_REQUEST_INSTRUCTIONS": "/app/INSTRUCTIONS.md"
        }
      }
    }
  }
  ```

## Environment Variables

- `REDMINE_URL`: URL of your Redmine instance (required)
- `REDMINE_API_KEY`: Your Redmine API key (required, see below for how to get it)
- `REDMINE_REQUEST_INSTRUCTIONS`: Path to a file containing additional instructions for the redmine_request tool (optional). I've found it works great to have the LLM generate that file after a session. ([example1](INSTRUCTIONS_EXAMPLE1.md) [example2](INSTRUCTIONS_EXAMPLE2.md))

> **Note**: When running via Docker, the `REDMINE_REQUEST_INSTRUCTIONS` environment variable must point to a **path inside the container**, not a path on the host machine.  
> Therefore, if you want to use a local file, you need to **mount it into the container** at the correct location.


## Getting Your Redmine API Key

1. Log in to your Redmine instance
2. Go to "My account" (typically found in the top-right menu)
3. On the right side of the page, you should see "API access key"
4. Click "Show" to view your existing key or "Generate" to create a new one
5. Copy this key for use in your configuration

## API

### Tools

- **redmine_paths_list**
  - Return a list of available API paths from OpenAPI spec
  - No input required
  - Returns a YAML string containing a list of path templates:
  ```
  - /issues.json
  - /projects.json
  - /time_entries.json
  ...
  ```

- **redmine_paths_info**
  - Get full path information for given path templates
  - Input: `path_templates` (list of strings)
  - Returns YAML string containing API specifications for the requested paths:
  ```yaml
  /issues.json:
    get:
      operationId: getIssues
      parameters:
        - $ref: '#/components/parameters/format'
      ...
  ```

- **redmine_request**
  - Make a request to the Redmine API
  - Inputs:
    - `path` (string): API endpoint path (e.g. '/issues.json')
    - `method` (string, optional): HTTP method to use (default: 'get')
    - `data` (object, optional): Dictionary for request body (for POST/PUT)
    - `params` (object, optional): Dictionary for query parameters
    - `mcp_filter` (object, optional): MCP response filtering (use redmine_paths_info to discover options)
  - Returns YAML string containing response status code, body and error message:
  ```yaml
  status_code: 200
  body:
    issues:
      - id: 1
        subject: "Fix login page"
        ...
  error: ""
  mcp_filtered: true  # Added when filtering is applied
  ```

- **redmine_upload**
  - Upload a file to Redmine and get a token for attachment
  - Inputs:
    - `file_path` (string): Fully qualified path to the file to upload
    - `description` (string, optional): Optional description for the file
  - Returns YAML string with the same format as redmine_request, including upload token:
  ```yaml
  status_code: 201
  body:
    upload:
      id: 7
      token: "7.ed32257a2ab0f7526c0d72c32994c58b131bb2c0775f7aa84aae01ea8397ea54"
  error: ""
  ```

- **redmine_download**
  - Download an attachment from Redmine and save it to a local file
  - Inputs:
    - `attachment_id` (integer): The ID of the attachment to download
    - `save_path` (string): Fully qualified path where the file should be saved
    - `filename` (string, optional): Optional filename to use (determined automatically if not provided)
  - Returns YAML string with download results:
  ```yaml
  status_code: 200
  body:
    saved_to: "/path/to/downloaded/file.pdf"
    filename: "file.pdf"
  error: ""
  ```

## Examples

### Creating a new issue

```
Let's create a new bug report in the "Website" project:

1. Title: "Homepage not loading on mobile devices"
2. Description: "When accessing the homepage from iOS or Android devices, the loading spinner appears but the content never loads. This issue started after the last deployment."
3. Priority: High
4. Assign to: John Smith
```

### Searching for issues

```
Can you find all high priority issues in the "Website" project that are currently unassigned?
```

### Updating issue status

```
Please mark issue #123 as "In Progress" and add a comment: "I've started working on this issue. Expect it to be completed by Friday."
```

### Logging time

```
Log 3.5 hours against issue #456 for "Implementing user authentication" done today.
```

### Using Response Filtering (New)

```
Get issues with reduced verbosity:
redmine_request("/issues.json", params={"limit": 5}, mcp_filter={"remove_empty": True, "remove_custom_fields": True})

Use preset for clean responses:
redmine_request("/issues.json", mcp_filter="clean")
Filter journals for code reviews:
redmine_request("/issues/123.json", params={"include": "journals"}, mcp_filter={"journals": {"code_review_only": True}})
```

## MCP Directory Listings

MCP Redmine is listed in the following MCP directory sites and repositories:

- [MCP.so](https://mcp.so/server/mcp-redmine)
- [Glama](https://glama.ai/mcp/servers/@runekaagaard/mcp-redmine)

## Developing

First clone the github repository and install the dependencies:

```
git clone git@github.com:runekaagaard/mcp-redmine.git
cd mcp-redmine
uv sync
```

Then set this in claude_desktop_config.json:

```
...
"command": "uv",
"args": ["run", "--directory", "/path/to/mcp-redmine", "-m", "mcp_redmine.server", "main"],
...
```

## My Other LLM Projects

- **[MCP Alchemy](https://github.com/runekaagaard/mcp-alchemy)** - Connect Claude Desktop to databases for exploring schema and running SQL.
- **[MCP Notmuch Sendmail](https://github.com/runekaagaard/mcp-notmuch-sendmail)** - Email assistant for Claude Desktop using notmuch.
- **[Diffpilot](https://github.com/runekaagaard/diffpilot)** - Multi-column git diff viewer with file grouping and tagging.
- **[Claude Local Files](https://github.com/runekaagaard/claude-local-files)** - Access local files in Claude Desktop artifacts.

## Contributing

Contributions are warmly welcomed! Whether it's bug reports, feature requests, documentation improvements, or code contributions - all input is valuable. Feel free to:

- Open an issue to report bugs or suggest features
- Submit pull requests with improvements
- Enhance documentation or share your usage examples
- Ask questions and share your experiences

The goal is to make Redmine project management with Claude even better, and your insights and contributions help achieve that.

## Acknowledgments

This project builds on the excellent work of others:

- [httpx](https://www.python-httpx.org/) - For handling HTTP requests
- [Redmine OpenAPI Specification](https://github.com/d-yoshi/redmine-openapi) - For the comprehensive API specification
- [Redmine](https://www.redmine.org/) - The flexible project management web application

## License

Mozilla Public License Version 2.0
