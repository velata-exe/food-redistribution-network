# Food Redistribution Network

A web-based platform that connects food donors with individuals and organizations that need food. The system aims to reduce food wastage by coordinating food donations, receiver requests, location-based matching, and food allocation.

## Project Overview

Surplus food from hotels, hostels, events, and individuals can be redistributed to people and organizations that need it.

The Food Redistribution Network provides a centralized platform where donors can publish available food donations and receivers can submit food requests. The application helps identify potential matches and manage the allocation of available food.

## Objectives

- Reduce avoidable food wastage.
- Connect food donors with individuals and organizations in need.
- Provide an organized process for submitting food donations and requests.
- Identify suitable matches between available food and receiver requirements.
- Support location-based matching using pincode information.
- Prioritize receiver requests based on urgency and receiver category.
- Support partial allocation of available food.
- Track donation, request, and allocation status.

## Features

### User Management
- User registration and login.
- Donor and receiver account roles.
- Donor and receiver profile management.
- Support for registered and temporary users.

### Food Donation
- Submit food donation details.
- Add individual food items under a donation.
- Record food names, categories, quantities, and meal types.
- Store cooking time and food safety expiry time.
- Track available and remaining food quantities.

### Food Requests
- Submit food requirements.
- Specify required date and meal preference.
- Specify requested quantity and urgency level.
- Support partial-allocation preferences.
- Track allocated and remaining quantities.

### Matching and Allocation
- Identify potential matches between food donations and receiver requests.
- Use location information to support matching.
- Consider food availability, required dates, meal preferences, and request priority.
- Support partial allocation.
- Maintain allocation records and status.

### Dashboards
- User dashboard.
- Donor allocation information.
- Receiver matching information.
- Profile management.

## Technology Stack

- Programming Language: Python
- Backend Framework: Flask
- Frontend: HTML and CSS
- Database: MySQL 8
- Database Hosting: Aiven
- Application Hosting: Render
- Database Connector: mysql-connector-python
- WSGI Server: Gunicorn
- Version Control: Git and GitHub

## Project Structure

```text
food-redistribution-network/
|
|-- app.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- .env.example
|
|-- data/
|   |-- pincode_geo.csv
|
|-- database/
|   |-- food_system_structure.sql
|
|-- docs/
|   |-- PROJECT_DETAILS.md
|   |-- DATABASE_DETAILS.md
|
|-- static/
|   |-- style.css
|
|-- templates/
|   |-- dashboard.html
|   |-- donate.html
|   |-- donor_allocations.html
|   |-- edit_profile.html
|   |-- landing.html
|   |-- login.html
|   |-- receiver_matches.html
|   |-- request.html
|   |-- signup.html
```

## Database

The application uses a MySQL database named `food_system`, hosted on Aiven.

The database contains the following ten tables:

- `person`
- `registered_user`
- `temporary_user`
- `donor_profile`
- `receiver_profile`
- `food_donation`
- `food_item`
- `request`
- `allocation`
- `pincode_geo`

The database schema reference is available in `database/food_system_structure.sql`.

Detailed database documentation is available in `docs/DATABASE_DETAILS.md`.

## Pincode Dataset

The project includes a geographical dataset named `pincode_geo.csv`.

It contains the following fields:

- Pincode
- District
- State
- Latitude
- Longitude

Dataset summary:

- Total records: 1,404
- Unique pincodes: 876
- Pincode groups with duplicate records: 308
- Records with missing fields: 0

Some pincodes have multiple coordinate records in the source CSV. The database uses `pincode` as the primary key and stores one geographical record per pincode.

## Installation and Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/velata-exe/food-redistribution-network.git
cd food-redistribution-network
```

Alternatively, use the SSH clone URL available in the GitHub repository.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

For Linux or macOS:

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root.

Use `.env.example` as a reference and provide your own database credentials and Flask secret key.

Never commit the actual `.env` file to GitHub.

### 6. Run the Application

```bash
python app.py
```

Open the local URL displayed in the terminal.

## Environment Variables

The application uses the following environment variables:

- `FLASK_SECRET` - Flask session secret key.
- `FLASK_DEBUG` - Controls Flask debug mode.
- `DB_HOST` - MySQL server hostname.
- `DB_PORT` - MySQL server port.
- `DB_USER` - MySQL username.
- `DB_PASSWORD` - MySQL password.
- `DB_NAME` - Database name.

## Deployment

The application is deployed on Render, while the MySQL database is hosted on Aiven.

The deployment architecture consists of:

- GitHub for source code management.
- Render for hosting the Flask application.
- Aiven for hosting the MySQL database.

The Render start command is:

```bash
gunicorn app:app
```

Configure the required environment variables in the Render service settings.

## Security

- Do not commit actual database credentials.
- Keep the Flask secret key private.
- Keep the `.env` file out of version control.
- Use `.env.example` to document the required configuration.
- Store full database backups privately and securely.
- Review SQL scripts before executing them against an existing database.

## Documentation

Additional documentation is available in the `docs` directory:

- `PROJECT_DETAILS.md` - Project objectives, modules, workflows, and architecture.
- `DATABASE_DETAILS.md` - Database tables, relationships, and constraints.

## Project Status

The Food Redistribution Network is a deployed Flask and MySQL application. The project may be extended with additional matching, notification, reporting, and food redistribution features.