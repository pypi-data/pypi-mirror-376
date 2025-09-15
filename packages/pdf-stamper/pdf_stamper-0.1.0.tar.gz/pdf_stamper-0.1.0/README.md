# PDF Stamper

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/pdf-stamper.svg)](https://badge.fury.io/py/pdf-stamper)

A Python library and cli for stamping PDF files with sequential numbers or custom text overlays.

## Features

- Stamp PDF files with custom text
- Generate multiple numbered copies of PDFs
- Customizable font, size, and positioning
- Memory-efficient processing using streams
- Command-line interface for batch operations
- Clean, object-oriented API

## Installation

```bash
pip install pdf-stamper
```

Or install from source:

```bash
git clone https://github.com/MateusMolina/pdf-stamper.git
cd pdf-stamper
pip install -e .
```

## Quick Start

```bash
# Stamp a PDF with sequential numbers (Copy-1, Copy-2, ..., Copy-5)
pdf-stamper input.pdf --copies 5 --prefix "Copy-" --output-dir ./output --position top-right

# Custom positioning and formatting
pdf-stamper input.pdf --copies 10 --x 100 --y 750 --font-size 14
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
