import json
import os

class AccountControl:
    def __init__(self, filename="assets/account.json"):
        self.filename = filename

    def write_account(self, username, fullname):
        """Creates or overwrites the account.json file, ensuring the folder exists."""
        data = {
            "username": username,
            "fullname": fullname
        }
        
        try:
            # Get the directory path (e.g., 'assets')
            directory = os.path.dirname(self.filename)
            
            # If the directory path isn't empty and doesn't exist, create it
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")

            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Account successfully written to {self.filename}")
            
        except Exception as e:
            print(f"Error writing account: {e}")

    def read_account(self):
        """Reads the account data if file exists; otherwise returns None."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                return data.get("username"), data.get("fullname")
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error reading account: {e}")
                return None, None
        else:
            print(f"{self.filename} does not exist.")
            return None, None

    def update_account(self, username, fullname):
        """Updates the account if it exists, otherwise creates a new one."""
        if os.path.exists(self.filename):
            print("Updating existing account...")
        else:
            print("Account not found. Preparing new folder and record...")
        
        self.write_account(username, fullname)