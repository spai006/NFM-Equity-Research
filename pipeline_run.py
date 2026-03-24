import subprocess
import sys
import os

def run_step(name, command):
    print(f"\n{'='*50}")
    print(f"🚀 Running Step: {name}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*50}")
    
    try:
        # Run the command
        subprocess.run(command, check=True)
        print(f"✅ {name} completed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} failed with exit code {e.returncode}.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        sys.exit(1)

def main():
    print("🌟 Starting NFM Equity Research Pipeline (v2) 🌟\n")
    
    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)
    
    # Auto-compile C++ consumer if necessary
    cpp_source = "main.cpp"
    cpp_binary = "consumer"
    
    # We compile if the binary doesn't exist, or if the source is newer than the binary
    if not os.path.exists(cpp_binary) or os.path.getmtime(cpp_source) > os.path.getmtime(cpp_binary):
        run_step("Compile C++ Consumer", ["g++", "-O3", "-std=c++17", cpp_source, "-o", cpp_binary])

    # Step 1: Data Ingestion & Factor Engineering
    run_step("Python Producer (Data & Factors)", [sys.executable, "producer.py"])

    # Step 2: NFM Scoring & Ranking
    run_step("C++ Consumer (Scoring & Ranking)", ["./" + cpp_binary])

    # Step 3: Monitoring & Churn Updates
    run_step("Python Churn Monitor", [sys.executable, "src/monitoring/churn.py"])
    
    print("\n🎉 Pipeline Execution Complete! 🎉")
    print("Check the 'reports/' directory for the latest Top 50 outputs.\n")

if __name__ == "__main__":
    main()
