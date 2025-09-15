# dbini

**A lightweight, zero-configuration NoSQL database solution for Python applications**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/dbini?style=for-the-badge)](https://pypi.org/project/dbini)
[![GitHub Stars](https://img.shields.io/github/stars/Binidu01/dbini?style=for-the-badge&logo=github)](https://github.com/Binidu01/dbini/stargazers)
[![License](https://img.shields.io/github/license/Binidu01/dbini?style=for-the-badge)](https://github.com/Binidu01/dbini/blob/main/LICENSE)
[![Issues](https://img.shields.io/github/issues/Binidu01/dbini?style=for-the-badge&logo=github)](https://github.com/Binidu01/dbini/issues)

---

## Overview

dbini is a self-contained NoSQL database solution designed for Python applications that need persistent data storage without the complexity of external database setup. It provides a simple, file-based storage system with support for both embedded usage and REST API access, making it ideal for prototyping, small to medium applications, and local-first development.

## Key Features

- **Zero Configuration**: Start using immediately without setup or external dependencies
- **Document Storage**: Store and query JSON documents with full CRUD operations
- **File Management**: Integrated file storage and retrieval system
- **Atomic Operations**: Secure atomic writes ensuring data integrity
- **Dual Interface**: Use as embedded Python library or standalone REST API server
- **Real-time Updates**: WebSocket support for live data synchronization
- **Query Support**: Flexible filtering and pagination capabilities
- **Local-first**: All data stored within your project directory

## Installation

### Requirements

- Python 3.9 or higher
- pip package manager

### Install from PyPI

```bash
pip install dbini
```

### Install from Source

```bash
git clone https://github.com/Binidu01/dbini.git
cd dbini
pip install .
```

## Quick Start

### Embedded Database Usage

```python
from dbini import DBini

# Initialize database for your project
db = DBini("myproject")

# Add a new document
user_data = {
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "age": 28
}
db.add_document("users", user_data)

# Find documents
users = db.find("users", filters={"age": 28})
for user in users:
    print(f"User: {user['name']} ({user['age']} years old)")

# Find single document
user = db.find_one("users", filters={"email": "alice@example.com"})
print(f"Found user: {user['name']}")

# File storage
file_id = db.save_file("profile_picture.jpg")

# Get file path
file_path = db.get_file_path(file_id)
print(f"File stored at: {file_path}")

# Add file reference to document
user_with_avatar = {
    "name": "Bob Smith",
    "email": "bob@example.com",
    "avatar": file_id
}
db.add_document("users", user_with_avatar)
```

### Complete Example Application

```python
import tkinter as tk
from tkinter import filedialog, messagebox
from dbini import DBini
from PIL import Image, ImageTk
import os

# Initialize dbini project
db = DBini("user_project")

def submit_form():
    name = entry_name.get().strip()
    email = entry_email.get().strip()
    password = entry_password.get().strip()
    profile_path = profile_pic_path.get()

    if not (name and email and password and profile_path):
        messagebox.showerror("Error", "All fields are required")
        return

    try:
        # Save profile picture
        file_id = db.save_file(profile_path)
        
        # Create user document
        user_data = {
            "name": name, 
            "email": email, 
            "password": password, 
            "avatar": file_id
        }
        db.add_document("users", user_data)

        messagebox.showinfo("Success", "User registered successfully!")
        show_dashboard()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save user: {e}")

def show_dashboard():
    # Get all users
    users = db.find("users", filters=None)
    
    for user in users:
        print(f"Name: {user['name']}, Email: {user['email']}")
        
        # Get avatar file path
        avatar_file_path = db.get_file_path(user.get("avatar"))
        if avatar_file_path and os.path.exists(avatar_file_path):
            print(f"Avatar: {avatar_file_path}")
```

### REST API Server

```python
from dbini.server import DBiniServer

# Start API server
server = DBiniServer("myproject")
server.serve(host="localhost", port=8080)
```

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/{collection}` | Create new document |
| `GET` | `/v1/{collection}` | Query documents with filters |
| `GET` | `/v1/{collection}/{id}` | Get document by ID |
| `PUT` | `/v1/{collection}/{id}` | Update document |
| `DELETE` | `/v1/{collection}/{id}` | Delete document |
| `POST` | `/v1/files` | Upload file |
| `GET` | `/v1/files/{id}` | Download file |

## Core API Methods

### Document Operations

```python
# Initialize database
db = DBini("project_name")

# Add document to collection
db.add_document("collection_name", document_data)

# Find documents with filters
results = db.find("collection_name", filters={"key": "value"})

# Find single document
doc = db.find_one("collection_name", filters={"email": "user@example.com"})

# Find all documents (no filters)
all_docs = db.find("collection_name", filters=None)
```

### File Operations

```python
# Save file and get ID
file_id = db.save_file("/path/to/file.jpg")

# Get file path from ID  
file_path = db.get_file_path(file_id)

# Check if file exists
if file_path and os.path.exists(file_path):
    print(f"File exists at: {file_path}")
```

## Project Structure

When you initialize a dbini project, the following directory structure is created:

```
myproject/
├── data/
│   └── users/
│       ├── 550e8400-e29b-41d4-a716-446655440000.json
│       └── 6ba7b810-9dad-11d1-80b4-00c04fd430c8.json
├── files/
│   ├── 123e4567-e89b-12d3-a456-426614174000.jpg
│   └── 987fcdeb-51a2-43d1-9f12-345678901234.png
└── meta/
    └── project.json
```

- **data/**: Contains JSON documents organized by collection
- **files/**: Stores uploaded files referenced by unique IDs
- **meta/**: Project metadata and configuration

## Advanced Usage

### Query with Filters

```python
# Find users by specific criteria
young_users = db.find("users", filters={"age": 25})
admin_users = db.find("users", filters={"role": "admin"})

# Find all documents in collection
all_users = db.find("users", filters=None)

# Find single matching document
user = db.find_one("users", filters={"email": "specific@example.com"})
```

### File Management

```python
# Save file and associate with document
profile_pic_id = db.save_file("user_photo.jpg")

user_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "profile_picture": profile_pic_id
}
db.add_document("users", user_data)

# Later, retrieve file path
users = db.find("users", filters={"name": "John Doe"})
for user in users:
    pic_id = user.get("profile_picture")
    if pic_id:
        pic_path = db.get_file_path(pic_id)
        if pic_path and os.path.exists(pic_path):
            print(f"Profile picture: {pic_path}")
```

## Architecture

dbini is built with modern Python technologies:

- **Core**: Pure Python with minimal dependencies
- **API Server**: FastAPI framework for REST endpoints
- **ASGI Server**: Uvicorn for high-performance async operations
- **Storage**: File-based JSON storage with atomic write operations
- **Real-time**: WebSocket support for live updates

## Use Cases

- **Rapid Prototyping**: Get started with persistent storage immediately
- **Small Applications**: Perfect for applications with moderate data requirements
- **Local Development**: Test applications without external database dependencies
- **Desktop Applications**: Ideal for tkinter, PyQt, or other desktop GUI frameworks
- **Edge Computing**: Lightweight storage for resource-constrained environments
- **Offline-first Apps**: Applications that need to work without network connectivity

## Contributing

We welcome contributions to dbini! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please ensure your code follows Python best practices and includes appropriate tests.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/Binidu01/dbini/blob/main/LICENSE) file for details.

## Support

- **Documentation**: [GitHub Repository](https://github.com/Binidu01/dbini)
- **Package**: [PyPI](https://pypi.org/project/dbini)
- **Issues**: [GitHub Issues](https://github.com/Binidu01/dbini/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Binidu01/dbini/discussions)

## Acknowledgments

dbini is inspired by modern database solutions and local-first software principles. Special thanks to the Python community and all contributors who help improve this project.

---

**Made with ❤️ by [Binidu01](https://github.com/Binidu01)**

*If you find dbini useful, please consider giving it a ⭐ on GitHub!*