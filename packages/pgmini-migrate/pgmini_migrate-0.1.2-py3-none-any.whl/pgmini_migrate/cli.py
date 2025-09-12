import os
import sys
import psycopg
from contextlib import contextmanager
from datetime import datetime
import argparse

# Default layout
DEFAULT_MIGRATIONS_DIR = "migrations"
UPGRADE_SUBDIR = "upgrade"
DOWNGRADE_SUBDIR = "downgrade"
MIGRATION_TABLE = "schema_migrations"


def load_env_file(env_path=".env"):
    """Load simple env file KEY=VALUE into os.environ (if not already set)."""
    if not os.path.exists(env_path):
        return
    with open(env_path, "r") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            if "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            # do not overwrite existing env set by host
            if k not in os.environ:
                os.environ[k] = v


def build_conninfo_from_args(args):
    """Return a psycopg-compatible connection string or dict kwargs"""
    if args.database_url:
        return args.database_url
    # build a dict for psycopg.connect(...)
    kw = {}
    if args.db_host:
        kw["host"] = args.db_host
    if args.db_port:
        kw["port"] = args.db_port
    if args.db_name:
        kw["dbname"] = args.db_name
    if args.db_user:
        kw["user"] = args.db_user
    if args.db_password:
        kw["password"] = args.db_password
    return kw


@contextmanager
def get_connection(conninfo):
    """Context manager returning a connected psycopg connection (sync)."""
    if isinstance(conninfo, str):
        conn = psycopg.connect(conninfo)
    else:
        conn = psycopg.connect(**conninfo)
    try:
        yield conn
    finally:
        conn.close()


def ensure_migration_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
    conn.commit()


def get_applied_migrations(conn):
    with conn.cursor() as cur:
        cur.execute(f"SELECT version FROM {MIGRATION_TABLE} ORDER BY version")
        rows = cur.fetchall()
        return [row[0] for row in rows]


def apply_migration(conn, version, sql_path):
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    try:
        with conn.cursor() as cur:
            print(f"⬆️  Applying {version} -> {os.path.basename(sql_path)}")
            cur.execute(sql)
            cur.execute(
                f"INSERT INTO {MIGRATION_TABLE} (version) VALUES (%s)", (version,)
            )
        conn.commit()
        print(f"✅ {version} applied.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to apply {version}: {e}")
        raise


def rollback_migration_from_file(conn, version, sql_path):
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    try:
        with conn.cursor() as cur:
            print(f"⬇️  Rolling back {version} -> {os.path.basename(sql_path)}")
            cur.execute(sql)
            cur.execute(f"DELETE FROM {MIGRATION_TABLE} WHERE version = %s", (version,))
        conn.commit()
        print(f"✅ {version} rolled back.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to rollback {version}: {e}")
        raise


def find_migration_files(migrations_root):
    """Return sorted list of upgrade filenames in migrations/upgrade"""
    upgrade_dir = os.path.join(migrations_root, UPGRADE_SUBDIR)
    if not os.path.isdir(upgrade_dir):
        return []
    files = [f for f in os.listdir(upgrade_dir) if f.endswith(".sql")]
    files = sorted(files)
    return files


def parse_version_from_filename(filename):
    """Expect filenames like 001.description.upgrade.sql or 001.description.sql"""
    base = os.path.basename(filename)
    parts = base.split(".", 1)
    return parts[0]


def full_upgrade_path(migrations_root, filename):
    return os.path.join(migrations_root, UPGRADE_SUBDIR, filename)


def full_downgrade_path(migrations_root, filename):
    return os.path.join(migrations_root, DOWNGRADE_SUBDIR, filename)


def get_next_version_str(migrations_root):
    upgrade_dir = os.path.join(migrations_root, UPGRADE_SUBDIR)
    os.makedirs(upgrade_dir, exist_ok=True)
    files = [f for f in os.listdir(upgrade_dir) if f[0:3].isdigit()]
    versions = [int(f[0:3]) for f in files if f[0:3].isdigit()]
    next_v = max(versions) + 1 if versions else 1
    return f"{next_v:03d}"


def create_migration(migrations_root, description):
    desc = description.strip()
    # sanitize description
    desc_clean = "_".join(
        c for c in desc.lower().replace(" ", "_") if (c.isalnum() or c == "_")
    )
    version = get_next_version_str(migrations_root)
    upgrade_name = f"{version}.{desc_clean}.upgrade.sql"
    downgrade_name = f"{version}.{desc_clean}.downgrade.sql"

    upgrade_path = full_upgrade_path(migrations_root, upgrade_name)
    downgrade_path = full_downgrade_path(migrations_root, downgrade_name)

    # ensure dirs
    os.makedirs(os.path.dirname(upgrade_path), exist_ok=True)
    os.makedirs(os.path.dirname(downgrade_path), exist_ok=True)

    ts = datetime.utcnow().isoformat() + "Z"
    with open(upgrade_path, "w", encoding="utf-8") as f:
        f.write(f"-- +upgrade {version} {desc}\n-- created at {ts}\n\n")
    with open(downgrade_path, "w", encoding="utf-8") as f:
        f.write(f"-- +downgrade {version} {desc}\n-- created at {ts}\n\n")

    print(f"Created:\n  {upgrade_path}\n  {downgrade_path}")
    return upgrade_path, downgrade_path


def cmd_upgrade(args):
    conninfo = build_conninfo_from_args(args)
    migrations_root = args.migrations
    files = find_migration_files(migrations_root)
    if not files:
        print("No migration files found.")
        return

    with get_connection(conninfo) as conn:
        ensure_migration_table(conn)
        applied = set(get_applied_migrations(conn))
        for fname in files:
            version = parse_version_from_filename(fname)
            if version in applied:
                print(f"Skipping {fname} (already applied).")
                continue
            sql_path = full_upgrade_path(migrations_root, fname)
            apply_migration(conn, version, sql_path)


def cmd_history(args):
    conninfo = build_conninfo_from_args(args)
    with get_connection(conninfo) as conn:
        ensure_migration_table(conn)
        applied = get_applied_migrations(conn)
        print("Applied migrations (ordered):")
        for v in applied:
            print("  -", v)


def cmd_show(args):
    conninfo = build_conninfo_from_args(args)
    with get_connection(conninfo) as conn:
        ensure_migration_table(conn)
        applied = get_applied_migrations(conn)
        if not applied:
            print("Database has no applied migrations (base).")
        else:
            print("Current version:", applied[-1])


def cmd_downgrade(args):
    conninfo = build_conninfo_from_args(args)
    migrations_root = args.migrations

    with get_connection(conninfo) as conn:
        ensure_migration_table(conn)
        applied = get_applied_migrations(conn)

        if not applied:
            print("No migrations applied.")
            return

        target = args.target  # None => step=1, "base" => all, specific version => to that
        if target is None:
            # default: rollback 1 step
            target_index = len(applied) - 2
        elif target == "base":
            target_index = -1
        else:
            if target not in applied:
                print(f"Target {target} not found in applied migrations.")
                return
            target_index = applied.index(target)

        to_rollback = applied[target_index + 1 :]
        if not to_rollback:
            print("Nothing to rollback.")
            return

        # rollback in reverse order
        for version in reversed(to_rollback):
            # find corresponding file in downgrade dir
            # find filename that starts with version in upgrade dir to get remainder name
            upgrade_dir = os.path.join(migrations_root, UPGRADE_SUBDIR)
            candidates = [f for f in os.listdir(upgrade_dir) if f.startswith(version)]
            if not candidates:
                print(f"⚠️  No upgrade file found for version {version} (can't map to downgrade).")
                continue
            # infer name: replace 'upgrade' -> 'downgrade'
            up_fname = candidates[0]
            down_fname = up_fname.replace(".upgrade.", ".downgrade.")
            down_path = full_downgrade_path(migrations_root, down_fname)
            if not os.path.exists(down_path):
                print(f"⚠️  No rollback file for {version} -> expected {down_path}")
                continue
            rollback_migration_from_file(conn, version, down_path)


def build_arg_parser():
    p = argparse.ArgumentParser(prog="pgmigrate", description="Simple PostgreSQL migration tool")
    p.add_argument("--env-file", default=".env", help="Path to .env file (default: .env)")
    p.add_argument(
        "--migrations",
        default=DEFAULT_MIGRATIONS_DIR,
        help=f"Root migrations dir (default: {DEFAULT_MIGRATIONS_DIR})",
    )

    # DB connection options (mutually override database_url)
    p.add_argument("--database-url", help="Full DATABASE_URL (postgresql://...)", default=None)
    p.add_argument("--db-host", help="DB host", default=os.getenv("POSTGRES_HOST"))
    p.add_argument("--db-port", help="DB port", default=os.getenv("POSTGRES_PORT"))
    p.add_argument("--db-name", help="DB name", default=os.getenv("POSTGRES_DB"))
    p.add_argument("--db-user", help="DB user", default=os.getenv("POSTGRES_USER"))
    p.add_argument("--db-password", help="DB password", default=os.getenv("POSTGRES_PASSWORD"))

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("upgrade", help="Apply all pending migrations")

    down_p = sub.add_parser("downgrade", help="Rollback migrations to target version (or 1 step if no target)")
    down_p.add_argument("target", nargs="?", help="target version (e.g. 002) or 'base'")

    sub.add_parser("history", help="Show applied migrations (history)")

    sub.add_parser("show", help="Show current applied version")

    create_p = sub.add_parser("create", help="Create new migration skeleton")
    create_p.add_argument("description", nargs="+", help="Migration description (quoted)")

    return p


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # Load env file first (do not overwrite existing env vars)
    if args.env_file:
        load_env_file(args.env_file)

    # prefer CLI args, else env
    # Re-populate db fields from env if not provided explicitly
    # (build_conninfo handles database_url precedence)
    # Dispatch commands:
    if args.cmd == "create":
        desc = " ".join(args.description)
        create_migration(args.migrations, desc)
        return

    # For commands that touch DB, ensure connection info exists
    # Build conninfo now (will use args or environment)
    # If neither database_url nor db_name provided, abort
    conninfo = build_conninfo_from_args(args)
    if not conninfo:
        print("No database connection info provided. Provide --database-url or host/name/user/password or set env vars.")
        sys.exit(2)

    if args.cmd == "upgrade":
        cmd_upgrade(args)
    elif args.cmd == "downgrade":
        cmd_downgrade(args)
    elif args.cmd == "history":
        cmd_history(args)
    elif args.cmd == "show":
        cmd_show(args)
    else:
        print("Unknown command:", args.cmd)
        sys.exit(2)
