import subprocess
import sys
import os

def run_command(command):
    """Executes a command and exits if it fails."""
    try:
        # Pass command as a list, and don't use shell=True
        # The output will be streamed to stdout/stderr by default.
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        # Re-construct the command string for the error message
        command_str = ' '.join(e.cmd)
        print(f"Error executing command: {command_str}", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: command not found: {command[0]}", file=sys.stderr)
        sys.exit(1)

def main():
    """Installs dependencies and runs tests."""
    # Ensure we are in the script's directory to ensure paths are correct
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Install dependencies
    requirements_path = os.path.join("scholar-core", "requirements.txt")
    print(f">>> Installing dependencies from {requirements_path}...")
    pip_command = [sys.executable, "-m", "pip", "install", "-r", requirements_path]
    run_command(pip_command)
    print(">>> Dependencies installed successfully.")
    print()

    # Run tests
    print(">>> Running the test suite...")
    test_dir = "scholar-core"
    pytest_command = [sys.executable, "-m", "pytest", test_dir]
    run_command(pytest_command)
    print(">>> Tests completed successfully.")

if __name__ == "__main__":
    main()
