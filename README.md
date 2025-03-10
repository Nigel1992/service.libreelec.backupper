# LibreELEC Config Backupper

<div align="center">

![LibreELEC Logo](https://raw.githubusercontent.com/LibreELEC/LibreELEC.tv/master/distribution/doc/resources/logo.png)

*A powerful backup solution for your LibreELEC system*

[![License: GPL-2.0](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](LICENSE)
[![Platform: LibreELEC](https://img.shields.io/badge/Platform-LibreELEC-green.svg)](https://libreelec.tv)
[![Kodi Add-on](https://img.shields.io/badge/Kodi-Add--on-orange.svg)](https://kodi.tv)

</div>

## Repository Structure

```
.
├── .github/                    # GitHub templates and workflows
├── service.libreelec.backupper/# Main addon directory
│   ├── resources/             # Addon resources
│   │   ├── lib/              # Core functionality
│   │   ├── language/         # Translations
│   │   └── settings.xml      # Addon settings
│   ├── addon.xml             # Addon metadata
│   └── README.md             # Addon documentation
├── LICENSE                    # GPL-2.0 license
└── README.md                  # This file
```

## About

LibreELEC Config Backupper is a comprehensive backup solution for LibreELEC systems, offering automated scheduling and intelligent backup management. The addon provides a user-friendly interface for backing up and restoring system configurations, add-ons, and user data.

## Key Features

- **System Configuration Backup**
  - Essential system files
  - Add-on configurations
  - User settings
  
- **Smart Backup Management**
  - Automated scheduling
  - Backup verification
  - Resource optimization
  
- **User-Friendly Interface**
  - Progress notifications
  - Easy restore options
  - Detailed status updates

## Installation

1. Download the latest release
2. Open Kodi
3. Navigate to Add-ons → Install from zip file
4. Select the downloaded zip file
5. Configure backup settings

## Development

### Requirements
- Python 3.x
- Kodi 20 (Nexus)
- LibreELEC 12.0+

### Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Documentation

For detailed documentation, please see:
- [Addon README](service.libreelec.backupper/README.md) - Complete feature documentation
- [Wiki](../../wiki) - Usage guides and tutorials
- [Issues](../../issues) - Bug reports and feature requests

## License

This project is licensed under the GNU General Public License v2.0 - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for the LibreELEC Community**

[Report Bug](../../issues) · [Request Feature](../../issues) · [Get Support](../../discussions)

</div>
