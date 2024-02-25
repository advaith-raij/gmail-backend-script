# Gmail Automation Script

This script automates tasks related to Gmail using the Gmail API. It can fetch emails, store them in a SQLite database, apply rules to process emails, and take actions based on those rules.

## Installation

1. Clone the repository:

git clone https://github.com/advaith-raij/gmail-backend-script.git

2. Navigate to the project directory:

cd gmail-backend-script

3. Install dependencies using pip:

pip install -r requirements.txt

## Setup

1. Enable the Gmail API:
    - Go to the [Google Developers Console](https://console.developers.google.com/).
    - Create a new project (or select an existing one).
    - Enable the Gmail API for your project.
    - Create credentials for a desktop application.
    - Download the credentials JSON file and save it as `credentials.json` in the project directory.

2. Run the script:
    - Execute the script by running the following command:
    
    ```
    python gmail_script.py
    ```

    - Follow the instructions to authenticate with your Google account and grant necessary permissions.
    - The script will fetch emails, store them in a SQLite database, and apply rules defined in `rules.json`.

3. Define rules:
    - Edit the `rules.json` file to define rules for processing emails.
    - Each rule should specify conditions and actions to be taken if conditions are met.

4. Customize:
    - Modify the script as needed to add more functionality or tailor it to your specific use case.

## Usage

- Running the script will automatically fetch emails, store them in the database, apply rules, and perform actions based on those rules.

- Modify the script or rules as necessary to suit your requirements.