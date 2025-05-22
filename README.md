# 📘 C-Planner: AI-Powered University Course Scheduler

## 🏫 Project Description

**C-Planner** is a university course planner developed for the **American University of Armenia (AUA)**. It leverages **Gemini AI** to generate **personalized course schedules** based on a student's transcript, preferences, and degree requirements.

This tool supports **undergraduate and graduate programs**, incorporates **General Education Cluster requirements**, and integrates real-time course data scraped from **Sonis Jenzabar** and it also uses the respective degree requirements derived manually for each program from AUA's website.

Users can iteratively refine their schedule and export it as an `.ics` file for calendar use. It features an interactive interface built with **Streamlit** and utilizes **Docker** for containerized deployment.

---

## ✨ Features

* ✅ **AI-Powered Schedule Generation** based on personal preferences & program requirements
* 🎓 **Support for Undergraduate & Graduate Programs**
* 📄 **Transcript Upload & Parsing** for auto-detecting completed courses
* 🧠 **Interactive UI** with editable inputs and iterative generation
* 📆 **Export to `.ics`** calendar file (Google Calendar, Apple, Outlook, etc.)
* 🔍 **Real-Time Course Scraping** from Sonis Jenzabar via Selenium
* 🔐 **Secure Login/Signup System** with persistent session management

---

## ⚙️ Setup Instructions

### ✅ Prerequisites

* [Docker](https://docs.docker.com/get-docker/) and Docker Compose
* Gemini AI API Key

---

### 🔐 Environment Configuration

Create a `.env` file in the root directory with the following contents:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=streamlit_db
DB_USER=streamlit_user
DB_PASS=streamlit_pass
SECRET_KEY=your_secret_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Replace `your_secret_key_here` and `your_gemini_api_key_here` with valid values.

---

### 🚀 Running the Application

Build and launch services:

```bash
docker-compose up --build -d
```

Access the app at: `http://localhost:8501`
Adminer (database UI): `http://localhost:8080`

---

## 🗂 Project Structure Overview

```
C-Planner/
├── automating/       # Selenium scripts for Sonis scraping
├── data/             # Course data, requirements, preprocessing scripts
├── db/               # SQL schemas and view definitions
├── views/            # Streamlit app logic (UI layer)
├── .env              # Environment variables
├── docker-compose.yml
├── README.md
└── ...
```

---

## 📁 Views (UI Layer)

The `views/` directory contains the Streamlit logic managing the user interface, interactions, and navigation. It serves as the bridge between users and backend/AI systems.

### Key Responsibilities

* Rendering UI: forms, buttons, dropdowns, calendars, etc.
* Session Management using `st.session_state`
* Backend + Gemini AI Integration
* Schedule Parsing and Display
* Export functionality (`.ics` calendar format)

---

### 🔍 Detailed Views Overview

| File                  | Purpose                                                |
| --------------------- | ------------------------------------------------------ |
| `landing.py`          | Landing page; directs users to Sign Up or Login        |
| `login.py`            | Secure login with lockout and session timeout          |
| `signup.py`           | Signup with password hashing, validation, and feedback |
| `welcome.py`          | Welcome message post-login, directs users to planning  |
| `session_choice.py`   | Choose academic session & manage session state         |
| `transcript_intro.py` | Upload transcript; auto-parse completed courses        |
| `gemini.py`           | Interactive questionnaire: preferences, program, etc.  |
| `review_skipped.py`   | Review and complete skipped questions                  |
| `resume.py`           | Edit previously saved transcript or answers            |
| `generation.py`       | Generate schedule via Gemini API using inputs          |
| `gemini_answer.py`    | Display raw AI-generated schedule by weekdays          |
| `final_view.py`       | Show final schedule & allow `.ics` calendar export     |

---

## 🔄 How Views Work Together (User Flow)

1. **Landing**: User visits → chooses Sign Up / Log In
2. **Session Management**: Choose semester or resume previous planning
3. **Transcript Upload**: Auto-extract completed courses (optional)
4. **Questionnaire**: Preferences, program, elective choices
5. **Generation**: Schedule generated using Gemini AI
6. **Review**: View AI results by day and edit preferences
7. **Final Export**: Export calendar or refine again

---

## 🧠 Technical Highlights

### 🧾 Parsing Logic

* `final_view.py` uses regex to parse AI text into structured course objects
* Extracts course codes, instructors, days, and times

### 🕒 Date/Time Handling

* Uses `pytz` for timezone-aware conversions
* Handles daylight saving automatically

### 📅 ICS Calendar Export

* Uses `icalendar` Python package
* Embeds recurrence rules (weekly)
* Compatible with Google, Outlook, Apple calendars

### 🧠 AI Integration

* Uses Gemini API with a custom prompt template
* Combines: preferences, transcript, degree requirements
* Full traceability for debugging and review

---

## 🛠 Notes on API & Environment

* Gemini AI key must be set via `.env` (`GEMINI_API_KEY`)
* App uses a MySQL database (in Docker) with credentials from `.env`
* Secure session encryption with `SECRET_KEY`
* ChromeDriver must match installed Chrome version (for Selenium)
