# Projecto Integrador Prodigi Grupo2

Modular system for clinical management, including emergency episodes, triage, inpatient care, and operational analytics.

## Structure
- `backend/`: FastAPI Python application.
- `frontend/`: React Web application.
- `database/`: SQL schema for PostgreSQL.
- `ai/`: Analytical models and resource optimization logic.
- `mobile/`: Read-only consultation mobile app (React Native).

## How to Run

### 1. Database
1. Install PostgreSQL.
2. Create a database named `urgencias_g2`.
3. Execute `database/schema.sql` to initialize the tables and seed data.

### 2. Backend
1. Navigate to `backend/`.
2. Create a virtual environment: `python -m venv venv`.
3. Activate it: `venv\Scripts\activate`.
4. Install dependencies: `pip install -r requirements.txt`.
5. Run the server: `uvicorn app.main:app --reload`.

### 3. Frontend
1. Navigate to `frontend/`.
2. Install dependencies: `npm install`.
3. Start the application: `npm start`.

## Security & Privacy
- **RBAC**: Access levels for Admin, Doctor, Nurse, and Receptionist.
- **Anonymization**: `utente_analitico` view for GDPR-compliant analytics.
- **Audit**: All sensitive accesses are logged in the `auditoria` table.

## AI & Analytics
- Primary focus on **Operational Analytics** to optimize resource allocation and predict bottlenecks in the emergency patient flow.
