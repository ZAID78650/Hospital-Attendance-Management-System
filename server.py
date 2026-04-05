"""
MediCore HMS — Flask Backend (Full Edition)
Tables: admissions, patients, doctors, wards, billing, appointments, medications
Auto-creates hospital.db with schema + seed data on first run.
Run: python3 server.py  →  http://localhost:8080
"""

import sqlite3, os, random
from datetime import date, timedelta
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB       = os.path.join(BASE_DIR, "hospital.db")


# ══════════════════════════════════════════════════════════════
#  SCHEMA + SEED
# ══════════════════════════════════════════════════════════════

def init_db():
    conn = sqlite3.connect(DB)
    c    = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")

    # ── 1. doctors ────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            speciality TEXT    NOT NULL,
            phone      TEXT    NOT NULL,
            email      TEXT,
            available  INTEGER NOT NULL DEFAULT 1
        )
    """)

    # ── 2. wards ──────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS wards (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_name    TEXT    NOT NULL,
            bed_number   TEXT    NOT NULL UNIQUE,
            bed_type     TEXT    NOT NULL,
            rate_per_day INTEGER NOT NULL,
            occupied     INTEGER NOT NULL DEFAULT 0
        )
    """)

    # ── 3. patients ───────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            name              TEXT NOT NULL,
            age               INTEGER NOT NULL,
            gender            TEXT NOT NULL,
            phone             TEXT NOT NULL,
            address           TEXT NOT NULL,
            blood_group       TEXT,
            emergency_contact TEXT,
            created_at        TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── 4. admissions ─────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS admissions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id     INTEGER REFERENCES patients(id),
            name           TEXT    NOT NULL,
            age            INTEGER NOT NULL,
            gender         TEXT    NOT NULL,
            phone          TEXT    NOT NULL,
            address        TEXT    NOT NULL,
            disease        TEXT    NOT NULL,
            doctor         TEXT    NOT NULL,
            ward           TEXT    NOT NULL,
            bed            TEXT    NOT NULL,
            rate           INTEGER NOT NULL,
            adm_date       TEXT    NOT NULL,
            discharge_date TEXT,
            status         TEXT    NOT NULL DEFAULT 'Admitted',
            payment        TEXT    NOT NULL,
            notes          TEXT,
            created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── 5. billing ────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS billing (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_id     INTEGER NOT NULL REFERENCES admissions(id),
            patient_name     TEXT    NOT NULL,
            bed_charges      INTEGER NOT NULL DEFAULT 0,
            medicine_charges INTEGER NOT NULL DEFAULT 0,
            lab_charges      INTEGER NOT NULL DEFAULT 0,
            doctor_charges   INTEGER NOT NULL DEFAULT 0,
            other_charges    INTEGER NOT NULL DEFAULT 0,
            total            INTEGER NOT NULL DEFAULT 0,
            payment_mode     TEXT    NOT NULL DEFAULT 'Cash',
            payment_status   TEXT    NOT NULL DEFAULT 'Pending',
            bill_date        TEXT    NOT NULL DEFAULT (date('now')),
            created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── 6. appointments ───────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name  TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            doctor        TEXT NOT NULL,
            appt_date     TEXT NOT NULL,
            appt_time     TEXT NOT NULL,
            reason        TEXT,
            status        TEXT NOT NULL DEFAULT 'Scheduled',
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── 7. medications ────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_id INTEGER NOT NULL REFERENCES admissions(id),
            patient_name TEXT    NOT NULL,
            medicine     TEXT    NOT NULL,
            dosage       TEXT    NOT NULL,
            frequency    TEXT    NOT NULL,
            prescribed_by TEXT   NOT NULL,
            start_date   TEXT    NOT NULL,
            end_date     TEXT,
            created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    if c.execute("SELECT COUNT(*) FROM admissions").fetchone()[0] == 0:
        print("📦  Seeding hospital.db …")
        _seed(c)
        print("✅  All tables seeded successfully.")
    else:
        print("✅  Data already exists — skipping seed.")

    conn.commit()
    conn.close()


def _seed(c):
    today = date.today()

    # ── Doctors ───────────────────────────────────────────────
    doctors_data = [
        ("Dr. Mehta",  "Cardiology",       "9811111111", "mehta@medicore.in"),
        ("Dr. Khan",   "Neurology",        "9822222222", "khan@medicore.in"),
        ("Dr. Sharma", "Orthopedics",      "9833333333", "sharma@medicore.in"),
        ("Dr. Iyer",   "General Medicine", "9844444444", "iyer@medicore.in"),
        ("Dr. Patel",  "Pulmonology",      "9855555555", "patel@medicore.in"),
        ("Dr. Singh",  "Endocrinology",    "9866666666", "singh@medicore.in"),
        ("Dr. Reddy",  "Gastroenterology", "9877777777", "reddy@medicore.in"),
        ("Dr. Gupta",  "Nephrology",       "9888888888", "gupta@medicore.in"),
    ]
    c.executemany(
        "INSERT INTO doctors (name, speciality, phone, email) VALUES (?,?,?,?)",
        doctors_data
    )

    # ── Wards ─────────────────────────────────────────────────
    wards_data = [
        ("General Ward", "G101", "General", 2000),
        ("General Ward", "G102", "General", 2000),
        ("General Ward", "G103", "General", 2000),
        ("General Ward", "G104", "General", 2000),
        ("ICU",          "I201", "ICU",     8000),
        ("ICU",          "I202", "ICU",     8000),
        ("ICU",          "I203", "ICU",     8000),
        ("Private Ward", "P301", "Private", 5000),
        ("Private Ward", "P302", "Private", 5000),
        ("Private Ward", "P303", "Private", 5000),
    ]
    c.executemany(
        "INSERT INTO wards (ward_name, bed_number, bed_type, rate_per_day) VALUES (?,?,?,?)",
        wards_data
    )

    # ── Patients + Admissions ─────────────────────────────────
    patients_raw = [
        ("Aisha Kapoor",  45, "Female", "9812345678", "101 MG Road, Mumbai", "B+",  "9900000001"),
        ("Rahul Mehta",   32, "Male",   "9823456789", "202 MG Road, Mumbai", "O+",  "9900000002"),
        ("Priya Singh",   28, "Female", "9834567890", "303 MG Road, Mumbai", "A+",  "9900000003"),
        ("Arjun Patel",   55, "Male",   "9845678901", "404 MG Road, Mumbai", "AB+", "9900000004"),
        ("Neha Sharma",   40, "Female", "9856789012", "505 MG Road, Mumbai", "B-",  "9900000005"),
        ("Vikram Bose",   62, "Male",   "9867890123", "606 MG Road, Mumbai", "O-",  "9900000006"),
        ("Sunita Reddy",  38, "Female", "9878901234", "707 MG Road, Mumbai", "A-",  "9900000007"),
        ("Karan Gupta",   50, "Male",   "9889012345", "808 MG Road, Mumbai", "B+",  "9900000008"),
        ("Meena Iyer",    33, "Female", "9890123456", "109 MG Road, Mumbai", "O+",  "9900000009"),
        ("Suresh Khanna", 47, "Male",   "9801234567", "210 MG Road, Mumbai", "A+",  "9900000010"),
        ("Fatima Khan",   29, "Female", "9712345678", "311 MG Road, Mumbai", "AB-", "9900000011"),
        ("Ankit Joshi",   41, "Male",   "9723456789", "412 MG Road, Mumbai", "B+",  "9900000012"),
        ("Deepa Nair",    36, "Female", "9734567890", "513 MG Road, Mumbai", "O+",  "9900000013"),
        ("Rohit Verma",   58, "Male",   "9745678901", "614 MG Road, Mumbai", "A+",  "9900000014"),
        ("Kavita Pillai", 44, "Female", "9756789012", "715 MG Road, Mumbai", "B-",  "9900000015"),
    ]
    diseases = [
        "Acute Appendicitis", "Hypertension",    "Diabetes Type 2",
        "Fracture - Tibia",   "Migraine",        "Cardiac Arrhythmia",
        "Pneumonia",          "Dengue Fever",    "Kidney Stone",
        "Thyroid Disorder",   "Asthma",          "Vertigo",
        "Anaemia",            "Jaundice",        "COVID-19",
    ]
    doctors_list = [d[0] for d in doctors_data]
    ward_list = [
        ("General", "G101", 2000), ("General", "G102", 2000),
        ("ICU",     "I201", 8000), ("Private", "P301", 5000),
        ("General", "G103", 2000), ("ICU",     "I202", 8000),
        ("Private", "P302", 5000), ("General", "G104", 2000),
        ("ICU",     "I203", 8000), ("Private", "P303", 5000),
    ]
    payments  = ["Paid", "Pending", "Insurance"]
    notes_list = [
        "Patient stable, monitoring required.",
        "Requires daily blood pressure checks.",
        "On insulin therapy.",
        "Post-op care, no weight-bearing.",
        "Prescribed migraine prophylaxis.",
        "ECG every 6 hours.",
        "Chest X-ray done, improving.",
        "Platelet count monitored daily.",
        "Hydration and pain management ongoing.",
        "Thyroid levels normalising.",
        "Nebulisation 3x daily.",
        "Physiotherapy recommended.",
        "Iron infusion scheduled.",
        "Bilirubin levels reducing.",
        "Isolation protocol followed.",
    ]

    admission_ids = []
    for i, p in enumerate(patients_raw):
        c.execute(
            """INSERT INTO patients
               (name, age, gender, phone, address, blood_group, emergency_contact)
               VALUES (?,?,?,?,?,?,?)""", p
        )
        patient_id = c.lastrowid

        days_ago  = random.randint(1, 18)
        adm_date  = (today - timedelta(days=days_ago)).isoformat()
        w, b, r   = ward_list[i % len(ward_list)]
        status    = "Admitted" if i < 10 else "Discharged"
        disc_date = (today - timedelta(days=random.randint(0, max(1, days_ago - 1)))).isoformat() \
                    if status == "Discharged" else None

        c.execute(
            """INSERT INTO admissions
               (patient_id, name, age, gender, phone, address, disease, doctor,
                ward, bed, rate, adm_date, discharge_date, status, payment, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                patient_id, p[0], p[1], p[2], p[3], p[4],
                diseases[i], doctors_list[i % len(doctors_list)],
                w, b, r, adm_date, disc_date, status,
                payments[i % 3], notes_list[i],
            ),
        )
        adm_id = c.lastrowid
        admission_ids.append((adm_id, p[0], days_ago, r, status))

    # ── Billing ───────────────────────────────────────────────
    pmodes = ["Cash", "Card", "Insurance", "UPI"]
    for adm_id, pname, days, rate, status in admission_ids:
        bed_ch = rate * days
        med_ch = random.randint(500,  5000)
        lab_ch = random.randint(200,  3000)
        doc_ch = random.randint(1000, 4000)
        oth_ch = random.randint(0,    1000)
        total  = bed_ch + med_ch + lab_ch + doc_ch + oth_ch
        pst    = "Paid" if status == "Discharged" else random.choice(["Pending", "Partial"])
        c.execute(
            """INSERT INTO billing
               (admission_id, patient_name, bed_charges, medicine_charges,
                lab_charges, doctor_charges, other_charges, total,
                payment_mode, payment_status)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (adm_id, pname, bed_ch, med_ch, lab_ch, doc_ch, oth_ch,
             total, random.choice(pmodes), pst)
        )

    # ── Appointments ──────────────────────────────────────────
    reasons = ["Follow-up", "Routine Check", "Blood Test Review",
               "Post-surgery Review", "New Consultation", "ECG Review"]
    for i in range(12):
        offset    = random.randint(-3, 7)
        appt_date = (today + timedelta(days=offset)).isoformat()
        appt_time = f"{random.randint(9,17):02d}:{random.choice(['00','15','30','45'])}"
        p         = patients_raw[i % len(patients_raw)]
        appt_st   = "Done" if offset < 0 else ("Cancelled" if offset == 0 and i % 4 == 0 else "Scheduled")
        c.execute(
            """INSERT INTO appointments
               (patient_name, patient_phone, doctor, appt_date, appt_time, reason, status)
               VALUES (?,?,?,?,?,?,?)""",
            (p[0], p[3], doctors_list[i % len(doctors_list)],
             appt_date, appt_time, random.choice(reasons), appt_st)
        )

    # ── Medications ───────────────────────────────────────────
    meds = [
        ("Paracetamol 500mg",  "1 tablet", "3x daily"),
        ("Metformin 500mg",    "1 tablet", "2x daily"),
        ("Amlodipine 5mg",     "1 tablet", "Once daily"),
        ("Azithromycin 500mg", "1 tablet", "Once daily"),
        ("Pantoprazole 40mg",  "1 tablet", "Before meals"),
        ("Cefixime 200mg",     "1 tablet", "2x daily"),
        ("Ibuprofen 400mg",    "1 tablet", "SOS"),
        ("Ondansetron 4mg",    "1 tablet", "SOS"),
    ]
    for i, (adm_id, pname, days, _, _2) in enumerate(admission_ids[:10]):
        med   = meds[i % len(meds)]
        start = (today - timedelta(days=days)).isoformat()
        end   = (today + timedelta(days=random.randint(3, 7))).isoformat()
        c.execute(
            """INSERT INTO medications
               (admission_id, patient_name, medicine, dosage, frequency,
                prescribed_by, start_date, end_date)
               VALUES (?,?,?,?,?,?,?,?)""",
            (adm_id, pname, med[0], med[1], med[2],
             doctors_list[i % len(doctors_list)], start, end)
        )


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_dict(row):
    return dict(row)


def adm_dict(row):
    d = dict(row)
    return {
        "id":            d["id"],
        "patientId":     d.get("patient_id"),
        "name":          d["name"],
        "age":           d["age"],
        "gender":        d["gender"],
        "phone":         d["phone"],
        "address":       d["address"],
        "disease":       d["disease"],
        "doctor":        d["doctor"],
        "ward":          d["ward"],
        "bed":           d["bed"],
        "rate":          d["rate"],
        "admDate":       d["adm_date"],
        "dischargeDate": d.get("discharge_date"),
        "status":        d["status"],
        "payment":       d["payment"],
        "notes":         d.get("notes", ""),
        "createdAt":     d.get("created_at", ""),
    }


def cors(resp):
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.after_request
def after(resp):
    return cors(resp)


@app.route("/api/<path:p>", methods=["OPTIONS"])
def options(p):
    return cors(jsonify({}))


# ══════════════════════════════════════════════════════════════
#  FRONTEND
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


# ══════════════════════════════════════════════════════════════
#  ADMISSIONS
#  ⚠️  /search MUST be registered before /<int:pid>
# ══════════════════════════════════════════════════════════════

@app.route("/api/admissions", methods=["GET"])
def list_admissions():
    conn = get_db()
    rows = conn.execute("SELECT * FROM admissions ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([adm_dict(r) for r in rows])


@app.route("/api/admissions/search", methods=["GET"])
def search_admissions():
    q      = request.args.get("q",      "").strip()
    status = request.args.get("status", "").strip()
    doctor = request.args.get("doctor", "").strip()
    ward   = request.args.get("ward",   "").strip()

    sql, params = "SELECT * FROM admissions WHERE 1=1", []
    if q:
        sql += " AND (name LIKE ? OR disease LIKE ? OR bed LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if status:
        sql += " AND status = ?"
        params.append(status)
    if doctor:
        sql += " AND doctor = ?"
        params.append(doctor)
    if ward:
        sql += " AND ward = ?"
        params.append(ward)
    sql += " ORDER BY id DESC"

    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([adm_dict(r) for r in rows])


@app.route("/api/admissions/<int:pid>", methods=["GET"])
def get_admission(pid):
    conn = get_db()
    row = conn.execute("SELECT * FROM admissions WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Patient not found"}), 404
    return jsonify(adm_dict(row))


@app.route("/api/admissions", methods=["POST"])
def create_admission():
    data = request.get_json(force=True)

    required = ["name", "age", "gender", "phone", "address",
                "disease", "doctor", "ward", "bed", "rate", "admDate", "payment"]
    for f in required:
        if f not in data or str(data[f]).strip() == "":
            return jsonify({"error": f"Missing required field: {f}"}), 400

    try:
        age  = int(data["age"])
        rate = int(data["rate"])
        assert 0 < age <= 130, "age out of range"
        assert rate > 0,       "rate must be positive"
    except (ValueError, AssertionError) as e:
        return jsonify({"error": str(e)}), 400

    conn = get_db()

    # Auto-upsert patient record by phone
    existing = conn.execute(
        "SELECT id FROM patients WHERE phone=?", (data["phone"].strip(),)
    ).fetchone()
    if existing:
        patient_id = existing["id"]
    else:
        cur = conn.execute(
            """INSERT INTO patients
               (name, age, gender, phone, address, blood_group, emergency_contact)
               VALUES (?,?,?,?,?,?,?)""",
            (
                data["name"].strip(), age, data["gender"].strip(),
                data["phone"].strip(), data["address"].strip(),
                data.get("bloodGroup", ""), data.get("emergencyContact", "")
            )
        )
        patient_id = cur.lastrowid

    cur = conn.execute(
        """INSERT INTO admissions
           (patient_id, name, age, gender, phone, address, disease, doctor,
            ward, bed, rate, adm_date, status, payment, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'Admitted',?,?)""",
        (
            patient_id,
            data["name"].strip(), age, data["gender"].strip(),
            data["phone"].strip(), data["address"].strip(),
            data["disease"].strip(), data["doctor"].strip(),
            data["ward"].strip(), data["bed"].strip(), rate,
            data["admDate"].strip(), data["payment"].strip(),
            data.get("notes", "")
        ),
    )
    adm_id = cur.lastrowid

    # Auto-create blank billing entry for this admission
    conn.execute(
        """INSERT INTO billing
           (admission_id, patient_name, bed_charges, total, payment_status)
           VALUES (?,?,0,0,'Pending')""",
        (adm_id, data["name"].strip())
    )

    conn.commit()
    row = conn.execute("SELECT * FROM admissions WHERE id=?", (adm_id,)).fetchone()
    conn.close()
    return jsonify(adm_dict(row)), 201


@app.route("/api/admissions/<int:pid>", methods=["PUT"])
def update_admission(pid):
    data = request.get_json(force=True)
    conn = get_db()
    if not conn.execute("SELECT id FROM admissions WHERE id=?", (pid,)).fetchone():
        conn.close()
        return jsonify({"error": "Patient not found"}), 404

    col_map = {
        "admDate":       "adm_date",
        "dischargeDate": "discharge_date",
        "name":    "name",    "age":     "age",     "gender":  "gender",
        "phone":   "phone",   "address": "address", "disease": "disease",
        "doctor":  "doctor",  "ward":    "ward",    "bed":     "bed",
        "rate":    "rate",    "status":  "status",  "payment": "payment",
        "notes":   "notes",
    }
    cols, vals = [], []
    for k, v in data.items():
        if k in col_map:
            cols.append(f"{col_map[k]} = ?")
            vals.append(v)

    if not cols:
        conn.close()
        return jsonify({"error": "No valid fields to update"}), 400

    vals.append(pid)
    conn.execute(f"UPDATE admissions SET {', '.join(cols)} WHERE id=?", vals)
    conn.commit()
    row = conn.execute("SELECT * FROM admissions WHERE id=?", (pid,)).fetchone()
    conn.close()
    return jsonify(adm_dict(row))


@app.route("/api/admissions/<int:pid>", methods=["DELETE"])
def delete_admission(pid):
    conn = get_db()
    if not conn.execute("SELECT id FROM admissions WHERE id=?", (pid,)).fetchone():
        conn.close()
        return jsonify({"error": "Patient not found"}), 404
    conn.execute("DELETE FROM billing    WHERE admission_id=?", (pid,))
    conn.execute("DELETE FROM medications WHERE admission_id=?", (pid,))
    conn.execute("DELETE FROM admissions WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": pid})


# ══════════════════════════════════════════════════════════════
#  PATIENTS
# ══════════════════════════════════════════════════════════════

@app.route("/api/patients", methods=["GET"])
def list_patients():
    conn = get_db()
    rows = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([row_dict(r) for r in rows])


@app.route("/api/patients/<int:pid>", methods=["GET"])
def get_patient(pid):
    conn = get_db()
    row = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    admissions = conn.execute(
        "SELECT * FROM admissions WHERE patient_id=? ORDER BY id DESC", (pid,)
    ).fetchall()
    conn.close()
    result = row_dict(row)
    result["admissions"] = [adm_dict(a) for a in admissions]
    return jsonify(result)


# ══════════════════════════════════════════════════════════════
#  DOCTORS
# ══════════════════════════════════════════════════════════════

@app.route("/api/doctors", methods=["GET"])
def list_doctors():
    conn = get_db()
    rows = conn.execute("SELECT * FROM doctors ORDER BY name").fetchall()
    conn.close()
    return jsonify([row_dict(r) for r in rows])


@app.route("/api/doctors", methods=["POST"])
def create_doctor():
    data = request.get_json(force=True)
    for f in ["name", "speciality", "phone"]:
        if not data.get(f):
            return jsonify({"error": f"Missing: {f}"}), 400
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO doctors (name, speciality, phone, email) VALUES (?,?,?,?)",
        (data["name"], data["speciality"], data["phone"], data.get("email", ""))
    )
    conn.commit()
    row = conn.execute("SELECT * FROM doctors WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(row_dict(row)), 201


# ══════════════════════════════════════════════════════════════
#  WARDS
# ══════════════════════════════════════════════════════════════

@app.route("/api/wards", methods=["GET"])
def list_wards():
    conn = get_db()
    rows = conn.execute("SELECT * FROM wards ORDER BY bed_number").fetchall()
    conn.close()
    return jsonify([row_dict(r) for r in rows])


@app.route("/api/wards/available", methods=["GET"])
def available_wards():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM wards WHERE occupied=0 ORDER BY bed_type, bed_number"
    ).fetchall()
    conn.close()
    return jsonify([row_dict(r) for r in rows])


# ══════════════════════════════════════════════════════════════
#  BILLING
# ══════════════════════════════════════════════════════════════

@app.route("/api/billing", methods=["GET"])
def list_billing():
    conn = get_db()
    rows = conn.execute("SELECT * FROM billing ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([row_dict(r) for r in rows])


@app.route("/api/billing/<int:adm_id>", methods=["GET"])
def get_bill(adm_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM billing WHERE admission_id=?", (adm_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Bill not found"}), 404
    return jsonify(row_dict(row))


@app.route("/api/billing/<int:adm_id>", methods=["PUT"])
def update_bill(adm_id):
    data = request.get_json(force=True)
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM billing WHERE admission_id=?", (adm_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Bill not found"}), 404

    bed_ch = int(data.get("bedCharges",      row["bed_charges"]))
    med_ch = int(data.get("medicineCharges", row["medicine_charges"]))
    lab_ch = int(data.get("labCharges",      row["lab_charges"]))
    doc_ch = int(data.get("doctorCharges",   row["doctor_charges"]))
    oth_ch = int(data.get("otherCharges",    row["other_charges"]))
    total  = bed_ch + med_ch + lab_ch + doc_ch + oth_ch

    conn.execute(
        """UPDATE billing SET
           bed_charges=?, medicine_charges=?, lab_charges=?,
           doctor_charges=?, other_charges=?, total=?,
           payment_mode=?, payment_status=?
           WHERE admission_id=?""",
        (bed_ch, med_ch, lab_ch, doc_ch, oth_ch, total,
         data.get("paymentMode",   row["payment_mode"]),
         data.get("paymentStatus", row["payment_status"]),
         adm_id)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM billing WHERE admission_id=?", (adm_id,)).fetchone()
    conn.close()
    return jsonify(row_dict(row))


# ══════════════════════════════════════════════════════════════
#  APPOINTMENTS
# ══════════════════════════════════════════════════════════════

@app.route("/api/appointments", methods=["GET"])
def list_appointments():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM appointments ORDER BY appt_date DESC, appt_time DESC"
    ).fetchall()
    conn.close()
    return jsonify([row_dict(r) for r in rows])


@app.route("/api/appointments", methods=["POST"])
def create_appointment():
    data = request.get_json(force=True)
    for f in ["patientName", "patientPhone", "doctor", "apptDate", "apptTime"]:
        if not data.get(f):
            return jsonify({"error": f"Missing: {f}"}), 400
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO appointments
           (patient_name, patient_phone, doctor, appt_date, appt_time, reason, status)
           VALUES (?,?,?,?,?,?,?)""",
        (data["patientName"], data["patientPhone"], data["doctor"],
         data["apptDate"],    data["apptTime"],
         data.get("reason", ""), data.get("status", "Scheduled"))
    )
    conn.commit()
    row = conn.execute("SELECT * FROM appointments WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(row_dict(row)), 201


@app.route("/api/appointments/<int:aid>", methods=["PUT"])
def update_appointment(aid):
    data = request.get_json(force=True)
    conn = get_db()
    if not conn.execute("SELECT id FROM appointments WHERE id=?", (aid,)).fetchone():
        conn.close()
        return jsonify({"error": "Not found"}), 404

    col_map = {
        "patientName":  "patient_name",
        "patientPhone": "patient_phone",
        "doctor":    "doctor",
        "apptDate":  "appt_date",
        "apptTime":  "appt_time",
        "reason":    "reason",
        "status":    "status",
    }
    cols, vals = [], []
    for k, v in data.items():
        if k in col_map:
            cols.append(f"{col_map[k]} = ?")
            vals.append(v)
    if cols:
        vals.append(aid)
        conn.execute(f"UPDATE appointments SET {', '.join(cols)} WHERE id=?", vals)
        conn.commit()
    row = conn.execute("SELECT * FROM appointments WHERE id=?", (aid,)).fetchone()
    conn.close()
    return jsonify(row_dict(row))


# ══════════════════════════════════════════════════════════════
#  MEDICATIONS
# ══════════════════════════════════════════════════════════════

@app.route("/api/medications/<int:adm_id>", methods=["GET"])
def get_medications(adm_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM medications WHERE admission_id=? ORDER BY id DESC", (adm_id,)
    ).fetchall()
    conn.close()
    return jsonify([row_dict(r) for r in rows])


@app.route("/api/medications", methods=["POST"])
def add_medication():
    data = request.get_json(force=True)
    required = ["admissionId", "patientName", "medicine",
                "dosage", "frequency", "prescribedBy", "startDate"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"Missing: {f}"}), 400
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO medications
           (admission_id, patient_name, medicine, dosage, frequency,
            prescribed_by, start_date, end_date)
           VALUES (?,?,?,?,?,?,?,?)""",
        (data["admissionId"], data["patientName"], data["medicine"],
         data["dosage"],      data["frequency"],   data["prescribedBy"],
         data["startDate"],   data.get("endDate", ""))
    )
    conn.commit()
    row = conn.execute("SELECT * FROM medications WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(row_dict(row)), 201


# ══════════════════════════════════════════════════════════════
#  DASHBOARD STATS
# ══════════════════════════════════════════════════════════════

@app.route("/api/stats", methods=["GET"])
def stats():
    conn = get_db()

    total      = conn.execute("SELECT COUNT(*) FROM admissions").fetchone()[0]
    admitted   = conn.execute("SELECT COUNT(*) FROM admissions WHERE status='Admitted'").fetchone()[0]
    discharged = conn.execute("SELECT COUNT(*) FROM admissions WHERE status='Discharged'").fetchone()[0]
    total_beds = conn.execute("SELECT COUNT(*) FROM wards").fetchone()[0]
    occ_beds   = conn.execute("SELECT COUNT(*) FROM wards WHERE occupied=1").fetchone()[0]
    total_rev  = conn.execute("SELECT COALESCE(SUM(total),0) FROM billing").fetchone()[0]
    pending    = conn.execute(
        "SELECT COALESCE(SUM(total),0) FROM billing WHERE payment_status='Pending'"
    ).fetchone()[0]
    today_appt = conn.execute(
        "SELECT COUNT(*) FROM appointments WHERE appt_date=?",
        (date.today().isoformat(),)
    ).fetchone()[0]

    # Admissions per day — last 7 days
    weekly = {}
    for row in conn.execute(
        """SELECT adm_date, COUNT(*) as cnt FROM admissions
           WHERE adm_date >= date('now','-6 days')
           GROUP BY adm_date ORDER BY adm_date"""
    ):
        weekly[row["adm_date"]] = row["cnt"]

    # Ward occupancy by type
    ward_stats = {}
    for row in conn.execute(
        """SELECT bed_type, COUNT(*) as total, SUM(occupied) as occupied
           FROM wards GROUP BY bed_type"""
    ):
        ward_stats[row["bed_type"]] = {
            "total": row["total"], "occupied": row["occupied"]
        }

    # Top 5 diseases
    top_diseases = []
    for row in conn.execute(
        """SELECT disease, COUNT(*) as cnt FROM admissions
           GROUP BY disease ORDER BY cnt DESC LIMIT 5"""
    ):
        top_diseases.append({"disease": row["disease"], "count": row["cnt"]})

    conn.close()
    return jsonify({
        "total":             total,
        "admitted":          admitted,
        "discharged":        discharged,
        "availableBeds":     max(0, total_beds - occ_beds),
        "totalBeds":         total_beds,
        "totalRevenue":      total_rev,
        "pendingPayments":   pending,
        "todayAppointments": today_appt,
        "weekly":            weekly,
        "wardStats":         ward_stats,
        "topDiseases":       top_diseases,
    })


# ══════════════════════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════════════════════

with app.app_context():
    print(f"\n🏥  MediCore HMS — Full Edition")
    print(f"📂  Database : {DB}")
    init_db()
    print(f"🌐  Running  : http://localhost:8080")
    print("\n📋  API Endpoints:")
    print("    GET              /api/stats")
    print("    GET  POST        /api/admissions")
    print("    GET  PUT DELETE  /api/admissions/<id>")
    print("    GET              /api/admissions/search?q=&status=&doctor=&ward=")
    print("    GET              /api/patients")
    print("    GET              /api/patients/<id>")
    print("    GET  POST        /api/doctors")
    print("    GET              /api/wards")
    print("    GET              /api/wards/available")
    print("    GET              /api/billing")
    print("    GET  PUT         /api/billing/<admission_id>")
    print("    GET  POST        /api/appointments")
    print("    PUT              /api/appointments/<id>")
    print("    GET              /api/medications/<admission_id>")
    print("    POST             /api/medications\n")


if __name__ == "__main__":
    app.run(debug=True, port=8080)