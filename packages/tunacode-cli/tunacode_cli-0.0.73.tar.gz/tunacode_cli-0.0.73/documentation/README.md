# @documentation

Project documentation for tunacode.

## Directory Structure

```
documentation/
├── agent/                  # Agent architecture and workflows
│   ├── TOOLS_WORKFLOW.md
│   ├── agent-inspo.md
│   └── main-agent-architecture.md
├── configuration/         # System configuration docs
│   ├── config-file-example.md
│   ├── local-models.md
│   └── logging-configuration.md
├── development/          # Development practices
│   ├── codebase-hygiene.md
│   ├── command-system-architecture.md
│   ├── creating-custom-commands.md
│   ├── hatch-build-system.md
|   ├── performance-optimizations.md
│   └── prompt-principles.md
│── user/                 # user guides
    │── getting-started.md
    │── commands.md
    │── tools.md
```

## Purpose

General project documentation for features, architecture, and best practices.

## Quick Links

- [Command System Architecture](development/command-system-architecture.md) - Technical overview of the command system design and components.
- [Creating Custom Commands](development/creating-custom-commands.md) - Step-by-step guide for creating built-in and slash commands.
- [Hatch Build System](development/hatch-build-system.md) - Complete guide to using Hatch for development and building.
- [Configuration File Example](configuration/config-file-example.md) - Complete example of `~/.config/tunacode.json` with all available settings.
- [Local Models Setup](configuration/local-models.md) - Guide for using local models with LM Studio or any OpenAI-compatible API.
- [Performance Optimizations](development/performance-optimizations.md) - Major performance improvements and optimization strategies.
