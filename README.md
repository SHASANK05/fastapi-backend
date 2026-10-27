# WorkForce AI Pro - HR Attrition Prediction & Workforce Intelligence Platform

An enterprise-grade HR intelligence and operational risk monitoring platform that pairs continuous workforce analytics with proactive retention workflows and real-time AI attrition risk scoring.

---

## Architecture Overview

`
                      +-----------------------------+
                      | React (Vite) + Tailwind CSS |
                      |    (Enterprise Frontend)    |
                      +--------------+--------------+
                                     |
                                REST / JSON
                                     |
                      +--------------v--------------+
                      |     FastAPI Backend API     |
                      | (JWT Auth, RBAC, Heuristics)|
                      +------+---------------+------+
                             |               |
               SQLAlchemy / MySQL        APScheduler
                             |         (Nightly Engine)
                      +------v------+        |
                      | MySQL 8.0 DB| <------+
                      +-------------+
`

---

## Core System Modules

1. **Authentication & Multi-Role RBAC**:
   - Roles: ADMIN, HR, MANAGER, EMPLOYEE
   - Secure token-based session handling with OAuth2 password grants and BCrypt hashing.
   - Dynamic frontend view gating (employee self-service vs. administrative risk engines).

2. **Predictive Attrition & Intelligence Engine**:
   - Exit risk calculation (0-100%) driven by salary benchmarks, tenure duration, overtime patterns, and leave frequencies.
   - Automatic classification: Low Risk, Moderate Watch, and High Risk / Immediate Intervention (>= 65%).
   - Identification of primary risk factors (e.g., compensation gaps, overtime exhaustion, prolonged absence).

3. **Retention Intervention Workflow**:
   - Slide-over diagnostic review drawer for high-risk personnel.
   - Lifecycle tracking: OPEN, UNDER_REVIEW, ACTION_PLANNED, RESOLVED, LOST.
   - Action proposals (1-on-1 mentorship, salary revision, workload rebalancing, lateral rotation).

4. **Department Analytics Deep-Dive**:
   - Interactive Department Risk Index bar chart.
   - Departmental metric rollups (headcount, average turnover probability, team salary benchmarks, primary team drivers).
   - Direct department roster drill-down.

5. **Operational Audit Trail**:
   - Chronological logging of authentication attempts, administrative updates, leave decisions, and batch ingestion.

6. **Batch Dataset Ingestion & Reporting**:
   - Multipart CSV dataset imports with automated duplicate detection and immediate scoring recalculation.
   - One-click CSV export and printable executive PDF views.

---

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy ORM, Pydantic, APScheduler, PyMySQL
- **Frontend**: React 18 (Vite), Tailwind CSS, Recharts, Lucide Icons, Axios
- **Database**: MySQL 8.0
- **Testing**: Pytest, HTTPX, FastAPI TestClient
- **DevOps**: Docker, Docker Compose, Nginx

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- MySQL Server 8.0+

### 2. Backend Setup
`ash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
`
Interactive API documentation: http://localhost:8000/docs

### 3. Frontend Setup
`ash
cd frontend
npm install
npm run dev
`
Web application: http://localhost:5173/

### 4. Running Automated Tests
`ash
cd backend
python -m pytest -v
`

---

## Default Demo Credentials

| Role | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **ADMIN** | admin@workforce.ai | AdminPassword123 | Full administrative control, all analytics, audit logs |
| **EMPLOYEE** | aarav@workforce.ai | Password@123 | Self-service portal, personal leaves, profile overview |

---

## Docker Deployment

To spin up the entire multi-container architecture (Frontend + Backend + MySQL Database):

`ash
docker-compose up --build -d
`
- **Web Application**: http://localhost/
- **FastAPI API Documentation**: http://localhost:8000/docs
