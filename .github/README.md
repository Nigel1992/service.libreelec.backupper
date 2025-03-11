# 🔄 LibreELEC Backupper

<div align="center">

![icon](https://github.com/user-attachments/assets/0296587c-8be7-4a01-a889-e1231943907f)


*Your Ultimate Backup Solution for LibreELEC*

[![License: GPL-2.0](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](LICENSE)
[![Platform: LibreELEC](https://img.shields.io/badge/Platform-LibreELEC-green.svg)](https://libreelec.tv)
[![Kodi Add-on](https://img.shields.io/badge/Kodi-Add--on-orange.svg)](https://kodi.tv)
[![Python](https://img.shields.io/badge/Python-3.x-yellow.svg)](https://www.python.org)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)](../../commits/main)

---

[📥 Installation](#-installation) •
[✨ Features](#-features) •
[⚙️ Configuration](#%EF%B8%8F-configuration) •
[📖 Documentation](#-documentation) •
[🤝 Contributing](#-contributing)

</div>

## 🌟 Overview

LibreELEC Config Backupper is your comprehensive backup solution for LibreELEC systems. With a user-friendly interface and reliable backup management, it ensures your system configurations, add-ons, and personal data are always protected. (Note: Automated scheduling is planned for a future update)

<div align="center">

### 🎯 Key Benefits

| 🔒 Reliable | 🚀 Fast | 🎮 User-Friendly | 🔄 Manual Backups |
|:----------:|:-------:|:----------------:|:----------------:|
| Verified backups | Optimized performance | Intuitive interface | Easy to create |

</div>

## 📦 Features

<details>
<summary><b>💾 System Configuration Backup</b></summary>

- `config.txt` and essential system files
- Add-on configurations and data
- User preferences and settings
- Custom keymaps and profiles
</details>

<details>
<summary><b>🔄 Smart Management</b></summary>

- Manual backup creation
- Intelligent verification system
- Resource optimization
- Automatic cleanup routines
- Automated scheduling (Coming Soon)
</details>

<details>
<summary><b>🛡️ Data Protection</b></summary>

- Integrity verification
- Error recovery
- Secure storage
- Version control
</details>

## 📥 Installation

```bash
1️⃣ Download the latest release
2️⃣ Launch Kodi
3️⃣ Go to Add-ons → Install from zip file
4️⃣ Select the downloaded package
5️⃣ Configure your backup preferences
```

## ⚙️ Configuration

### Backup Settings
| Setting | Description | Default |
|:--------|:------------|:--------|
| 📂 Location | Backup storage path | `/storage/backup` |
| 🔢 Retention | Maximum backups to keep | 10 |
| ✅ Verify | Integrity checking | Enabled |

### Future Features (Coming Soon)
| Setting | Description | Status |
|:--------|:------------|:--------|
| ⏰ Scheduling | Automated backup scheduling | Planned |
| 🕒 Time | Execution time selection | Planned |
| 🧹 Auto-clean | Automatic old backup removal | Planned |

## 🔧 Development

### Prerequisites
```python
- Python 3.x
- Kodi 20 (Nexus)
- LibreELEC 12.0+
```

### Repository Structure
```
📁 service.libreelec.backupper
├── 📁 resources/
│   ├── 📁 lib/          # Core functionality
│   ├── 📁 language/     # Translations
│   └── 📄 settings.xml  # Configuration
├── 📄 addon.xml        # Metadata
└── 📄 README.md        # Documentation
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. 🍴 Fork the repository
2. 🌿 Create your feature branch
3. ✍️ Commit your changes
4. 🚀 Push to the branch
5. 📬 Open a Pull Request

## 📖 Documentation

- [📚 Detailed Guide](service.libreelec.backupper/README.md)
- [📝 Wiki](../../wiki)
- [❓ FAQ](../../wiki/FAQ)
- [🐛 Issue Tracker](../../issues)

## 📄 License

This project is protected under the [GNU General Public License v2.0](LICENSE).

---

<div align="center">

### 💖 Support & Community

[![Star](https://img.shields.io/github/stars/Nigel1992/service.libreelec.backupper?style=social)](../../stargazers)
[![Follow](https://img.shields.io/github/followers/Nigel1992?style=social)](https://github.com/Nigel1992)

[Report Bug](../../issues) • [Request Feature](../../issues) • [Get Support](../../discussions)

**Made with ❤️ for the LibreELEC Community**

</div>

