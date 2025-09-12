# pgmini-migrate

`pgmini-migrate` is a **lightweight SQL migration tool** for PostgreSQL.  
It allows you to easily **create migration files** and run **upgrades/downgrades** using simple CLI commands.  

No ORM required — just pure SQL.

---

## ✨ Features
- Auto-generate migration files (`upgrade` + `downgrade`).
- Run **upgrade** or **downgrade** up to a specific version.
- Two connection options:
  - via `DATABASE_URL`
  - via `host`, `port`, `user`, `password`, `dbname`.
- Configurable migrations directory.
- Minimal, simple, and PostgreSQL-focused.

---

## 📦 Installation

```bash
pip install pgmini-migrate