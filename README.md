# EduManage — Student Management System (Full-Stack Project)

A full-stack **Student Management System** built with a **Python (Flask) REST API backend**,
an **HTML/CSS/JavaScript frontend**, a **SQLite database**, and a companion
**.NET (C#) console tool** that consumes the same REST API — demonstrating both
full-stack Python development and basic .NET / cross-language API integration.

This project is designed as a resume/portfolio piece that matches the skill set:
**Python, Flask, REST API, JSON, SQL, HTML5, CSS3, JavaScript, and .NET (Basic)**.

---

## Architecture

```
Browser (HTML/CSS/JS)  <---->  Flask REST API (Python)  <---->  SQLite DB
                                        ^
                                        |  HTTP GET (JSON)
                                        |
                          .NET Console App (C#) — Report Generator
```

- The **Flask backend** exposes a secured REST API (JWT auth) for student CRUD
  operations, plus one **public** read-only endpoint (`/api/public/report-data`)
  meant for external tools/services to consume.
- The **frontend** (server-rendered HTML + vanilla JS) is a login page and an
  admin dashboard that calls the REST API with `fetch()`.
- The **.NET console tool** is a separate, independent application written in
  C# that calls the same Flask API over HTTP, parses the JSON with
  `System.Text.Json`, and generates a department-wise attendance report
  (console summary + CSV export) — showing how a .NET client can integrate
  with a Python-powered backend.

---

## Folder Structure

```
EduManage-FullStack-Project/
├── backend/                     # Python Flask full-stack app
│   ├── app.py                   # Flask app: models, JWT auth, REST API, routes
│   ├── requirements.txt
│   ├── templates/
│   │   ├── login.html
│   │   └── dashboard.html
│   └── static/
│       ├── css/style.css
│       └── js/script.js
├── dotnet-report-tool/          # C# .NET console app (API consumer)
│   ├── ReportGenerator.csproj
│   └── Program.cs
└── README.md
```

---

## 1. Running the Python Full-Stack App

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

**Default login:** `admin` / `admin123`

Features:
- JWT-based authentication (login issues a signed token, stored in `localStorage`)
- Full CRUD for student records (Create, Read, Update, Delete)
- SQLite database (auto-created and seeded with sample data on first run)
- Clean, responsive dashboard UI (no frontend framework/build step required)

### REST API Reference

| Method | Endpoint                     | Auth | Description                         |
|--------|-------------------------------|------|--------------------------------------|
| POST   | `/api/login`                  | No   | Login, returns a JWT token           |
| GET    | `/api/students`                | Yes  | List all students                    |
| GET    | `/api/students/<id>`           | Yes  | Get one student                      |
| POST   | `/api/students`                | Yes  | Add a new student                    |
| PUT    | `/api/students/<id>`           | Yes  | Update a student                     |
| DELETE | `/api/students/<id>`           | Yes  | Delete a student                     |
| GET    | `/api/public/report-data`     | No   | Public read-only data (used by the .NET tool) |

Authenticated requests must include: `Authorization: Bearer <token>`

---

## 2. Running the .NET Report Generator

Requires the [.NET 8 SDK](https://dotnet.microsoft.com/download).

```bash
# Make sure the Flask backend is running first (step 1 above)
cd dotnet-report-tool
dotnet run
```

This will:
1. Call the Flask API's `/api/public/report-data` endpoint over HTTP
2. Deserialize the JSON into C# objects
3. Print a department-wise attendance summary to the console
4. Flag any students with attendance below 80%
5. Export a full report to `attendance_report.csv`

This tool demonstrates basic .NET fundamentals: `HttpClient`, `async/await`,
`System.Text.Json`, LINQ (`GroupBy`, `Average`, `Where`), and file I/O — all
while integrating with the Python backend.

---

## Tech Stack Summary

| Layer            | Technology                          |
|-------------------|--------------------------------------|
| Backend API       | Python, Flask, Flask-SQLAlchemy      |
| Auth              | PyJWT (JSON Web Tokens)              |
| Database          | SQLite                               |
| Frontend          | HTML5, CSS3, JavaScript (Fetch API)  |
| Cross-stack Tool  | C#, .NET 8 (Console App)             |

## Possible Extensions
- Swap SQLite for PostgreSQL/MySQL for production use
- Add role-based access (teacher vs. admin)
- Turn the .NET console tool into a small ASP.NET Core minimal API/service
- Containerize both apps with Docker
