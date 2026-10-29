import json
import os
import sys

def main():
    # Prompt for SendGrid API key
    api_key = input("Enter your SendGrid API key: ").strip()
    # Basic validation – must start with 'SG.' and be longer than a few characters
    if not api_key.startswith("SG.") or len(api_key) < 10:
        print("Invalid API key format. It must start with 'SG.'")
        sys.exit(1)

    # Prompt for compliance approval note
    compliance_note = input("Enter a brief compliance approval note: ").strip()
    if not compliance_note:
        print("Compliance note cannot be empty.")
        sys.exit(1)

    # Build credentials payload
    credentials = {
        "sendgrid_api_key": api_key,
        "compliance_approved": True,
        "compliance_note": compliance_note
    }

    # Write to credentials.json with safe permissions
    try:
        with open("credentials.json", "w", encoding="utf-8") as f:
            json.dump(credentials, f, indent=2)
        # Restrict file permissions to owner read/write only (Unix-like systems)
        os.chmod("credentials.json", 0o600)
        print("Credentials successfully saved to credentials.json")
    except Exception as e:
        print(f"Failed to write credentials file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)