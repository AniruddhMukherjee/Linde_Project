# Enterprise Document & Project Management System (AIS-Machine)
### Automated Intelligence System · Built for Linde Engineering · Dec 2024 – Apr 2025

An enterprise-grade document intelligence platform built during an internship at **Linde Engineering, Vadodara**. AIS-Machine automates the extraction of answers from large document collections and generates structured, cited reports — replacing hours of manual document review with a single click.

---

## What It Does

Engineers at large industrial companies deal with hundreds of documents per project. Finding specific answers across them is slow, error-prone, and manual.

AIS-Machine solves this:

1. **Create a project** — define the scope and assign categories
2. **Upload documents** — attach relevant engineering documents to the project
3. **Add a questionnaire** — define the questions that need to be answered
4. **Generate a report** — the system reads all documents, answers every question, and cites exactly which document each answer was taken from

The result is a fully automated, source-cited intelligence report — generated in seconds instead of hours.

---

## Features

| Module | Description |
|--------|-------------|
| **Categories** | Organize projects and documents by domain or type |
| **Projects** | Create and manage engineering projects |
| **Docs** | Upload and attach documents to projects |
| **Questionnaire** | Define questions to be answered from the document set |
| **Reports** | Auto-generated reports with answers and source citations |

---

## Tech Stack

- **Frontend** — Streamlit (multi-page, ~2000 lines)
- **Backend** — Python, PostgreSQL, SQLite
- **Document Processing** — Automated extraction and NLP pipeline
- **Data** — Pandas, CSV pipelines
- **API** — Real-time data processing and visualization

---

## Key Results

- **40% improvement** in document processing efficiency across 100+ enterprise files
- **25% increase** in user engagement via real-time API integration
- Reduced manual document review time significantly across engineering teams

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
│   ├── Categories.py       # Category management
│   ├── Projects.py         # Project tracking
│   ├── Documents.py        # Document upload and management
│   ├── Questionnaire.py    # Question definition module
│   └── reports.py          # Automated report generation with citations
├── database_manager.py     # DB connection and queries
├── Data.csv                # Sample data
├── requirements.txt
└── README.md
```

---

## Context

Built during a **5-month internship at Linde Engineering** (Dec 2024 – Apr 2025), one of the world's largest industrial gas and engineering companies. The system was developed to handle real enterprise document workflows and deployed for internal use across engineering teams.

---

## Author

**Aniruddh Mukherjee**  
M.Sc. INFOTECH — Universität Stuttgart  
[GitHub](https://github.com/AniruddhMukherjee) · [LinkedIn](https://linkedin.com/in/aniruddh-mukherjee)
