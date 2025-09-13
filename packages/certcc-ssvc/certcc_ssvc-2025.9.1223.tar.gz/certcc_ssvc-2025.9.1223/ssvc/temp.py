import subprocess
import sys
from datetime import datetime

def get_last_commit_date():
    """
    Retrieves the date of the last commit from the git history.
    
    Returns:
        A string representing the committer date in ISO 8601 format,
        or None if the command fails.
    """
    try:
        # Use subprocess to run the git command.
        # -1: limit to one commit
        # --format=%cI: output committer date in ISO 8601 format
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cI'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Git command failed with return code {e.returncode}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        return None

def main():
    """
    Main function to generate the version number and save it to a file.
    """
    commit_date_str = get_last_commit_date()
    
    if not commit_date_str:
        print("Could not retrieve commit date. Aborting version generation.", file=sys.stderr)
        # Exit with a non-zero status code to indicate failure
        sys.exit(1)
        
    try:
        # Parse the ISO 8601 string into a datetime object.
        # For example, "2023-10-27T10:30:00-07:00"
        commit_dt = datetime.fromisoformat(commit_date_str)
        
        # Format the datetime object to the desired format: yyyy.mm.ddhhmm
        version_number = commit_dt.strftime('%Y.%m.%d%H%M')
        
        # Save the version number to a file.
        with open('VERSION', 'w') as f:
            f.write(version_number)
            
        print(f"Version number '{version_number}' generated successfully and saved to 'VERSION' file.")
        
    except ValueError:
        print(f"Error: Failed to parse the date string '{commit_date_str}'.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

