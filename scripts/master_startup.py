import os
import sys
import time
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

def print_header(title):
    print("\n" + "="*70)
    print(title)
    print("="*70)

def find_docker_path():
    import shutil
    # First check if it's already in the PATH
    if shutil.which("docker"):
        return "docker"
    
    # Common installation paths for Docker Desktop on Windows
    common_paths = [
        r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        r"C:\Program Files\Docker\Docker\bin\docker.exe",
        r"C:\Program Files\Docker\Docker\resources\docker.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            # Return quoted path to handle spaces in Program Files
            return f'"{p}"'
    return "docker"

def run_cmd(cmd, desc):
    docker_bin = find_docker_path()
    if docker_bin != "docker":
        clean_bin = docker_bin.strip('"')
        docker_dir = os.path.dirname(clean_bin)
        # Add to the current process's environment PATH
        if docker_dir and os.path.exists(docker_dir):
            os.environ["PATH"] = docker_dir + os.pathsep + os.environ["PATH"]
            
    if isinstance(cmd, list):
        # Substitute 'docker' with resolved path if it's the first element
        if cmd and cmd[0] == "docker":
            cmd[0] = docker_bin
        cmd_str = ' '.join(cmd)
    else:
        cmd_str = cmd
        if cmd_str.startswith("docker "):
            cmd_str = cmd_str.replace("docker ", f"{docker_bin} ", 1)
        
    print(f"\n⏳ Running: {desc}...")
    print(f"   Command: {cmd_str}")
    try:
        result = subprocess.run(cmd_str, check=True, shell=True)
        print(f"✅ Success: {desc}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {desc}")
        print(f"Error Code: {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print_header("RENTORA FULL PLATFORM STARTUP & VALIDATION MASTER SCRIPT")
    
    # Step 1: Start Core DB Infrastructure
    success = run_cmd(["docker", "compose", "up", "-d", "postgres", "redis", "rabbitmq"], "Start Core Infrastructure (PostgreSQL, Redis, RabbitMQ)")
    if not success:
        print("Stopping due to infrastructure failure.")
        return
        
    print("\n⏳ Waiting 15 seconds for PostgreSQL & RabbitMQ to fully initialize...")
    time.sleep(15)
    
    # Step 2: Validate Search Setup & Schema Init
    success = run_cmd([sys.executable, "scripts/validate_search_setup.py"], "Validate Search Setup & Initialize Schema")
    if not success:
        print("Stopping due to search schema validation failure.")
        return
        
    # Step 3: Build Search Index
    success = run_cmd([sys.executable, "scripts/build_search_index.py"], "Build Search Index & Embeddings")
    # We won't block if this fails, just warn
    if not success:
        print("⚠️ Warning: Search index build encountered errors. Continuing anyway.")
        
    # Step 4: Start Full Microservices Platform
    success = run_cmd(["docker", "compose", "up", "--build", "-d"], "Start Full Microservices Platform")
    if not success:
        print("Stopping due to platform startup failure.")
        return
        
    print("\n⏳ Waiting 30 seconds for microservices and gateway to boot up...")
    for i in range(30, 0, -1):
        print(f"   {i} seconds remaining...", end='\r')
        time.sleep(1)
    print("   Boot wait complete.              ")
    
    # Step 5: Run End-to-End Diagnostics
    run_cmd([sys.executable, "scripts/full_platform_validation.py"], "Run End-to-End Diagnostics & Final Report")

if __name__ == "__main__":
    main()
