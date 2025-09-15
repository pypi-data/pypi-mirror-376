# bball

Meta-package for the bball ecosystem - a comprehensive NBA analytics platform.

## Installation

### Install everything
```bash
pip install bball[all]
```

### Install specific components
```bash
# Just the CLI
pip install bball[cli]

# API server
pip install bball[api]

# Analytics stack (data, strategies, reports)
pip install bball[analytics]

# Multiple components
pip install bball[cli,api,data]
```

## Components

- **bball-core**: Core models and utilities shared across all packages
- **bball-cli**: Command-line interface for bball operations
- **bball-api**: REST/GraphQL API server
- **bball-data**: Data fetching and processing
- **bball-strategies**: Analysis strategies and algorithms
- **bball-reports**: Report generation and visualization

## Documentation

See [https://docs.bball.dev](https://docs.bball.dev) for full documentation.

## License

MIT
