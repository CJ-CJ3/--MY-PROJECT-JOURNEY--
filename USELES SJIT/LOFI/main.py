import subprocess
import sys

# List of scripts to run in order
scripts = [
    r"C:\Users\Never\Desktop\LOFI\lofi_renamer.py",
    r"C:\Users\Never\Desktop\LOFI\combine_audio.py"
]


def run_scripts():
    for script in scripts:
        print(f"\n{'=' * 50}")
        print(f"Running: {script}")
        print('=' * 50)

        # Run the script and wait for it to complete
        result = subprocess.run([sys.executable, script], capture_output=False)

        # Check if script ran successfully
        if result.returncode != 0:
            print(f"Error: {script} failed with return code {result.returncode}")
            break
        else:
            print(f"Completed: {script}")

    print("\n" + "=" * 50)
    print("All scripts finished!")
    print("=" * 50)


if __name__ == "__main__":
    run_scripts()