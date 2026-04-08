-- ============================================================
-- Mahaveer Hospital AI — Supabase Table Setup
-- Run this ONCE in your Supabase dashboard → SQL Editor
-- ============================================================

-- PATIENTS
CREATE TABLE IF NOT EXISTS patients (
    id                      BIGSERIAL PRIMARY KEY,
    uhid                    TEXT UNIQUE NOT NULL,
    name                    TEXT,
    diagnosis               TEXT,
    status                  TEXT DEFAULT 'Admitted',
    admitted_on             TEXT,
    discharged_on           TEXT,
    age                     TEXT,
    gender                  TEXT,
    address                 TEXT,
    mobile                  TEXT,
    discharge_condition     TEXT,
    discharge_type          TEXT,
    discharge_instructions  TEXT,
    follow_up               TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- VITALS
CREATE TABLE IF NOT EXISTS vitals (
    id       BIGSERIAL PRIMARY KEY,
    uhid     TEXT NOT NULL,
    date     TEXT,
    time     TEXT,
    pulse    TEXT,
    bp       TEXT,
    rr       TEXT,
    spo2     TEXT,
    temp     TEXT,
    source   TEXT DEFAULT 'Manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS vitals_uhid_idx ON vitals(uhid);
CREATE INDEX IF NOT EXISTS vitals_date_idx ON vitals(date);

-- MEDICATIONS
CREATE TABLE IF NOT EXISTS medications (
    id         BIGSERIAL PRIMARY KEY,
    uhid       TEXT NOT NULL,
    date       TEXT,
    time       TEXT,
    medicine   TEXT,
    dose       TEXT,
    route      TEXT,
    frequency  TEXT,
    given_by   TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS meds_uhid_idx ON medications(uhid);

-- NURSING NOTES
CREATE TABLE IF NOT EXISTS nursing_notes (
    id         BIGSERIAL PRIMARY KEY,
    uhid       TEXT NOT NULL,
    date       TEXT,
    note       TEXT,
    nurse      TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- OT NOTES
CREATE TABLE IF NOT EXISTS ot_notes (
    id               BIGSERIAL PRIMARY KEY,
    uhid             TEXT UNIQUE NOT NULL,
    note             TEXT,
    surgeon          TEXT,
    procedure        TEXT,
    date_of_surgery  TEXT,
    created_at       TEXT
);

-- OT REGISTER
CREATE TABLE IF NOT EXISTS ot_register (
    id           BIGSERIAL PRIMARY KEY,
    date         TEXT,
    patient_name TEXT,
    uhid         TEXT,
    diagnosis    TEXT,
    surgery      TEXT,
    implant      TEXT,
    nail_size    TEXT,
    plate_type   TEXT,
    holes        TEXT,
    surgeon      TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- DAYCARE REGISTER
CREATE TABLE IF NOT EXISTS daycare_register (
    id           BIGSERIAL PRIMARY KEY,
    date         TEXT,
    patient_name TEXT,
    diagnosis    TEXT,
    procedure    TEXT,
    surgeon      TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- BLOOD PRODUCTS
CREATE TABLE IF NOT EXISTS blood_products (
    id           BIGSERIAL PRIMARY KEY,
    uhid         TEXT NOT NULL,
    date         TEXT,
    product      TEXT,
    blood_group  TEXT,
    units        TEXT,
    reaction     TEXT,
    given_by     TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- AUDIT TRAIL
CREATE TABLE IF NOT EXISTS audit_trail (
    id         BIGSERIAL PRIMARY KEY,
    time       TEXT,
    user       TEXT,
    patient    TEXT,
    action     TEXT,
    details    TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- NOTIFICATIONS
CREATE TABLE IF NOT EXISTS notifications (
    id         BIGSERIAL PRIMARY KEY,
    time       TEXT,
    message    TEXT,
    user       TEXT,
    patient    TEXT,
    seen       BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SUMMARY APPROVALS
CREATE TABLE IF NOT EXISTS summary_approvals (
    id           BIGSERIAL PRIMARY KEY,
    uhid         TEXT,
    requested_by TEXT,
    status       TEXT DEFAULT 'Pending',
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- USERS (may already exist — skip if so)
CREATE TABLE IF NOT EXISTS users (
    id         BIGSERIAL PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    password   TEXT,
    role       TEXT,
    status     TEXT DEFAULT 'Pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (recommended)
ALTER TABLE patients        ENABLE ROW LEVEL SECURITY;
ALTER TABLE vitals          ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications     ENABLE ROW LEVEL SECURITY;
ALTER TABLE nursing_notes   ENABLE ROW LEVEL SECURITY;
ALTER TABLE ot_notes        ENABLE ROW LEVEL SECURITY;
ALTER TABLE ot_register     ENABLE ROW LEVEL SECURITY;
ALTER TABLE daycare_register ENABLE ROW LEVEL SECURITY;
ALTER TABLE blood_products  ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_trail     ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications   ENABLE ROW LEVEL SECURITY;
ALTER TABLE summary_approvals ENABLE ROW LEVEL SECURITY;

-- Allow anon key full access (your app uses anon key)
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'patients','vitals','medications','nursing_notes',
        'ot_notes','ot_register','daycare_register','blood_products',
        'audit_trail','notifications','summary_approvals','users'
    ]
    LOOP
        EXECUTE format('CREATE POLICY IF NOT EXISTS "allow_all_%s" ON %s FOR ALL USING (true) WITH CHECK (true)', tbl, tbl);
    END LOOP;
END $$;
