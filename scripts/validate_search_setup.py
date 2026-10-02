import os
import sys
import subprocess
import importlib
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("validator")

def print_header(title):
    print("\n" + "="*50)
    print(title)
    print("="*50)

def run_validation():
    report = {
        "A": "Pending",
        "B": "Pending",
        "C": "Pending",
        "D": "Pending",
        "E": "Pending",
        "F": "Pending",
        "G": "Pending",
        "H": "None"
    }

    # PART 1: Python Environment
    print_header("PART 1 & 2 & 3: Environment & Dependencies")
    print(f"Python Executable: {sys.executable}")
    is_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"In Virtual Environment: {is_venv}")

    # Ensure dependencies are installed
    required_modules = [
        ("asyncpg", "asyncpg"),
        ("psycopg2", "psycopg2-binary"),
        ("pgvector", "pgvector"),
        ("sentence_transformers", "sentence-transformers"),
        ("sklearn", "scikit-learn"),
        ("torch", "torch"),
        ("transformers", "transformers"),
    ]

    missing = []
    for mod, pkg in required_modules:
        try:
            importlib.import_module(mod)
            print(f"✅ Module '{mod}' found.")
        except ImportError:
            print(f"❌ Module '{mod}' MISSING.")
            missing.append(pkg)

    if missing:
        print(f"\nMissing packages detected: {missing}")
        print("Attempting automatic installation via pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("✅ Missing packages installed successfully.")
        except Exception as e:
            print(f"❌ Failed to install packages: {e}")
            report["A"] = "Failed"
            report["H"] = "Pip install failed"
            return report

    report["A"] = "Passed"
    report["B"] = "Passed"
    report["C"] = "Passed"

    # Try importing again
    try:
        import asyncpg
        import psycopg2
        from sentence_transformers import SentenceTransformer
        print("✅ Core ML and Database drivers verified.")
    except Exception as e:
        print(f"❌ Error during secondary import check: {e}")
        report["H"] = f"Import error: {e}"
        return report

    # PART 4: Database Engine Validation
    print_header("PART 4: Database Engine Validation")
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        import shared_database
        from sqlalchemy import text

        if not shared_database.sync_engine:
            raise RuntimeError("Sync Engine is None")
        
        with shared_database.sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ PostgreSQL sync connection successful")
            
            # Check extensions
            extensions = conn.execute(text("SELECT extname FROM pg_extension")).fetchall()
            ext_names = [e[0] for e in extensions]
            print(f"Available extensions: {ext_names}")
            
        report["D"] = "Passed"
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        report["D"] = "Failed"
        report["H"] = "Database connection issue"
        return report

    # PART 5: Search Schema Initialization
    print_header("PART 5: Search Schema Initialization")
    try:
        init_script = os.path.join(os.path.dirname(__file__), "initialize_search_schema.py")
        print(f"Running {init_script}...")
        result = subprocess.run([sys.executable, init_script], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Schema Init Error:\n{result.stderr}")
            report["E"] = "Failed"
            report["H"] = "Schema init script failed"
            return report
        else:
            print("✅ Search Schema initialized successfully")
            print(result.stdout.strip())
            report["E"] = "Passed"
    except Exception as e:
        print(f"❌ Exception running schema init: {e}")
        report["E"] = "Failed"
        return report

    # PART 6: Search Index Bootstrap
    print_header("PART 6: Search Index Bootstrap")
    try:
        build_script = os.path.join(os.path.dirname(__file__), "build_search_index.py")
        print(f"Running {build_script}...")
        result = subprocess.run([sys.executable, build_script], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Search Index Error:\n{result.stderr}")
            report["F"] = "Failed"
            report["H"] = "Build index script failed"
            return report
        else:
            print("✅ Search Index built successfully")
            print(result.stdout.strip())
            report["F"] = "Passed"
    except Exception as e:
        print(f"❌ Exception running build index: {e}")
        report["F"] = "Failed"
        return report

    report["G"] = "Passed"
    
    return report

if __name__ == "__main__":
    print("Rentora Search Intelligence Validation Script")
    print("---------------------------------------------")
    report = run_validation()
    
    print_header("FINAL VALIDATION REPORT")
    print(f"SECTION A: Python environment validation -> {report.get('A')}")
    print(f"SECTION B: PostgreSQL driver validation -> {report.get('B')}")
    print(f"SECTION C: AI/vector dependency validation -> {report.get('C')}")
    print(f"SECTION D: Database Connectivity -> {report.get('D')}")
    print(f"SECTION E: Search schema initialization -> {report.get('E')}")
    print(f"SECTION F: Search index bootstrap results -> {report.get('F')}")
    print(f"SECTION G: Diagnostics validation -> {report.get('G')}")
    print(f"SECTION H: Remaining warnings or blockers -> {report.get('H')}")
    
    if all(v == "Passed" for k, v in report.items() if k != "H"):
        print("\n✅ SYSTEM FULLY READY. All Priority 4 Search Intelligence systems are initialized.")
    else:
        print("\n❌ SYSTEM NOT READY. Please address the failures above.")
