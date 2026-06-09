# Enterprise Document & Project Management System
### Built for Linde Engineering · Dec 2024 – Apr 2025

An internal enterprise web application built during an internship at **Linde Engineering, Vadodara**, designed to streamline project documentation, data extraction, and reporting workflows across the organization.

---

## Overview

Large engineering companies manage hundreds of documents, projects, and questionnaires across teams. This system replaced manual processes with a centralized, interactive platform — reducing document retrieval time and improving reporting efficiency by **40%** across 100+ enterprise documents.

Built entirely in Python with a Streamlit frontend, the app integrates a PostgreSQL-backed database with an automated ML-based analytics pipeline.

---

## Features

| Module | Description |
|--------|-------------|
| **Categories** | Organize and filter enterprise documents by category |
| **Projects** | Track project status, metadata, and file paths |
| **Docs** | Upload, manage, and retrieve enterprise documents |
| **Questionnaire** | Structured data collection across business workflows |
| **Reports** | Automated report generation with real-time data insights |

---

## Tech Stack

- **Frontend** — Streamlit (multi-page app, ~2000 lines)
- **Backend** — Python, SQLite / PostgreSQL
- **Data** — Pandas, CSV pipelines
- **Automation** — ML-based analytics and reporting
- **API** — Real-time data processing and visualization

---

## Key Results

- **40% improvement** in document processing efficiency across 100+ enterprise files
- **25% increase** in user engagement via real-time API integration
- Replaced manual document workflows with an automated extraction and reporting pipeline

---

## Setup

```bash
# Clone the repo
git clone https://github.com/AniruddhMukherjee/Linde_Project.git
cd Linde_Project

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

---

## Project Structure

```
Linde_Project/
├── app.py                  # Main entry point, navigation
├── paths/
│   ├── Categories.py       # Category management module
│   ├── Projects.py         # Project tracking module
│   ├── Documents.py        # Document upload/retrieval
│   ├── Questionnaire.py    # Data collection module
│   └── reports.py          # Automated reporting
├── database_manager.py     # DB connection and queries
├── Data.csv                # Sample data
├── requirements.txt
└── README.md
```

---

## Context

This project was developed as part of a **5-month internship at Linde Engineering** (Dec 2024 – Apr 2025), one of the world's largest industrial gas and engineering companies. The system was built to handle real enterprise data workflows and deployed for internal use.

---

## Author

**Aniruddh Mukherjee**  
M.Sc. INFOTECH — Universität Stuttgart  
[GitHub](https://github.com/AniruddhMukherjee) · [LinkedIn](https://linkedin.com/in/aniruddh-mukherjee)
