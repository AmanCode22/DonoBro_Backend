# 🩸 DonorBro Backend (Forensic-Grade Core)

> **Status:** 🟢 Live & Deployed
> **Architecture:** Python/Flask + Immutable Blockchain Ledger + RAM-Ticket SSE
> **Mission:** Reducing Time-to-Transfusion via Decentralized, Forensic Logic.

![SDG Alignment](https://img.shields.io/badge/SDG-3_9_10_11_16-green?style=flat-square)
![License](https://img.shields.io/badge/License-AGPLv3-blue?style=flat-square)
![Environment](https://img.shields.io/badge/Host-FreeBSD-red?style=flat-square)

---

## 🌍 The Mission
DonorBro is **Humanitarian Digital Infrastructure**. It operates in low-trust, high-latency environments to connect blood donors with urgent requests instantly.

It strictly adheres to **UN Sustainable Development Goals**:
* **SDG 3:** Good Health (Life-saving alerting).
* **SDG 9:** Innovation (Resilient, offline-capable infrastructure).
* **SDG 10:** Reduced Inequalities (Democratized access to donors).
* **SDG 16:** Peace & Justice (Anti-corruption via Blockchain logging).

---

## 🏗️ Architecture & Security
The backend acts as a **Forensic State Machine**, assuming the network is hostile and the client device is unreliable.

### 1. The "Two-Key" Security Protocol (RAM-Ticket)
To secure real-time events (SSE) in restrictive hosting environments, the system uses a custom handshake:
1.  **Auth:** Client validates identity via SSO.
2.  **Minting:** Backend generates a disposable, in-memory "Stream Ticket."
3.  **Burning:** The ticket is atomically destroyed upon connection, preventing replay attacks.

### 2. Forensic Blockchain Ledger
Every critical action (Request Created, Donation Pledged, Fulfillment) is hashed and linked to the previous entry using SHA-256.
* **Immutability:** Logs cannot be altered without breaking the cryptographic chain.
* **Auditability:** Provides a verifiable trail for post-incident analysis.

### 3. "Heartbeat" Persistence
The system emits keepalive signals to allow client-side monitoring. If the heartbeat stops, the client automatically attempts to heal the connection.

---

## ⚙️ Tech Stack
* **Language:** Python 3.11+
* **Framework:** Flask (Production Mode)
* **Concurrency:** Asynchronous Event Workers
* **Database:** SQLite (Relational) + Custom JSON Ledger (Forensic)

---

## 📜 License
**GNU Affero General Public License v3.0 (AGPL-3.0)**

Copyright (c) 2026 **Team DonorBro**

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation.
