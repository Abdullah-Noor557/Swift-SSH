# SwiftSSH - Lightweight SSH GUI Client

A modern, lightweight SSH GUI client with a hacker-themed interface. Built with Python and CustomTkinter for a clean, professional look.

## Features

### 🔐 Secure Connections
- SSH connection management with encrypted profile storage
- AES-encrypted password storage for saved connections
- Support for multiple connection profiles
- Quick reconnect from saved profiles

### 📁 File Management
- Remote file browser with directory navigation
- Drag-and-drop file uploads
- Download files from remote server
- File operations: create, delete, rename, properties
- Progress tracking for file transfers using SCP

### 💻 Multiple Terminals
- Tabbed terminal interface
- Multiple concurrent SSH sessions
- Terminal emulation with command history
- Copy/paste support
- ANSI color support

### 🔎 Network Discovery
- Scan local subnet(s) for open SSH (port 22)
- Live progress bar and detailed log output
- Auto-detect local networks; manual CIDR entry supported
- Optional UDP broadcast beacon for instant discovery

### 🎨 Modern UI
- Dark hacker theme with orange/red accents
- Professional, clean interface
- Responsive design
- Intuitive navigation

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Setup
1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Dependencies
- `customtkinter==5.2.2` - Modern UI framework
- `paramiko==3.4.0` - SSH client library
- `cryptography==41.0.7` - Encryption for password storage
- `tkinterdnd2==0.3.0` - Drag and drop support
- `Pillow==10.1.0` - Image processing

## Usage

### Starting the Application
```bash
python main.py
```

### Connecting to SSH Server
1. Enter connection details:
   - Host/IP address
   - Username
   - Password
   - Port (default: 22)

2. Save connection as profile (optional):
   - Click "Save" to store connection details
   - Profiles are encrypted and stored securely

3. Click "Connect" to establish SSH connection

### File Operations
- **Navigate**: Use breadcrumb navigation or path bar
- **Upload**: Drag and drop files or use Upload button
- **Download**: Select files and click Download button
- **Create Folder**: Use New Folder button
- **Delete**: Select files and click Delete button

### Terminal Sessions
- **New Terminal**: Click "New Terminal" button
- **Switch Tabs**: Click on terminal tab
- **Close Terminal**: Click "×" on tab or use context menu
- **Multiple Sessions**: Each tab maintains independent SSH session

### Network Discovery
- **Open**: Go to the "🔎 Discover" tab (or click "Discover SSH" in the sidebar)
- **Auto-detect**: Subnet is prefilled when possible; adjust as needed
- **Scan**: Click "Start Scan" to search for hosts with SSH open
- **Stop**: Click "Stop" to cancel an ongoing scan
- Results and detailed progress appear in the discovery log

#### Beacon-based Discovery (recommended in mixed networks)
- On the other PC, run the beacon sender to broadcast its presence:
  ```bash
  python beacon_sender.py --port 22
  ```
- In the login screen's Discovery card, choose Mode: "Broadcast" and click "Start Scan" to listen for beacons. Click a result to fill the Host.

## Project Structure

```
SwiftSSH/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config/
│   └── profiles.enc       # Encrypted connection profiles
├── ui/
│   ├── login_window.py    # Login/connection screen
│   ├── main_window.py     # Main application window
│   ├── file_browser.py    # Remote file browser
│   ├── terminal_panel.py  # Terminal interface
│   └── theme.py           # UI theme configuration
├── core/
│   ├── ssh_manager.py     # SSH connection handler
│   ├── scp_manager.py     # File transfer handler
│   ├── profile_manager.py # Encrypted profile storage
│   └── terminal.py        # Terminal emulation
└── assets/
    └── icons/             # File type icons
```

## Security Features

- **Encrypted Storage**: All saved passwords are encrypted using AES encryption
- **Secure Connections**: Uses Paramiko for secure SSH connections
- **No Plain Text**: Passwords are never stored in plain text
- **Profile Management**: Secure profile creation, loading, and deletion

## Target Platform

- **Primary**: Ubuntu Linux servers (target machine)
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **SSH Protocol**: Standard SSH/SCP protocol support

## Troubleshooting

### Connection Issues
- Verify SSH server is running on target machine
- Check firewall settings
- Ensure correct username and password
- Verify port number (default: 22)

### File Transfer Issues
- Check file permissions on remote server
- Ensure sufficient disk space
- Verify network connectivity

### Terminal Issues
- Check SSH server supports PTY allocation
- Verify terminal emulation settings
- Ensure proper shell environment

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

For support and questions, please open an issue in the project repository.
