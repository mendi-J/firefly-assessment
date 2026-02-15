# Firefly Asset Management Solution

A DevOps Asset Management solution that closes the gap between Infrastructure-as-Code (IaC) and cloud actual-footprint.

## Overview

This project implements a "cloud to Infrastructure-as-Code (IaC)" resources analyzer. It compares cloud resources with IaC resources and provides detailed analysis including:

- **CloudResourceItem**: The actual cloud resource
- **IacResourceItem**: The matching IaC resource (if exists)
- **State**: Can be `Missing`, `Match`, or `Modified`
- **ChangeLog**: Details of modifications when State is `Modified`

## Project Structure

```
.
├── README.md
├── requirements.txt
├── main.py
├── analyzer.py
├── models.py
├── utils.py
├── tests/
│   ├── test_analyzer.py
│   └── test_data/
│       ├── cloud_resources.json
│       └── iac_resources.json
└── examples/
    ├── cloud_resources.json
    └── iac_resources.json
```
## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
# Analyze resources
python main.py --cloud examples/cloud_resources.json --iac examples/iac_resources.json

# Output to file
python main.py --cloud examples/cloud_resources.json --iac examples/iac_resources.json --output report.json

# Pretty print
python main.py --cloud examples/cloud_resources.json --iac examples/iac_resources.json --pretty
```

### Python API

```python
from analyzer import ResourceAnalyzer

# Initialize analyzer
analyzer = ResourceAnalyzer()

# Load resources
cloud_resources = analyzer.load_json('cloud_resources.json')
iac_resources = analyzer.load_json('iac_resources.json')

# Analyze
results = analyzer.analyze(cloud_resources, iac_resources)

# Process results
for result in results:
    print(f"Resource: {result['CloudResourceItem']['id']}")
    print(f"State: {result['State']}")
    if result['State'] == 'Modified':
        print(f"Changes: {result['ChangeLog']}")
```

## Features

- ✅ Deep comparison of nested resource properties
- ✅ Detailed change tracking for modified resources
- ✅ Support for complex nested structures
- ✅ Type-safe comparisons
- ✅ Comprehensive test coverage
- ✅ Clean, well-documented code following PEP 8 standards

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Response Format

Each analysis result contains:

```json
{
  "CloudResourceItem": {},
  "IacResourceItem": {},
  "State": "Missing|Match|Modified",
  "ChangeLog": []
}
```

### ChangeLog Format (when State is Modified)

```json
{
  "KeyName": "property.path",
  "CloudValue": "value_in_cloud",
  "IacValue": "value_in_iac"
}
```

## Example

Given cloud and IaC resources, the analyzer will produce:

```json
{
  "CloudResourceItem": {
    "id": "i-1234567890abcdef0",
    "type": "aws_instance",
    "tags": {
      "totalAmount": "17kb"
    }
  },
  "IacResourceItem": {
    "id": "i-1234567890abcdef0",
    "type": "aws_instance",
    "tags": {
      "totalAmount": "22kb"
    }
  },
  "State": "Modified",
  "ChangeLog": [
    {
      "KeyName": "tags.totalAmount",
      "CloudValue": "17kb",
      "IacValue": "22kb"
    }
  ]
}
```

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## License

MIT License
