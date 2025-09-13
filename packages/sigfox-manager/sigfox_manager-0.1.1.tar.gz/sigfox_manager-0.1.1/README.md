# Sigfox Manager

A Python library for handling Sigfox API operations with ease.

## Features

Currently supports the following operations:
- Get all contracts on current Token
- Get all devices on selected contract  
- Get device information
- Get messages from device
- Create device

## Installation

### From PyPI (when published)
```bash
pip install sigfox-manager
```

### From Source
```bash
git clone https://github.com/Jobenas/sigfox_manager_utility.git
cd sigfox_manager_utility
pip install .
```

### For Development
```bash
git clone https://github.com/Jobenas/sigfox_manager_utility.git
cd sigfox_manager_utility
pip install -e .[dev]
```

## Quick Start

```python
from sigfox_manager import SigfoxManager

# Initialize the manager with your Sigfox API credentials
manager = SigfoxManager(user="your_username", pwd="your_password")

# Get all contracts
contracts = manager.get_contracts()
print(f"Found {len(contracts.data)} contracts")

# Get devices for a contract
if contracts.data:
    contract_id = contracts.data[0].id
    devices = manager.get_devices(contract_id)
    print(f"Found {len(devices.data)} devices")

# Get device information
if devices.data:
    device_id = devices.data[0].id
    device_info = manager.get_device(device_id)
    print(f"Device: {device_info.name}")
    
    # Get device messages
    messages = manager.get_device_messages(device_id)
    print(f"Found {len(messages.data)} messages")
```

## API Reference

### SigfoxManager

The main class for interacting with the Sigfox API.

#### Constructor
```python
SigfoxManager(user: str, pwd: str)
```

#### Methods

- `get_contracts() -> ContractsResponse`: Get all contracts visible to the user
- `get_devices(contract_id: str) -> DevicesResponse`: Get all devices for a contract
- `get_device(device_id: str) -> Device`: Get detailed information about a specific device
- `get_device_messages(device_id: str) -> DeviceMessagesResponse`: Get messages from a device
- `create_device(device_data: BaseDevice) -> Device`: Create a new device

### Exceptions

The library provides custom exceptions for better error handling:

- `SigfoxAPIException`: Base exception for API errors
- `SigfoxDeviceNotFoundError`: Raised when a device is not found
- `SigfoxAuthError`: Raised for authentication errors
- `SigfoxDeviceCreateConflictException`: Raised when trying to create a duplicate device

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/Jobenas/sigfox_manager_utility.git
cd sigfox_manager_utility

# Install in development mode with dev dependencies
pip install -e .[dev]
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black sigfox_manager/
```

### Type Checking

```bash
mypy sigfox_manager/
```

### Building the Package

```bash
python -m build
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/Jobenas/sigfox_manager_utility/issues) page.

