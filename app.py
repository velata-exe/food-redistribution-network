from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import uuid
import math
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

if not app.secret_key:
    raise RuntimeError("FLASK_SECRET is missing. Set it in your environment.")


# ---------------- DB Helpers ----------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        connection_timeout=10,
        ssl_disabled=False,
    )


def lookup_lat_lng_by_pincode(pincode: str):
    pincode = (pincode or "").strip()
    if len(pincode) != 6 or not pincode.isdigit():
        return None

    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT latitude, longitude
            FROM pincode_geo
            WHERE pincode=%s
            LIMIT 1
        """, (pincode,))
        return cur.fetchone()
    finally:
        cur.close()
        db.close()


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def estimate_travel_minutes(distance_km, avg_speed_kmph=30.0):
    if avg_speed_kmph <= 0:
        avg_speed_kmph = 30.0
    hours = distance_km / avg_speed_kmph
    return int(math.ceil(hours * 60))


def current_identity():
    if session.get("user_id"):
        return ("registered", session["user_id"])
    if session.get("temp_user_id"):
        return ("temp", session["temp_user_id"])
    return (None, None)


def get_person_coords_for_registered(user_id):
    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT p.latitude, p.longitude, p.pincode
            FROM registered_user ru
            JOIN person p ON ru.person_id = p.person_id
            WHERE ru.user_id=%s
        """, (user_id,))
        return cur.fetchone()
    finally:
        cur.close()
        db.close()


def get_current_user_pincode(kind, ident):
    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    try:
        if kind == "registered":
            cur.execute("""
                SELECT p.pincode
                FROM registered_user ru
                JOIN person p ON ru.person_id = p.person_id
                WHERE ru.user_id=%s
            """, (ident,))
        else:
            cur.execute("""
                SELECT p.pincode
                FROM temporary_user tu
                JOIN person p ON tu.person_id = p.person_id
                WHERE tu.temp_user_id=%s
            """, (ident,))
        row = cur.fetchone()
        return row["pincode"] if row and row.get("pincode") else ""
    finally:
        cur.close()
        db.close()


def get_donor_allocations(kind, ident):
    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    try:
        if kind == "registered":
            cur.execute("""
                SELECT
                    a.donation_id,
                    fi.food_name,
                    p.name AS receiver_name,
                    rp.receiver_category,
                    a.allocated_quantity,
                    a.status AS allocation_status,
                    fi.remaining_quantity
                FROM allocation a
                JOIN food_item fi
                    ON a.donation_id = fi.donation_id
                   AND a.item_no = fi.item_no
                JOIN request r
                    ON a.request_id = r.request_id
                LEFT JOIN registered_user ru
                    ON r.receiver_user_id = ru.user_id
                LEFT JOIN temporary_user tu
                    ON r.receiver_temp_id = tu.temp_user_id
                JOIN person p
                    ON p.person_id = COALESCE(ru.person_id, tu.person_id)
                JOIN receiver_profile rp
                    ON rp.person_id = p.person_id
                JOIN food_donation fd
                    ON fd.donation_id = a.donation_id
                WHERE fd.donor_user_id = %s
                  AND a.status = 'Accepted'
                ORDER BY a.allocation_time DESC
            """, (ident,))
        else:
            cur.execute("""
                SELECT
                    a.donation_id,
                    fi.food_name,
                    p.name AS receiver_name,
                    rp.receiver_category,
                    a.allocated_quantity,
                    a.status AS allocation_status,
                    fi.remaining_quantity
                FROM allocation a
                JOIN food_item fi
                    ON a.donation_id = fi.donation_id
                   AND a.item_no = fi.item_no
                JOIN request r
                    ON a.request_id = r.request_id
                LEFT JOIN registered_user ru
                    ON r.receiver_user_id = ru.user_id
                LEFT JOIN temporary_user tu
                    ON r.receiver_temp_id = tu.temp_user_id
                JOIN person p
                    ON p.person_id = COALESCE(ru.person_id, tu.person_id)
                JOIN receiver_profile rp
                    ON rp.person_id = p.person_id
                JOIN food_donation fd
                    ON fd.donation_id = a.donation_id
                WHERE fd.donor_temp_id = %s
                  AND a.status = 'Accepted'
                ORDER BY a.allocation_time DESC
            """, (ident,))

        return cur.fetchall()

    finally:
        cur.close()
        db.close()


# ---------------- Routes ----------------
@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("landing"))


# ---------------- Signup ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    pincode = request.form.get("pincode", "").strip()
    role = request.form.get("role")
    account_type = request.form.get("account_type")
    receiver_category = request.form.get("receiver_category", "NGO")
    donor_category = request.form.get("donor_category", "Individual")

    if role not in ("Donor", "Receiver") or account_type not in ("Permanent", "Temporary"):
        flash("Please choose a valid role and account type.", "error")
        return redirect(url_for("signup"))

    if receiver_category not in ("NGO", "ChildrenHome", "OldAgeHome", "Individual"):
        flash("Please choose a valid receiver category.", "error")
        return redirect(url_for("signup"))

    if donor_category not in ("Individual", "Restaurant", "Hotel", "Caterer", "Organization"):
        flash("Please choose a valid donor category.", "error")
        return redirect(url_for("signup"))

    if not (name and phone and pincode and role and account_type):
        flash("Missing required signup fields.", "error")
        return redirect(url_for("signup"))

    if not phone.isdigit() or len(phone) < 8 or len(phone) > 15:
        flash("Invalid phone number format.", "error")
        return redirect(url_for("signup"))

    geo = lookup_lat_lng_by_pincode(pincode)
    if not geo:
        flash("Invalid/unsupported pincode.", "error")
        return redirect(url_for("signup"))

    latitude = geo["latitude"]
    longitude = geo["longitude"]

    if receiver_category in ["ChildrenHome", "OldAgeHome"]:
        priority_level = 3
    elif receiver_category == "NGO":
        priority_level = 2
    else:
        priority_level = 1

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    db = get_db_connection()
    cur = db.cursor()

    try:
        db.start_transaction()

        cur.execute("""
            INSERT INTO person (name, phone, pincode, latitude, longitude)
            VALUES (%s,%s,%s,%s,%s)
        """, (name, phone, pincode, latitude, longitude))
        person_id = cur.lastrowid

        if account_type == "Permanent":
            if not (username and password):
                db.rollback()
                flash("Permanent account needs username and password.", "error")
                return redirect(url_for("signup"))

            if len(password) < 6:
                db.rollback()
                flash("Password must be at least 6 characters.", "error")
                return redirect(url_for("signup"))

            password_hash = generate_password_hash(password)

            cur.execute("""
                INSERT INTO registered_user (person_id, username, password_hash, role)
                VALUES (%s,%s,%s,%s)
            """, (person_id, username, password_hash, role))

            if role == "Donor":
                cur.execute("""
                    INSERT INTO donor_profile (person_id, donor_category)
                    VALUES (%s,%s)
                """, (person_id, donor_category))
            else:
                cur.execute("""
                    INSERT INTO receiver_profile (person_id, receiver_category, priority_level, status)
                    VALUES (%s,%s,%s,'Active')
                """, (person_id, receiver_category, int(priority_level)))

            db.commit()
            flash("Signup successful. Please login.", "success")
            return redirect(url_for("login"))

        else:
            temp_user_id = str(uuid.uuid4())
            tracking_id = f"TMP-{uuid.uuid4().hex[:10].upper()}"

            cur.execute("""
                INSERT INTO temporary_user (temp_user_id, person_id, tracking_id)
                VALUES (%s,%s,%s)
            """, (temp_user_id, person_id, tracking_id))

            if role == "Donor":
                cur.execute("""
                    INSERT INTO donor_profile (person_id, donor_category)
                    VALUES (%s,%s)
                """, (person_id, donor_category))
            else:
                cur.execute("""
                    INSERT INTO receiver_profile (person_id, receiver_category, priority_level, status)
                    VALUES (%s,%s,%s,'Active')
                """, (person_id, receiver_category, int(priority_level)))

            db.commit()

            session.clear()
            session["temp_user_id"] = temp_user_id
            session["role"] = role
            session["tracking_id"] = tracking_id

            flash(f"One-time signup successful. Tracking ID: {tracking_id}", "success")
            return redirect(url_for("dashboard"))

    except Error as e:
        db.rollback()
        app.logger.exception("Database operation failed")
        flash("A database error occurred. Please try again.", "error")
        return redirect(url_for("signup"))

    finally:
        cur.close()
        db.close()


# ---------------- Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT user_id, password_hash, role
            FROM registered_user
            WHERE username=%s
        """, (username,))
        user = cur.fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["user_id"]
        session["role"] = user["role"]

        flash("Login successful.", "success")
        return redirect(url_for("dashboard"))
    finally:
        cur.close()
        db.close()


# ---------------- Dashboard ----------------
@app.route("/dashboard")
def dashboard():
    kind, ident = current_identity()

    if not kind:
        return redirect(url_for("landing"))

    role = session.get("role")

    if role not in ("Donor", "Receiver"):
        flash("Invalid session role. Please login again.", "error")
        return redirect(url_for("logout"))

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    try:
        display_name = "User"
        account_phone = "-"
        account_pincode = "-"

        if kind == "registered":
            cur.execute("""
                SELECT p.name, p.phone, p.pincode
                FROM registered_user ru
                JOIN person p ON ru.person_id = p.person_id
                WHERE ru.user_id = %s
            """, (ident,))
        else:
            cur.execute("""
                SELECT p.name, p.phone, p.pincode
                FROM temporary_user tu
                JOIN person p ON tu.person_id = p.person_id
                WHERE tu.temp_user_id = %s
            """, (ident,))

        row = cur.fetchone()

        if row:
            display_name = row.get("name") or "User"
            account_phone = row.get("phone") or "-"
            account_pincode = row.get("pincode") or "-"

        current_donations = []
        past_donations = []

        current_requests = []
        past_requests = []

        donor_allocations = []

        stats_total_donations = 0
        stats_active_donations = 0

        stats_total_requests = 0
        stats_active_requests = 0
        stats_fulfilled_requests = 0

        # =========================================================
        # DONOR DASHBOARD
        # =========================================================
        if role == "Donor":

            # Mark a donation Expired when none of its remaining items are still
            # within their safe_until window. This preserves partially allocated
            # donations when at least one usable item remains.
            if kind == "registered":
                cur.execute("""
                    UPDATE food_donation fd
                    SET fd.status = 'Expired'
                    WHERE fd.donor_user_id = %s
                      AND fd.status IN ('Open', 'PartiallyAllocated')
                      AND NOT EXISTS (
                          SELECT 1
                          FROM food_item fi
                          WHERE fi.donation_id = fd.donation_id
                            AND fi.remaining_quantity > 0
                            AND fi.safe_until > NOW()
                      )
                """, (ident,))
            else:
                cur.execute("""
                    UPDATE food_donation fd
                    SET fd.status = 'Expired'
                    WHERE fd.donor_temp_id = %s
                      AND fd.status IN ('Open', 'PartiallyAllocated')
                      AND NOT EXISTS (
                          SELECT 1
                          FROM food_item fi
                          WHERE fi.donation_id = fd.donation_id
                            AND fi.remaining_quantity > 0
                            AND fi.safe_until > NOW()
                      )
                """, (ident,))
            db.commit()

            if kind == "registered":
                cur.execute("""
                    SELECT fd.donation_id, fd.created_at, fd.status,
                           fd.remaining_quantity, fd.total_quantity
                    FROM food_donation fd
                    WHERE fd.donor_user_id = %s
                      AND fd.status IN ('Open', 'PartiallyAllocated')
                      AND EXISTS (
                          SELECT 1
                          FROM food_item fi
                          WHERE fi.donation_id = fd.donation_id
                            AND fi.remaining_quantity > 0
                            AND fi.safe_until > NOW()
                      )
                    ORDER BY fd.created_at DESC
                    LIMIT 5
                """, (ident,))
            else:
                cur.execute("""
                    SELECT fd.donation_id, fd.created_at, fd.status,
                           fd.remaining_quantity, fd.total_quantity
                    FROM food_donation fd
                    WHERE fd.donor_temp_id = %s
                      AND fd.status IN ('Open', 'PartiallyAllocated')
                      AND EXISTS (
                          SELECT 1
                          FROM food_item fi
                          WHERE fi.donation_id = fd.donation_id
                            AND fi.remaining_quantity > 0
                            AND fi.safe_until > NOW()
                      )
                    ORDER BY fd.created_at DESC
                    LIMIT 5
                """, (ident,))

            current_donations = cur.fetchall()

            # ---- Past donations: one row per receiver with allocated quantity ----
            if kind == "registered":
                cur.execute("""
                    SELECT
                        fd.donation_id,
                        fd.created_at,
                        fd.status,
                        p.name AS receiver_name,
                        a.allocated_quantity
                    FROM food_donation fd
                    LEFT JOIN allocation a
                        ON fd.donation_id = a.donation_id
                       AND a.status IN ('Accepted', 'Completed')
                    LEFT JOIN request r
                        ON a.request_id = r.request_id
                    LEFT JOIN registered_user ru
                        ON r.receiver_user_id = ru.user_id
                    LEFT JOIN temporary_user tu
                        ON r.receiver_temp_id = tu.temp_user_id
                    LEFT JOIN person p
                        ON p.person_id = COALESCE(ru.person_id, tu.person_id)
                    WHERE fd.donor_user_id = %s
                    AND fd.status IN ('PartiallyAllocated', 'Completed', 'Expired')
                    ORDER BY fd.created_at DESC, a.allocation_time DESC
                    LIMIT 5
                """, (ident,))
            else:
                cur.execute("""
                    SELECT
                        fd.donation_id,
                        fd.created_at,
                        fd.status,
                        p.name AS receiver_name,
                        a.allocated_quantity
                    FROM food_donation fd
                    LEFT JOIN allocation a
                        ON fd.donation_id = a.donation_id
                       AND a.status IN ('Accepted', 'Completed')
                    LEFT JOIN request r
                        ON a.request_id = r.request_id
                    LEFT JOIN registered_user ru
                        ON r.receiver_user_id = ru.user_id
                    LEFT JOIN temporary_user tu
                        ON r.receiver_temp_id = tu.temp_user_id
                    LEFT JOIN person p
                        ON p.person_id = COALESCE(ru.person_id, tu.person_id)
                    WHERE fd.donor_temp_id = %s
                    AND fd.status IN ('PartiallyAllocated', 'Completed', 'Expired')
                    ORDER BY fd.created_at DESC, a.allocation_time DESC
                    LIMIT 5
                """, (ident,))

            past_donations = cur.fetchall()

            donor_allocations = get_donor_allocations(kind, ident)

            if kind == "registered":
                cur.execute("""
                    SELECT
                        COUNT(*) AS total_donations,
                        SUM(CASE WHEN status IN ('Open', 'PartiallyAllocated') THEN 1 ELSE 0 END) AS active_donations
                    FROM food_donation
                    WHERE donor_user_id = %s
                """, (ident,))
            else:
                cur.execute("""
                    SELECT
                        COUNT(*) AS total_donations,
                        SUM(CASE WHEN status IN ('Open', 'PartiallyAllocated') THEN 1 ELSE 0 END) AS active_donations
                    FROM food_donation
                    WHERE donor_temp_id = %s
                """, (ident,))

            stat_row = cur.fetchone() or {}
            stats_total_donations = stat_row.get("total_donations") or 0
            stats_active_donations = stat_row.get("active_donations") or 0

        # =========================================================
        # RECEIVER DASHBOARD
        # =========================================================
        if role == "Receiver":
            # Both registered and temporary receivers own requests.
            owner_column = "receiver_user_id" if kind == "registered" else "receiver_temp_id"

            # Auto-cancel requests whose required date has passed.
            cur.execute(f"""
                UPDATE request
                SET status = 'Cancelled'
                WHERE {owner_column} = %s
                  AND required_date < CURDATE()
                  AND status IN ('Pending', 'Partial')
            """, (ident,))
            db.commit()

            # Current requests (latest 5)
            cur.execute(f"""
                SELECT request_id, required_date, created_at, status,
                       remaining_required, urgency_level, meal_preference
                FROM request
                WHERE {owner_column} = %s
                  AND required_date >= CURDATE()
                  AND status IN ('Pending', 'Partial')
                ORDER BY required_date ASC, created_at DESC
                LIMIT 5
            """, (ident,))
            current_requests = cur.fetchall()

            # Past/closed requests, including expired and cancelled requests.
            cur.execute(f"""
                SELECT
                    r.request_id,
                    r.required_date,
                    r.created_at,
                    r.status,
                    COALESCE(SUM(a.allocated_quantity), 0) AS received_quantity,
                    CASE
                        WHEN COUNT(DISTINCT dp.name) = 0 THEN '-'
                        WHEN COUNT(DISTINCT dp.name) = 1 THEN MAX(dp.name)
                        ELSE 'Multiple donors'
                    END AS donor_name
                FROM request r
                LEFT JOIN allocation a
                    ON r.request_id = a.request_id
                   AND a.status IN ('Accepted', 'Completed')
                LEFT JOIN food_donation fd
                    ON a.donation_id = fd.donation_id
                LEFT JOIN registered_user dru
                    ON fd.donor_user_id = dru.user_id
                LEFT JOIN temporary_user dtu
                    ON fd.donor_temp_id = dtu.temp_user_id
                LEFT JOIN person dp
                    ON dp.person_id = COALESCE(dru.person_id, dtu.person_id)
                WHERE r.{owner_column} = %s
                  AND NOT (r.required_date >= CURDATE()
                           AND r.status IN ('Pending', 'Partial'))
                GROUP BY r.request_id, r.required_date, r.created_at, r.status
                ORDER BY r.required_date DESC, r.created_at DESC
                LIMIT 5
            """, (ident,))
            past_requests = cur.fetchall()

            # Receiver stats include registered and temporary accounts.
            cur.execute(f"""
                SELECT
                    COUNT(*) AS total_requests,
                    SUM(CASE WHEN required_date >= CURDATE()
                              AND status IN ('Pending', 'Partial')
                             THEN 1 ELSE 0 END) AS active_requests,
                    SUM(CASE WHEN status = 'Fulfilled'
                             THEN 1 ELSE 0 END) AS fulfilled_requests
                FROM request
                WHERE {owner_column} = %s
            """, (ident,))
            stat_row = cur.fetchone() or {}
            stats_total_requests = stat_row.get("total_requests") or 0
            stats_active_requests = stat_row.get("active_requests") or 0
            stats_fulfilled_requests = stat_row.get("fulfilled_requests") or 0

        return render_template(
            "dashboard.html",
            role=role,
            kind=kind,
            display_name=display_name,
            account_phone=account_phone,
            account_pincode=account_pincode,
            stats_total_donations=stats_total_donations,
            stats_active_donations=stats_active_donations,
            stats_total_requests=stats_total_requests,
            stats_active_requests=stats_active_requests,
            stats_fulfilled_requests=stats_fulfilled_requests,
            current_donations=current_donations,
            past_donations=past_donations,
            donor_allocations=donor_allocations,
            current_requests=current_requests,
            past_requests=past_requests,
        )

    finally:
        cur.close()
        db.close()


# ---------------- Edit Profile ----------------
@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():
    kind, ident = current_identity()
    if not kind:
        flash("Please login/signup first.", "error")
        return redirect(url_for("landing"))

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    try:
        if kind == "registered":
            cur.execute("""
                SELECT ru.user_id, ru.username, ru.role, p.person_id, p.name, p.phone, p.pincode
                FROM registered_user ru
                JOIN person p ON ru.person_id = p.person_id
                WHERE ru.user_id=%s
            """, (ident,))
        else:
            cur.execute("""
                SELECT tu.temp_user_id, p.person_id, p.name, p.phone, p.pincode
                FROM temporary_user tu
                JOIN person p ON tu.person_id = p.person_id
                WHERE tu.temp_user_id=%s
            """, (ident,))

        profile = cur.fetchone()
        if not profile:
            flash("Profile not found.", "error")
            return redirect(url_for("dashboard"))

        if request.method == "GET":
            return render_template("edit_profile.html", kind=kind, profile=profile)

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        pincode = request.form.get("pincode", "").strip()

        if not (name and phone and pincode):
            flash("Name, phone, and pincode are required.", "error")
            return redirect(url_for("edit_profile"))

        geo = lookup_lat_lng_by_pincode(pincode)
        if not geo:
            flash("Invalid/unsupported pincode.", "error")
            return redirect(url_for("edit_profile"))

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        db.start_transaction()

        cur.execute("""
            UPDATE person
            SET name=%s, phone=%s, pincode=%s, latitude=%s, longitude=%s
            WHERE person_id=%s
        """, (name, phone, pincode, geo["latitude"], geo["longitude"], profile["person_id"]))

        if kind == "registered" and (current_password or new_password or confirm_password):
            if not (current_password and new_password and confirm_password):
                db.rollback()
                flash("To change password, fill current, new, and confirm password.", "error")
                return redirect(url_for("edit_profile"))

            if new_password != confirm_password:
                db.rollback()
                flash("New password and confirm password do not match.", "error")
                return redirect(url_for("edit_profile"))

            if len(new_password) < 6:
                db.rollback()
                flash("New password must be at least 6 characters.", "error")
                return redirect(url_for("edit_profile"))

            cur.execute("SELECT password_hash FROM registered_user WHERE user_id=%s", (ident,))
            row = cur.fetchone()
            if not row or not check_password_hash(row["password_hash"], current_password):
                db.rollback()
                flash("Current password is incorrect.", "error")
                return redirect(url_for("edit_profile"))

            cur.execute("""
                UPDATE registered_user
                SET password_hash=%s
                WHERE user_id=%s
            """, (generate_password_hash(new_password), ident))

        db.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("dashboard"))

    except Error as e:
        db.rollback()
        app.logger.exception("Database operation failed")
        flash("A database error occurred. Please try again.", "error")
        return redirect(url_for("edit_profile"))
    finally:
        cur.close()
        db.close()


# ---------------- Donate ----------------
@app.route("/donate", methods=["GET", "POST"])
def donate():
    kind, ident = current_identity()
    if not kind:
        flash("Please signup/login first.", "error")
        return redirect(url_for("landing"))

    if request.method == "GET":
        donation_token = str(uuid.uuid4())
        default_pincode = get_current_user_pincode(kind, ident)
        return render_template(
            "donate.html",
            donation_token=donation_token,
            default_pincode=default_pincode
        )

    donation_token = request.form.get("donation_token")
    pincode = request.form.get("pincode", "").strip()

    if not donation_token:
        flash("Missing donation token.", "error")
        return redirect(url_for("donate"))

    geo = lookup_lat_lng_by_pincode(pincode)
    if not geo:
        flash("Invalid/unsupported pincode.", "error")
        return redirect(url_for("donate"))

    latitude = geo["latitude"]
    longitude = geo["longitude"]

    items = []
    for idx in [1, 2, 3]:
        food_name = request.form.get(f"food_name_{idx}", "").strip()
        qty = request.form.get(f"quantity_{idx}", "").strip()
        cooked_time = request.form.get(f"cooked_time_{idx}", "").strip()
        safe_until = request.form.get(f"safe_until_{idx}", "").strip()
        meal_type = request.form.get(f"meal_type_{idx}", "Any").strip()
        category = request.form.get(f"food_category_{idx}", "").strip()

        if food_name and qty and cooked_time and safe_until:
            try:
                qty_int = int(qty)
                ct = datetime.fromisoformat(cooked_time)
                su = datetime.fromisoformat(safe_until)
                now = datetime.now()
                if qty_int <= 0 or ct > now or su <= now or su <= ct:
                    raise ValueError
            except Exception:
                flash(f"Invalid item {idx}.", "error")
                return redirect(url_for("donate"))

            if meal_type not in ["Breakfast", "Lunch", "Dinner", "Any"]:
                meal_type = "Any"

            items.append({
                "food_name": food_name,
                "food_category": category or None,
                "quantity": qty_int,
                "cooked_time": cooked_time,
                "safe_until": safe_until,
                "meal_type": meal_type,
            })

    if not items:
        flash("Add at least one food item.", "error")
        return redirect(url_for("donate"))

    total_qty = sum(i["quantity"] for i in items)

    db = get_db_connection()
    cur = db.cursor()

    try:
        cur.execute(
            "SELECT donation_id FROM food_donation WHERE donation_token=%s",
            (donation_token,)
        )
        if cur.fetchone():
            flash("Duplicate prevented: donation already submitted.", "warning")
            return redirect(url_for("dashboard"))

        if kind == "registered":
            cur.execute("""
                INSERT INTO food_donation (
                    donor_user_id, total_quantity, remaining_quantity,
                    pincode, latitude, longitude, donation_token, status
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,'Open')
            """, (ident, total_qty, total_qty, pincode, latitude, longitude, donation_token))
        else:
            cur.execute("""
                INSERT INTO food_donation (
                    donor_temp_id, total_quantity, remaining_quantity,
                    pincode, latitude, longitude, donation_token, status
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,'Open')
            """, (ident, total_qty, total_qty, pincode, latitude, longitude, donation_token))

        donation_id = cur.lastrowid

        item_no = 1
        for it in items:
            cur.execute("""
                INSERT INTO food_item (
                    donation_id, item_no, food_name, food_category,
                    quantity, remaining_quantity, meal_type,
                    cooked_time, safe_until
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                donation_id,
                item_no,
                it["food_name"],
                it["food_category"],
                it["quantity"],
                it["quantity"],
                it["meal_type"],
                it["cooked_time"],
                it["safe_until"]
            ))
            item_no += 1

        db.commit()
        flash("Donation submitted successfully.", "success")
        return redirect(url_for("dashboard"))

    except Error as e:
        db.rollback()
        app.logger.exception("Database operation failed")
        flash("A database error occurred. Please try again.", "error")
        return redirect(url_for("donate"))

    finally:
        cur.close()
        db.close()


# ---------------- Request ----------------
@app.route("/request", methods=["GET", "POST"])
def make_request():
    kind, ident = current_identity()
    if not kind:
        flash("Please signup/login first.", "error")
        return redirect(url_for("landing"))

    if session.get("role") != "Receiver":
        flash("Only receivers can request.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        default_pincode = get_current_user_pincode(kind, ident)
        if not default_pincode:
            flash("Please update your pincode before requesting.", "error")
            return redirect(url_for("edit_profile"))
        return render_template("request.html", default_pincode=default_pincode)

    required_date = request.form.get("required_date")
    meal_preference = request.form.get("meal_preference", "Any")
    urgency_level = request.form.get("urgency_level", "Medium")
    qty = request.form.get("quantity", "").strip()

    if not (required_date and qty):
        flash("Missing required fields.", "error")
        return redirect(url_for("make_request"))

    try:
        parsed_required_date = date.fromisoformat(required_date)
        if parsed_required_date < date.today():
            raise ValueError
    except (TypeError, ValueError):
        flash("Required date must be today or a future date.", "error")
        return redirect(url_for("make_request"))

    try:
        qty_int = int(qty)
        if qty_int <= 0:
            raise ValueError
    except Exception:
        flash("Quantity must be positive.", "error")
        return redirect(url_for("make_request"))

    if meal_preference not in ["Breakfast", "Lunch", "Dinner", "Any"]:
        meal_preference = "Any"
    if urgency_level not in ["High", "Medium", "Low"]:
        urgency_level = "Medium"

    db = get_db_connection()
    cur = db.cursor()
    try:
        if kind == "registered":
            cur.execute("""
                INSERT INTO request (receiver_user_id, required_date, meal_preference,
                                     total_quantity_requested, remaining_required, urgency_level, status)
                VALUES (%s,%s,%s,%s,%s,%s,'Pending')
            """, (ident, required_date, meal_preference, qty_int, qty_int, urgency_level))
        else:
            cur.execute("""
                INSERT INTO request (receiver_temp_id, required_date, meal_preference,
                                     total_quantity_requested, remaining_required, urgency_level, status)
                VALUES (%s,%s,%s,%s,%s,%s,'Pending')
            """, (ident, required_date, meal_preference, qty_int, qty_int, urgency_level))

        db.commit()
        flash("Request submitted successfully.", "success")
        return redirect(url_for("dashboard"))
    except Error as e:
        db.rollback()
        app.logger.exception("Database operation failed")
        flash("A database error occurred. Please try again.", "error")
        return redirect(url_for("make_request"))
    finally:
        cur.close()
        db.close()


# ---------------- Receiver Matches ----------------
@app.route("/receiver-matches")
def receiver_matches():
    kind, ident = current_identity()

    if not kind:
        flash("Please login first.", "error")
        return redirect(url_for("landing"))

    if session.get("role") != "Receiver":
        flash("Only receivers can view matches.", "error")
        return redirect(url_for("dashboard"))

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    try:
        if kind == "registered":
            cur.execute("""
                SELECT
                    r.request_id,
                    r.remaining_required,
                    r.meal_preference,
                    r.urgency_level,
                    p.latitude AS r_lat,
                    p.longitude AS r_lng
                FROM request r
                JOIN registered_user ru
                    ON r.receiver_user_id = ru.user_id
                JOIN person p
                    ON ru.person_id = p.person_id
                WHERE r.receiver_user_id = %s
                  AND r.remaining_required > 0
                  AND r.status IN ('Pending', 'Partial')
            """, (ident,))
        else:
            cur.execute("""
                SELECT
                    r.request_id,
                    r.remaining_required,
                    r.meal_preference,
                    r.urgency_level,
                    p.latitude AS r_lat,
                    p.longitude AS r_lng
                FROM request r
                JOIN temporary_user tu
                    ON r.receiver_temp_id = tu.temp_user_id
                JOIN person p
                    ON tu.person_id = p.person_id
                WHERE r.receiver_temp_id = %s
                  AND r.remaining_required > 0
                  AND r.status IN ('Pending', 'Partial')
            """, (ident,))

        requests = cur.fetchall()

        # FIXED: include donor name and donor phone
        cur.execute("""
            SELECT
                i.donation_id,
                i.item_no,
                i.food_name,
                i.food_category,
                i.meal_type,
                i.remaining_quantity,
                i.safe_until,
                d.latitude AS d_lat,
                d.longitude AS d_lng,
                d.status AS donation_status,
                dp.name AS donor_name,
                dp.phone AS donor_phone
            FROM food_item i
            JOIN food_donation d
                ON d.donation_id = i.donation_id
            LEFT JOIN registered_user dru
                ON d.donor_user_id = dru.user_id
            LEFT JOIN temporary_user dtu
                ON d.donor_temp_id = dtu.temp_user_id
            LEFT JOIN person dp
                ON dp.person_id = COALESCE(dru.person_id, dtu.person_id)
            WHERE i.remaining_quantity > 0
              AND i.safe_until > NOW()
              AND (
                    d.status IN ('Open', 'PartiallyAllocated')
                    OR (d.status = 'Completed' AND d.remaining_quantity > 0)
              )
        """)
        items = cur.fetchall()

        rows = []
        now = datetime.now()

        for r in requests:
            if r["r_lat"] is None or r["r_lng"] is None:
                continue

            for it in items:
                if it["d_lat"] is None or it["d_lng"] is None:
                    continue

                if r["meal_preference"] != "Any" and it["meal_type"] != "Any":
                    if r["meal_preference"] != it["meal_type"]:
                        continue

                dist = haversine_km(
                    float(it["d_lat"]), float(it["d_lng"]),
                    float(r["r_lat"]), float(r["r_lng"])
                )

                if dist > 20:
                    continue

                travel_min = estimate_travel_minutes(dist, 30.0)
                arrival = now + timedelta(minutes=travel_min + 15)

                if it["safe_until"] <= arrival:
                    continue

                suggested_qty = min(
                    r["remaining_required"],
                    it["remaining_quantity"]
                )

                if suggested_qty <= 0:
                    continue

                rows.append({
                    "request_id": r["request_id"],
                    "food_name": it["food_name"],
                    "food_category": it["food_category"],
                    "available": it["remaining_quantity"],
                    "distance": round(dist, 2),
                    "safe_until": it["safe_until"],
                    "donation_id": it["donation_id"],
                    "item_no": it["item_no"],
                    "suggested_qty": suggested_qty,
                    "donor_name": it["donor_name"],
                    "donor_phone": it["donor_phone"]
                })

        rows.sort(key=lambda x: (x["request_id"], x["distance"]))

        return render_template("receiver_matches.html", rows=rows)

    finally:
        cur.close()
        db.close()


# ---------------- Accept Match ----------------
@app.route("/accept-match", methods=["POST"])
def accept_match():
    kind, ident = current_identity()

    if not kind:
        flash("Please login first.", "error")
        return redirect(url_for("landing"))

    if session.get("role") != "Receiver":
        flash("Only receivers can accept matches.", "error")
        return redirect(url_for("dashboard"))

    donation_id = request.form.get("donation_id")
    item_no = request.form.get("item_no")
    request_id = request.form.get("request_id")
    qty = request.form.get("qty")

    try:
        donation_id = int(donation_id)
        item_no = int(item_no)
        request_id = int(request_id)
        qty = int(qty)
        if qty <= 0:
            raise ValueError
    except Exception:
        flash("Invalid input.", "error")
        return redirect(url_for("receiver_matches"))

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    try:
        db.start_transaction()

        if kind == "registered":
            cur.execute("""
                SELECT request_id, remaining_required, status, required_date
                FROM request
                WHERE request_id = %s AND receiver_user_id = %s
                FOR UPDATE
            """, (request_id, ident))
        else:
            cur.execute("""
                SELECT request_id, remaining_required, status, required_date
                FROM request
                WHERE request_id = %s AND receiver_temp_id = %s
                FOR UPDATE
            """, (request_id, ident))

        req = cur.fetchone()
        if not req:
            db.rollback()
            flash("Request not found.", "error")
            return redirect(url_for("receiver_matches"))

        if req["status"] in ("Fulfilled", "Cancelled"):
            db.rollback()
            flash("Request is no longer active.", "warning")
            return redirect(url_for("receiver_matches"))

        if req["required_date"] < date.today():
            cur.execute("""
                UPDATE request SET status = 'Cancelled'
                WHERE request_id = %s
            """, (request_id,))
            db.commit()
            flash("This request has expired and was cancelled.", "warning")
            return redirect(url_for("receiver_matches"))

        cur.execute("""
            SELECT remaining_quantity, safe_until
            FROM food_item
            WHERE donation_id = %s AND item_no = %s
            FOR UPDATE
        """, (donation_id, item_no))
        item = cur.fetchone()

        if not item:
            db.rollback()
            flash("Food item not available.", "error")
            return redirect(url_for("receiver_matches"))

        if item["remaining_quantity"] <= 0:
            db.rollback()
            flash("Food item not available.", "error")
            return redirect(url_for("receiver_matches"))

        if item["safe_until"] <= datetime.now():
            db.rollback()
            flash("Food item has expired and can no longer be accepted.", "warning")
            return redirect(url_for("receiver_matches"))

        # Lock the parent donation row and use its current quantity/status.
        cur.execute("""
            SELECT remaining_quantity, status
            FROM food_donation
            WHERE donation_id = %s
            FOR UPDATE
        """, (donation_id,))
        donation = cur.fetchone()

        if (
            not donation
            or donation["remaining_quantity"] <= 0
            or donation["status"] not in ("Open", "PartiallyAllocated")
        ):
            db.rollback()
            flash("Donation is no longer available.", "warning")
            return redirect(url_for("receiver_matches"))

        max_allowed = min(
            int(item["remaining_quantity"]),
            int(req["remaining_required"]),
            int(donation["remaining_quantity"])
        )
        if qty > max_allowed:
            db.rollback()
            flash(
                f"Quantity too large. You can accept between 1 and {max_allowed} units.",
                "warning"
            )
            return redirect(url_for("receiver_matches"))

        alloc_qty = qty
        new_donation_remaining = int(donation["remaining_quantity"]) - alloc_qty
        new_donation_status = (
            "Completed" if new_donation_remaining == 0 else "PartiallyAllocated"
        )

        if alloc_qty <= 0:
            db.rollback()
            flash("Nothing to allocate.", "warning")
            return redirect(url_for("receiver_matches"))

        # The uq_alloc_once index permits only one Accepted row for each
        # donation/item/request combination. Add to that row when it exists.
        cur.execute("""
            SELECT allocated_quantity
            FROM allocation
            WHERE donation_id = %s
              AND item_no = %s
              AND request_id = %s
              AND status = 'Accepted'
            FOR UPDATE
        """, (donation_id, item_no, request_id))
        existing_allocation = cur.fetchone()

        if existing_allocation:
            cur.execute("""
                UPDATE allocation
                SET allocated_quantity = allocated_quantity + %s
                WHERE donation_id = %s
                  AND item_no = %s
                  AND request_id = %s
                  AND status = 'Accepted'
            """, (alloc_qty, donation_id, item_no, request_id))
        else:
            cur.execute("""
                INSERT INTO allocation
                (donation_id, item_no, request_id, allocated_quantity, status)
                VALUES (%s, %s, %s, %s, 'Accepted')
            """, (donation_id, item_no, request_id, alloc_qty))

        cur.execute("""
            UPDATE food_item
            SET remaining_quantity = remaining_quantity - %s
            WHERE donation_id = %s AND item_no = %s
        """, (alloc_qty, donation_id, item_no))

        # Set status from the explicitly calculated new quantity. This avoids
        # MySQL's left-to-right UPDATE assignment behavior marking a donation
        # Completed while units still remain.
        cur.execute("""
            UPDATE food_donation
            SET remaining_quantity = %s,
                status = %s
            WHERE donation_id = %s
        """, (new_donation_remaining, new_donation_status, donation_id))

        new_remaining = req["remaining_required"] - alloc_qty
        new_status = "Fulfilled" if new_remaining <= 0 else "Partial"
        new_partial_flag = new_remaining > 0

        cur.execute("""
            UPDATE request
            SET quantity_allocated = quantity_allocated + %s,
                remaining_required = %s,
                status = %s,
                partial_flag = %s,
                priority_score = CASE
                    WHEN %s > 0 THEN priority_score + 1
                    ELSE priority_score
                END
            WHERE request_id = %s
        """, (
            alloc_qty,
            new_remaining,
            new_status,
            new_partial_flag,
            new_remaining,
            request_id
        ))

        db.commit()
        flash("Match accepted successfully.", "success")
        return redirect(url_for("receiver_matches"))

    except Error as e:
        db.rollback()
        app.logger.exception("Database operation failed")
        flash("A database error occurred. Please try again.", "error")
        return redirect(url_for("receiver_matches"))

    finally:
        cur.close()
        db.close()


# ---------------- Donor Allocations ----------------
@app.route("/donor-allocations")
def donor_allocations_page():
    kind, ident = current_identity()
    if not kind:
        flash("Please login first.", "error")
        return redirect(url_for("landing"))

    if session.get("role") != "Donor":
        flash("Only donors can view approved allocations.", "error")
        return redirect(url_for("dashboard"))

    rows = get_donor_allocations(kind, ident)
    return render_template("donor_allocations.html", rows=rows)

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)