# ReNinja

A powerful image batch renaming tool with CSV mapping support.

## Features

- CSV-based image renaming
- Sequential batch renaming
- Automatic updates
- Modern dark theme UI
- Drag and drop support
- Progress tracking
- Duplicate handling
- Mapping file generation

## Installation

1. Download the latest installer from the [Releases](https://github.com/V0rt3xRP/supreme_auction_tools/releases) page
2. Run the installer
3. Follow the installation wizard

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/V0rt3xRP/supreme_auction_tools.git
cd supreme_auction_tools
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python ReNinja.py
```

## Building from Source

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build the executable:
```bash
pyinstaller --noconsole --icon=assets/reninja_logo.ico ReNinja.py
```

3. Build the installer (requires Inno Setup):
```bash
iscc setup.iss
```

The installer will be created in the `output` directory.

## Usage

1. Launch ReNinja
2. Upload your CSV mapping file
3. Select source and destination folders
4. Choose mapping columns
5. Click "Process" to start renaming

## Updates

The application checks for updates automatically on startup. When an update is available:
1. You'll be notified with a changelog
2. Choose to update now or later
3. The update will download and install automatically

## License

MIT License © V0rt3xRP 