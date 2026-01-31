PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Hospitals (
    hospital_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    sector_hash TEXT NOT NULL,
    auth_key_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Users (
    anon_id TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('Donor', 'Patient')),
    blood_type TEXT NOT NULL,
    sector_hash TEXT NOT NULL,
    device_id TEXT NOT NULL,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_by_hospital_id TEXT,
    auth_key TEXT NOT NULL,
    FOREIGN KEY (verified_by_hospital_id) REFERENCES Hospitals (hospital_id)
);

CREATE TABLE IF NOT EXISTS Requests (
    request_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    need TEXT NOT NULL,
    urgency TEXT NOT NULL CHECK (urgency IN ('High', 'Medium', 'Critical')),
    status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Fulfilled', 'Cancelled')),
    created_at TEXT NOT NULL
        DEFAULT (CAST(strftime('%s','now') AS TEXT)),
    verified_by_hospital_id TEXT,
    resource_type TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES Users (anon_id),
    FOREIGN KEY (verified_by_hospital_id) REFERENCES Hospitals (hospital_id)
);

CREATE TABLE IF NOT EXISTS Inbox (
    message_id TEXT PRIMARY KEY,
    sender_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    encrypted_content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Delivered', 'Pending')),
    created_at TEXT NOT NULL
        DEFAULT (CAST(strftime('%s','now') AS TEXT)),
    FOREIGN KEY (sender_id) REFERENCES Users (anon_id),
    FOREIGN KEY (recipient_id) REFERENCES Users (anon_id)
);

CREATE TABLE IF NOT EXISTS Ledger (
    block_id INT PRIMARY KEY,
    previous_hash TEXT NOT NULL,
    action_type TEXT NOT NULL,
    data_payload TEXT NOT NULL,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    block_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS PoliceEvidence (
    evidence_id TEXT PRIMARY KEY,
    related_message_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    encrypted_packet_police TEXT NOT NULL,
    FOREIGN KEY (sender_id) REFERENCES Users (anon_id),
    FOREIGN KEY (related_message_id) REFERENCES Inbox (message_id)
);

CREATE TABLE IF NOT EXISTS auth_tokens_users(
    sso_token TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
        DEFAULT (CAST(strftime('%s','now') AS TEXT)),
    user_id TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES Users (anon_id)
);

CREATE INDEX IF NOT EXISTS idx_users_location_role ON Users (sector_hash, role);
CREATE INDEX IF NOT EXISTS idx_inbox_recipient ON Inbox (recipient_id);
CREATE INDEX IF NOT EXISTS idx_requests_dashboard ON Requests (verified_by_hospital_id, status);
CREATE INDEX IF NOT EXISTS idx_requests_patient ON Requests (patient_id);
CREATE INDEX IF NOT EXISTS idx_users_verified ON Users (verified_by_hospital_id);
CREATE INDEX IF NOT EXISTS idx_police_sender ON PoliceEvidence (sender_id);
CREATE INDEX IF NOT EXISTS idx_inbox_pending ON Inbox (recipient_id, status);
CREATE INDEX IF NOT EXISTS idx_users_unverified_sector ON Users (sector_hash, verified_by_hospital_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_lookup ON auth_tokens_users (user_id, sso_token);