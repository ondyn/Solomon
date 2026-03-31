# Solomon Test Plugin

A minimal NetBox plugin to verify the plugin development workflow for the Solomon project.

## Features

- JSON status endpoint at `/plugins/solomon-test/status/`
- Navigation menu item
- Simple `TestItem` model

## Development

This plugin is automatically installed in editable mode when the Docker container starts.
Any changes to Python files trigger an immediate granian reload.
