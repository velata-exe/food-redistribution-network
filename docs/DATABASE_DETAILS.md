# Database Details - Food Redistribution Network

## 1. Database Overview

The Food Redistribution Network uses a MySQL database named `food_system`.

The database is hosted on Aiven and is used to store user information, donor and receiver profiles, food donations, food items, receiver requests, allocations, and geographical information.

Database details:

- Database name: `food_system`
- Database system: MySQL
- Schema export version: MySQL 8.0.44
- Database hosting platform: Aiven
- Storage engine: InnoDB
- Character set: utf8mb4

The database schema reference is available in:

`database/food_system_structure.sql`

## 2. Database Tables

The database contains ten tables:

1. `person`
2. `registered_user`
3. `temporary_user`
4. `donor_profile`
5. `receiver_profile`
6. `food_donation`
7. `food_item`
8. `request`
9. `allocation`
10. `pincode_geo`

## 3. Table Descriptions

### 3.1 person

The `person` table stores basic personal and geographical information.

Columns:

- `person_id` - Primary key and unique person identifier.
- `name` - Person's name.
- `phone` - Contact number.
- `pincode` - Six-character pincode.
- `latitude` - Geographical latitude.
- `longitude` - Geographical longitude.
- `created_at` - Record creation timestamp.

### 3.2 registered_user

The `registered_user` table stores registered account information.

Columns:

- `user_id` - Primary key and unique registered-user identifier.
- `person_id` - References the associated person.
- `username` - Unique username.
- `password_hash` - Hashed password.
- `role` - Account role, either Donor or Receiver.
- `created_at` - Record creation timestamp.

Important constraints:

- `person_id` is unique.
- `username` is unique.
- `person_id` references `person(person_id)`.

### 3.3 temporary_user

The `temporary_user` table stores information associated with temporary users.

Columns:

- `temp_user_id` - Primary key and temporary-user identifier.
- `person_id` - References the associated person.
- `tracking_id` - Unique tracking identifier.
- `created_at` - Record creation timestamp.

Important constraints:

- `person_id` is unique.
- `tracking_id` is unique.
- `person_id` references `person(person_id)`.

### 3.4 donor_profile

The `donor_profile` table stores donor-specific information.

Columns:

- `person_id` - Primary key and reference to the associated person.
- `donor_category` - Category of the donor.
- `status` - Donor profile status.

Supported donor categories:

- Hotel
- Hostel
- Event
- Individual

Supported statuses:

- Active
- Inactive

### 3.5 receiver_profile

The `receiver_profile` table stores receiver-specific information.

Columns:

- `person_id` - Primary key and reference to the associated person.
- `receiver_category` - Category of the receiver.
- `status` - Receiver profile status.
- `priority_level` - Receiver priority level.

Supported receiver categories:

- ChildrenHome
- OldAgeHome
- NGO
- Other

Supported statuses:

- Active
- Inactive

The priority level is restricted to 1, 2, or 3 through a CHECK constraint.

### 3.6 food_donation

The `food_donation` table stores the main information about food donations.

Columns:

- `donation_id` - Primary key and unique donation identifier.
- `donor_user_id` - References a registered donor account.
- `donor_temp_id` - References a temporary donor account.
- `total_quantity` - Total quantity of food donated.
- `remaining_quantity` - Quantity remaining for allocation.
- `pincode` - Donation location pincode.
- `latitude` - Donation location latitude.
- `longitude` - Donation location longitude.
- `donation_token` - Unique donation token.
- `status` - Current donation status.
- `created_at` - Record creation timestamp.

Supported donation statuses:

- Open
- PartiallyAllocated
- Completed
- Expired

Important constraints:

- `donation_token` is unique.
- `total_quantity` must be greater than zero.
- `remaining_quantity` cannot be negative.
- Latitude and longitude must be present according to the CHECK constraint.
- `donor_user_id` references `registered_user(user_id)`.
- `donor_temp_id` references `temporary_user(temp_user_id)`.

### 3.7 food_item

The `food_item` table stores individual food items belonging to a donation.

Columns:

- `donation_id` - References the associated donation.
- `item_no` - Item number within the donation.
- `food_name` - Name of the food item.
- `food_category` - Food category.
- `quantity` - Original quantity of the item.
- `remaining_quantity` - Quantity remaining.
- `meal_type` - Type of meal.
- `cooked_time` - Date and time when the food was cooked.
- `safe_until` - Food safety expiry time.

Supported meal types:

- Breakfast
- Lunch
- Dinner
- Any

Primary key:

The table uses a composite primary key consisting of `donation_id` and `item_no`.

Important constraints:

- `donation_id` references `food_donation(donation_id)`.
- `quantity` must be greater than zero.
- `remaining_quantity` cannot be negative.
- `safe_until` must be later than `cooked_time`.

### 3.8 request

The `request` table stores food requests submitted by receivers.

Columns:

- `request_id` - Primary key and unique request identifier.
- `receiver_user_id` - References a registered receiver account.
- `receiver_temp_id` - References a temporary receiver account.
- `required_date` - Date when food is required.
- `meal_preference` - Preferred meal type.
- `total_quantity_requested` - Total requested quantity.
- `quantity_allocated` - Quantity already allocated.
- `remaining_required` - Quantity still required.
- `urgency_level` - Request urgency.
- `partial_flag` - Indicates partial-allocation preference.
- `priority_score` - Request priority score.
- `status` - Current request status.
- `created_at` - Record creation timestamp.

Supported meal preferences:

- Breakfast
- Lunch
- Dinner
- Any

Supported urgency levels:

- High
- Medium
- Low

Supported request statuses:

- Pending
- Partial
- Fulfilled
- Cancelled

Important constraints:

- `total_quantity_requested` must be greater than zero.
- `remaining_required` cannot be negative.
- `receiver_user_id` references `registered_user(user_id)`.
- `receiver_temp_id` references `temporary_user(temp_user_id)`.

### 3.9 allocation

The `allocation` table stores food allocation records connecting food items with receiver requests.

Columns:

- `allocation_id` - Primary key and unique allocation identifier.
- `donation_id` - References the donation containing the food item.
- `item_no` - Identifies the food item within the donation.
- `request_id` - References the receiver request.
- `allocated_quantity` - Quantity allocated.
- `status` - Allocation status.
- `allocation_time` - Allocation timestamp.

Supported allocation statuses:

- Accepted
- Completed
- Cancelled

Important constraints:

- `allocation_id` is the primary key.
- The combination of `donation_id` and `item_no` references the corresponding food item.
- `request_id` references `request(request_id)`.
- `allocated_quantity` must be greater than zero.
- A unique constraint exists on `donation_id`, `item_no`, `request_id`, and `status`.

### 3.10 pincode_geo

The `pincode_geo` table stores geographical information associated with Indian pincodes.

Columns:

- `pincode` - Primary key and six-character pincode.
- `district` - District name.
- `state` - State name.
- `latitude` - Geographical latitude.
- `longitude` - Geographical longitude.

Indexes:

- Primary key on `pincode`.
- Index on `state`.
- Index on `district`.

The primary key ensures that only one record is stored for each pincode.

## 4. Database Relationships

The database uses primary keys and foreign keys to maintain relationships between its tables.

The main relationships are:

- `person` is referenced by `registered_user`.
- `person` is referenced by `temporary_user`.
- `person` is referenced by `donor_profile`.
- `person` is referenced by `receiver_profile`.
- `registered_user` can be referenced by `food_donation` as a donor.
- `temporary_user` can be referenced by `food_donation` as a donor.
- `food_donation` can contain multiple `food_item` records.
- `registered_user` can be referenced by `request` as a receiver.
- `temporary_user` can be referenced by `request` as a receiver.
- `food_item` can be referenced by `allocation`.
- `request` can be referenced by `allocation`.

The `food_item` table uses a composite primary key consisting of `donation_id` and `item_no`.

The `allocation` table uses a composite foreign key to reference the corresponding food item.

## 5. Primary Keys and Constraints

The database uses the following integrity mechanisms:

- Primary keys identify individual records.
- Foreign keys maintain relationships between tables.
- Unique constraints prevent duplicate values in selected columns and combinations.
- CHECK constraints validate quantities, priority levels, coordinates, and food safety times.
- Indexes support selected lookup operations.
- InnoDB provides relational database and transaction support.

The exact foreign-key deletion and update rules are defined in the SQL schema file.

## 6. Database Hosting and Configuration

The MySQL database is hosted on Aiven.

The Flask application connects to the database using environment variables.

The required database configuration variables are:

- `DB_HOST` - MySQL server hostname.
- `DB_PORT` - MySQL server port.
- `DB_USER` - Database username.
- `DB_PASSWORD` - Database password.
- `DB_NAME` - Database name.

The application uses the database name `food_system`.

Actual database credentials must not be included in project documentation or committed to GitHub.

## 7. Database Schema Reference

The SQL schema reference is maintained in:

`database/food_system_structure.sql`

The file contains:

- Table definitions.
- Column definitions.
- Primary keys.
- Foreign keys.
- Unique constraints.
- CHECK constraints.
- Indexes.

The available SQL file is a schema-only export from a local MySQL 8.0.44 database dated October 21, 2026.

It does not contain a full backup of production records.

Important warning:

The SQL file contains `DROP TABLE IF EXISTS` statements. Executing it can remove existing tables and their data.

Do not execute this file against the production database without reviewing the script and taking a verified backup.

## 8. Pincode Dataset

The source geographical dataset is maintained in:

`data/pincode_geo.csv`

The CSV contains the following columns:

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

The database table `pincode_geo` uses `pincode` as its primary key and stores one geographical record per pincode.

## 9. Backup and Maintenance

The SQL schema file in the repository is maintained for reference and database setup.

A separate full database backup containing actual records should be maintained privately and securely.

Recommended maintenance practices:

- Take a database backup before making schema changes.
- Verify backups before relying on them.
- Do not commit production credentials.
- Do not commit private database records.
- Review SQL scripts before executing them.
- Keep production database credentials outside the source repository.

## 10. Summary

The `food_system` database supports the main operations of the Food Redistribution Network.

Its ten tables manage personal information, registered and temporary users, donor and receiver profiles, food donations, individual food items, receiver requests, allocation records, and pincode-based geographical information.