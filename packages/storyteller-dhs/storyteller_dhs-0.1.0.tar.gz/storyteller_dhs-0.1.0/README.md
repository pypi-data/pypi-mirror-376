# Storyteller - DHS Database Viewer

Storyteller is a user-friendly web application designed to explore DHS (Demographic and Health Surveys) data.  
It provides an intuitive interface for browsing datasets, running queries, and generating insights, making it easier for researchers, analysts, and storytellers to work with complex health and demographic information.

---

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Development](#development)
6. [Contributing](#contributing)
7. [License](#license)
8. [Contact](#contact)

---

## Overview
The Storyteller app helps users unlock, search, and explore the full breadth of DHS datasets from any country or year.  
It is built on top of [Datasette](https://datasette.io/) and extends it with custom processors, exporters, and metadata tools.

---

## Features
- Browse DHS datasets across household, individual, and biomarker surveys.  
- Search across dozens of tables and thousands of records.  
- View variable definitions and relationships for every dataset.  
- Download filtered data for offline analysis.  
- Custom metadata export for reproducibility.  
- Simple CLI integration for automation.  

---

## Installation
Clone the repository and install the package in editable mode:

```bash
git clone https://github.com/kofiya-technologies/storyteller-DHS-database-viewer
cd storyteller-DHS-database-viewer
pip install pipenv
pipenv install --deploy --ignore-pipfile
```

Dependencies are managed with `setup.py` and `Pipfile`.

---

## Usage
After installation, you can start the Storyteller app:

```bash
storyteller start --db_path="path/to/your/dhs-database.db"
```

Other commands:
- Enable FTS manually:
  ```bash
  enable_fts --db_path="path/to/your/dhs-database.db"
  ```
- Run predefined queries:
  ```bash
  storyteller query path/to/your/dhs-database.db --menu mintiloai
  ```

---

## Development
To build the package (wheel + sdist):

```bash
python -m build
```

To run the development build process with additional checks:

```bash
build_package.bat
```

---

## Contributing
We welcome contributions!  
Please fork the repository, create a new branch, and submit a pull request.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact
**kofiyatech**  
Email: kofiya.technologies@gmail.com  
Website: [https://kofiyatech.com](https://kofiyatech.com)
