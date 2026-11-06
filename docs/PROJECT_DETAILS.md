# Project Details - Food Redistribution Network

## 1. Introduction

The Food Redistribution Network is a web-based application developed to reduce food wastage by connecting food donors with individuals and organizations that require food.

The platform provides a structured process for publishing food donations, submitting receiver requests, identifying potential matches, and managing food allocation.

The application is developed using Python Flask and MySQL. It is deployed using Render, with the database hosted on Aiven.

## 2. Problem Statement

Food wastage and food shortages are two problems that often exist simultaneously. Hotels, hostels, events, and individuals may have surplus food, while people and organizations continue to require food assistance.

Without an organized platform, connecting available food with people who need it can be difficult.

The Food Redistribution Network aims to address this problem by providing a centralized system for managing food donations and requests.

## 3. Objectives

The main objectives of the project are:

- To reduce avoidable food wastage.
- To connect food donors with individuals and organizations in need.
- To provide an organized donation submission process.
- To allow receivers to submit food requirements.
- To identify potential matches between donations and requests.
- To use geographical information to support location-based matching.
- To consider receiver priority and request urgency.
- To support partial allocation of available food.
- To maintain donation, request, and allocation records.
- To track available, allocated, and remaining food quantities.

## 4. Technologies Used

### Programming Language
Python is used for backend application development.

### Backend Framework
Flask is used to handle application routes, user requests, authentication workflows, and database operations.

### Frontend
HTML is used to create the application pages, while CSS is used for styling.

### Database
MySQL is used to store user information, profiles, donations, food items, requests, allocations, and geographical data.

### Database Hosting
Aiven is used to host the MySQL database online.

### Application Hosting
Render is used to deploy and host the Flask application.

### Version Control
Git and GitHub are used to maintain the project's source code and version history.

## 5. User Roles

The application database supports registered users and temporary users. Donor and receiver profiles are maintained separately.

### 5.1 Donor

A donor provides details of surplus food available for redistribution.

Donor-related activities include:

- Registering or accessing a donor account.
- Managing donor profile information.
- Submitting food donations.
- Providing individual food item details.
- Specifying food quantities and meal types.
- Providing cooking time and food safety expiry information.
- Viewing donation and allocation information.

The database supports the following donor categories:

- Hotel
- Hostel
- Event
- Individual

### 5.2 Receiver

A receiver represents an individual or organization that requires food.

Receiver-related activities include:

- Registering or accessing a receiver account.
- Managing receiver profile information.
- Submitting food requests.
- Specifying required dates and meal preferences.
- Providing requested quantities.
- Specifying urgency and partial-allocation preferences.
- Viewing potential donation matches.
- Tracking request and allocation information.

The database supports the following receiver categories:

- ChildrenHome
- OldAgeHome
- NGO
- Other

### 5.3 Temporary Users

The database includes a `temporary_user` table to support temporary-user workflows.

Each temporary user is associated with a person record and has a unique tracking identifier.

Food donation and request records can reference registered users or temporary users.

## 6. Main Application Modules

### 6.1 User Registration and Authentication

The application provides registration and login functionality.

Registered account information is stored in the `registered_user` table.

The table maintains the username, password hash, account role, and associated person record.

### 6.2 Profile Management

The application maintains personal information and separate donor and receiver profile records.

The `person` table stores basic information such as name, phone number, pincode, and geographical coordinates.

### 6.3 Food Donation Management

Donors can submit details of surplus food.

The `food_donation` table stores the main donation information, including:

- Donor reference.
- Total quantity.
- Remaining quantity.
- Pincode.
- Geographical coordinates.
- Donation token.
- Donation status.
- Creation timestamp.

The `food_item` table stores individual food items belonging to a donation.

Each food item includes its name, category, quantity, meal type, cooked time, and safe-until time.

### 6.4 Food Request Management

Receivers can submit requests describing their food requirements.

The `request` table stores:

- Receiver reference.
- Required date.
- Meal preference.
- Total requested quantity.
- Allocated quantity.
- Remaining required quantity.
- Urgency level.
- Partial-allocation preference.
- Priority score.
- Request status.
- Creation timestamp.

### 6.5 Matching and Allocation

The application supports identifying potential matches between food donations and receiver requests.

Relevant information represented in the database includes:

- Available food quantities.
- Remaining food quantities.
- Required dates.
- Meal preferences.
- Food safety expiry times.
- Receiver priority.
- Request urgency.
- Partial-allocation preference.
- Geographical information.

The `allocation` table records the relationship between a food item and a receiver request.

It stores the allocated quantity, allocation status, and allocation timestamp.

### 6.6 Receiver Priority

The `receiver_profile` table stores the receiver's category and priority level.

The application uses the following category-to-priority mapping:

- ChildrenHome: Priority 3
- OldAgeHome: Priority 3
- NGO: Priority 2
- Other: Priority 1

The database restricts priority levels to 1, 2, or 3.

### 6.7 Dashboards

The application includes dashboard pages for users to view and manage relevant information.

These include:

- General user dashboard.
- Donor allocation information.
- Receiver matching information.
- Profile editing.

## 7. Location-Based Information

The project includes a geographical dataset containing Indian pincode information.

The source file is:

`data/pincode_geo.csv`

The dataset contains the following columns:

- pincode
- district
- state
- latitude
- longitude

Dataset validation results:

- Total records: 1,404
- Unique pincodes: 876
- Duplicate pincode groups: 308
- Records with missing fields: 0

Some pincodes have multiple coordinate observations in the source CSV.

The `pincode_geo` database table uses `pincode` as its primary key and stores one record per pincode.

Geographical information is used to support location-related operations in the application.

## 8. Database Overview

The application uses a MySQL database named `food_system`.

The database contains ten tables:

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

The SQL schema reference is maintained in:

`database/food_system_structure.sql`

Detailed database documentation is available in:

`docs/DATABASE_DETAILS.md`

## 9. Deployment Architecture

The application and database are hosted separately.

### Render

Render hosts the Flask web application.

The application is started using Gunicorn:

`gunicorn app:app`

### Aiven

Aiven hosts the MySQL database.

The Flask application connects to the database using environment variables.

### GitHub

GitHub stores the project's source code, documentation, configuration template, and database schema reference.

### Application Workflow

1. A user accesses the web application.
2. Flask handles the requested application route.
3. The application performs the required database operations.
4. MySQL stores or retrieves the requested information.
5. Flask renders the appropriate HTML page.

## 10. Project Directory Structure

The project is organized into the following directories:

- `data` - Geographical pincode dataset.
- `database` - MySQL schema reference.
- `docs` - Project and database documentation.
- `static` - CSS and other static resources.
- `templates` - HTML templates.
- Root directory - Flask application, dependencies, and configuration files.

## 11. Configuration and Security

The application uses environment variables for configuration.

The required variables include:

- `FLASK_SECRET`
- `FLASK_DEBUG`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

Security practices:

- Database credentials must not be committed to GitHub.
- The Flask secret key must remain private.
- The actual `.env` file must be excluded from version control.
- Production environment variables should be configured through Render.
- Full database backups should be stored privately and securely.

## 12. Future Enhancements

Possible future improvements include:

- More advanced geographical matching.
- Improved donation and request ranking algorithms.
- Notifications for new matches and allocation updates.
- Additional donation and request analytics.
- Detailed reports for donors and receivers.
- Improved user experience and accessibility.
- Additional food safety and verification mechanisms.

## 13. Conclusion

The Food Redistribution Network provides a structured platform for coordinating surplus food donations and receiver requests.

By combining user management, food donation management, request submission, location-related information, matching, and allocation tracking, the application aims to make food redistribution more organized and efficient.