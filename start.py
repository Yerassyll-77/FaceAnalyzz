import os
import sys
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, "venv")
PORT = 8080

DB_FILE = os.path.join(BASE_DIR, "db.sqlite3")
MEDIA_DIR = os.path.join(BASE_DIR, "media")
INIT_MARKER = os.path.join(BASE_DIR, ".db_initialized")

if sys.platform == "win32":
    VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
    PIP = os.path.join(VENV_DIR, "Scripts", "pip.exe")
else:
    VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")
    PIP = os.path.join(VENV_DIR, "bin", "pip")


def run(cmd):
    subprocess.run(cmd, shell=True, check=False, cwd=BASE_DIR,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def reset_db():
    """One-time: wipe db + uploaded media."""
    print("[*] DB tazalanuda...")

    # Remove SQLite database
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except Exception as e:
            print(f"    db.sqlite3 zhoiu qatesi: {e}")

    # Remove uploaded media (analyses + live sessions)
    for sub in ("analysis", "live_sessions"):
        path = os.path.join(MEDIA_DIR, sub)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(f"    {sub} zhoiu qatesi: {e}")

    print("[*] DB tazalandy")


def main():
    print("FaceAnalyzer")
    print()

    if not os.path.exists(VENV_PYTHON):
        print("[1/2] Ornatyluda... (5-10 min)")
        subprocess.run(f'"{sys.executable}" -m venv venv', shell=True, check=True, cwd=BASE_DIR)
        subprocess.run(f'"{PIP}" install -r requirements.txt',
                       shell=True, check=False, cwd=BASE_DIR)
    else:
        result = subprocess.run(f'"{VENV_PYTHON}" -c "import deepface"',
                                shell=True, cwd=BASE_DIR,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode != 0:
            print("[1/2] Dependencies ornatyluda...")
            subprocess.run(f'"{PIP}" install -r requirements.txt',
                           shell=True, check=False, cwd=BASE_DIR)
        else:
            print("[1/2] OK")

    # First-run only: wipe DB and media
    if not os.path.exists(INIT_MARKER):
        reset_db()
        with open(INIT_MARKER, "w", encoding="utf-8") as f:
            f.write("initialized")

    print("[2/2] Dайындалуда...")
    run(f'"{VENV_PYTHON}" manage.py migrate --run-syncdb')
    run(f'"{VENV_PYTHON}" manage.py shell -c "'
        "from django.contrib.auth.models import User;"
        "User.objects.create_superuser('admin','admin@face.kz','admin123') "
        "if not User.objects.filter(username='admin').exists() else None"
        '"')

    print()
    print(f"http://127.0.0.1:{PORT}/")
    print(f"Login: admin / admin123")
    print()

    os.execv(VENV_PYTHON, [VENV_PYTHON, "manage.py", "runserver", str(PORT), "--noreload"])


if __name__ == "__main__":
    main()
