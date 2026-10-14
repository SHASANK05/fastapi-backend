# Enterprise Human Resource Management System (HRMS)

A full-stack Human Resource Management System designed to handle organizational headcount, attendance tracking, leave requests with balance management, payroll calculation with PDF payslip generation, real-time KPI metrics, and administrative audit trails.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python 3.12+, SQLAlchemy ORM, SQLite (or MySQL/PostgreSQL ready), Pydantic v2.
- **Security & Auth:** OAuth2 Password Bearer flow, JWT (JSON Web Tokens), `passlib` with `bcrypt==4.0.1`.
- **Reporting & Documents:** ReportLab (automated PDF payslips), Python `csv` streaming responses.
- **Frontend:** React 18, Vite, Tailwind CSS, Axios, Lucide React icons.

---

## 📁 Project Architecture

```text
hrms_system/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py          # Authentication & token issuing
│   │   │   ├── employees.py     # Employee profile & directory management
│   │   │   ├── attendance.py    # Punch-in / punch-out with duplicate validation
│   │   │   ├── leaves.py        # Leave applications, balances, and reviews
│   │   │   ├── payroll.py       # Payroll calculation & PDF slip generation
│   │   │   ├── dashboard.py     # Live organizational KPI summary
│   │   │   ├── reports.py       # Streaming CSV exports for attendance/leaves/payroll
│   │   │   └── audit.py         # Read-only audit trail viewer
│   │   ├── services/
│   │   │   └── notifications.py # Automated email & activity dispatch engine
│   │   ├── database.py          # SQLAlchemy engine & session setup
│   │   ├── dependencies.py      # Role-based access control (RBAC) guards
│   │   ├── models.py            # Relational database schema models
│   │   └── security.py          # Password hashing & JWT validation
│   ├── main.py                  # FastAPI application entry point & CORS configuration
│   ├── seed_data.py             # Database initializer & baseline record seeder
│   └── requirements.txt         # Pinned backend dependencies
├── frontend/
│   ├── src/
│   │   ├── api.js               # Axios client with automatic Bearer token interceptor
│   │   ├── App.jsx              # Role-aware dashboard & portal layout
│   │   ├── index.css            # Tailwind directives and utility classes
│   │   └── main.jsx             # React DOM root entry point
│   ├── package.json             # Frontend package manifests
│   └── vite.config.js           # Vite development and build settings
├── HRMS_API_Collection.json     # Ready-to-import Postman v2.1 test collection
└── README.md                    # Project run & deployment guide