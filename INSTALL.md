# Installation Guide

## Prerequisites

- Python 3.7 or higher
- PostgreSQL database
- pip package manager

## Step-by-Step Installation

### 1. Clone or Download Repository

```bash
cd bss-test
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database

Copy the example configuration:

```bash
copy config\database.ini.example config\database.ini
```

Edit `config/database.ini` with your PostgreSQL credentials:

```ini
[postgres]
host = localhost
port = 5432
user = your_username
pass = your_password
db_name = resultados_mh
```

### 5. Initialize Database

The database schema should already exist from the original BSS project.
If not, use the SQL scripts from the original `Database/` directory.

### 6. Verify Installation

Test the database connection:

```bash
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print('Database connection successful')"
```

## Quick Start

### Create an Experiment Queue

```bash
python cli/queue_manager.py --config config/experiments/example.yaml
```

### Start a Worker

```bash
python cli/worker.py
```

### Launch Dashboard

```bash
streamlit run ui/dashboard.py
```

## Troubleshooting

### Import Errors

Make sure you're running commands from the `bss-test` directory and your virtual environment is activated.

### Database Connection Errors

Verify your PostgreSQL server is running and credentials in `config/database.ini` are correct.

### Missing Dependencies

Reinstall dependencies:

```bash
pip install --upgrade -r requirements.txt
```
