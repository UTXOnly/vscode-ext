# Datadog Integration Configuration Extension

A VS Code extension that provides YAML autocompletion and validation for Datadog integration configuration files.

## Features

- **Automatic Schema Download**: Downloads integration schemas from the [DataDog integrations-core repository](https://github.com/DataDog/integrations-core)
- **YAML Autocompletion**: Provides intelligent autocompletion for integration configuration files
- **Schema Validation**: Validates your YAML files against the official Datadog integration schemas
- **Supported Integrations**: Currently supports popular integrations like:
  - disk
  - cpu
  - memory
  - network
  - postgres
  - mysql
  - redis
  - nginx
  - apache
  - elasticsearch
  - kafka
  - rabbitmq
  - mongodb
  - cassandra
  - docker
  - kubernetes

## Usage

1. **Install the Extension**: Install this extension in VS Code
2. **Open Integration Config Files**: Open any YAML file with integration names (e.g., `disk.yaml`, `postgres.yml`)
3. **Automatic Schema Association**: The extension automatically associates schemas with files in the `conf.d/` directory or files named after integrations
4. **Update Schemas**: Use the command palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run "Update Datadog Integration Schemas" to refresh schemas

## File Patterns

The extension automatically provides autocompletion for files matching these patterns:
- `**/conf.d/*.yaml`
- `**/conf.d/*.yml`
- `**/disk.yaml`, `**/postgres.yml`, etc. (integration-specific files)

## Example Configuration

Create a file named `disk.yaml` in your `conf.d/` directory:

```yaml
instances:
  - use_mount: false
    mount_point: /dev/sda1
    all_partitions: true
```

The extension will provide autocompletion and validation based on the official Datadog disk integration schema.

## How it Works

This extension uses the [Red Hat YAML Language Server](https://github.com/redhat-developer/yaml-language-server) to provide intelligent YAML support. It:

1. Downloads integration schemas from the DataDog GitHub repository
2. Converts the YAML specification files to JSON Schema format
3. Associates these schemas with your YAML files
4. Provides autocompletion, validation, and documentation

## Development

To build and run this extension:

```bash
npm install
npm run compile
```

Then press `F5` in VS Code to run the extension in a new Extension Development Host window.

## Contributing

Feel free to submit issues and enhancement requests!
