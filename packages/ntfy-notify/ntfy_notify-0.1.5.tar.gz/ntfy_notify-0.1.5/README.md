# ntfy-notify

## Installation

### Using pip

```bash
pip install ntfy-notify
```

### Using Poetry

```bash
poetry add ntfy-notify
```

## Configuration

Create a configuration file at `~/.config/ntfy-notify/config.toml` with your ntfy.sh credentials:

```toml
# Required: Your ntfy.sh server URL
server = "https://ntfy.sh"

# Required: Your access token (if using ntfy.sh with authentication)
token = "your_token_here"

# Required: Default topic to send notifications to
default_topic = "your_topic_here"

# Optional: Default message priority (default: "default")
# Valid values: "min", "low", "default", "high", "max"
default_priority = "default"
```

## Usage

### Python API

```python
import ntfy_notify

# Basic notification
ntfy_notify.send_notification("Hello from Python!")

# With title and priority
ntfy_notify.send_notification(
    "This is an important message",
    title="Important Update",
    priority="high"
)

# With custom topic
ntfy_notify.send_notification("This goes to a custom topic", topic="custom_topic")

# With additional options
ntfy_notify.send_notification(
    "Check out our website!",
    title="Website",
    click_url="https://example.com",
    tags=["globe_with_meridians", "link"]
)
```

### Command Line Interface

```bash
# Basic usage
ntfy_notify "Hello from the command line!"

# With options
ntfy_notify -m "Important message" -t mytopic --title "Alert" --priority high

# With clickable URL
ntfy_notify -m "Check out our website!" --click-url https://example.com

# With tags
ntfy_notify -m "Server down!" --tags warning,skull
```

#### Command Line Options

```
Usage: ntfy-notify [OPTIONS] [MESSAGE]

  Send a notification via ntfy.sh

  If MESSAGE is not provided, reads from stdin.

Options:
  -m, --message TEXT       The message to send (required if not reading from
                          stdin)
  -t, --topic TEXT         Topic to send to (overrides config)
  --title TEXT             Message title
  -p, --priority [min|low|default|high|max]
                          Message priority
  --click-url TEXT         URL to open when notification is clicked
  --tags TEXT              Comma-separated list of tags/emojis
  --config FILE            Path to config file
  --version                Show the version and exit.
  --help                   Show this message and exit.
```

## License

This project is licensed under the EUPL-1.2 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Running Tests

The test suite uses pytest and can be run with:

```bash
# Install test dependencies
poetry install --with test

# Run tests
poetry run pytest -v tests/
```

## Development

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Create a test configuration file at `~/.config/ntfy-notify/config.toml`
4. Run tests to verify your setup

## License

EUPL-1.2