import subprocess
import os
import sys

def run_script(script_name):
    print(f"\n{'='*60}")
    print(f"RUNNING: {script_name}")
    print(f"{'='*60}")
    
    result = subprocess.run([sys.executable, script_name], capture_output=False)
    if result.returncode != 0:
        print(f"\nERROR: {script_name} failed with exit code {result.returncode}")
        sys.exit(result.returncode)

def main():
    scripts = [
        "stage0_data.py",
        "stage1_garch.py",
        "stage2_dependence.py",
        "stage3_network.py",
        "stage4_sii.py",
        "stage5_analysis.py"
    ]
    
    for script in scripts:
        if os.path.exists(script):
            run_script(script)
        else:
            print(f"Warning: {script} not found. Skipping.")

    print("\n" + "#"*60)
    print("PROJECT EXECUTION COMPLETE")
    print("#"*60)

if __name__ == "__main__":
    main()
