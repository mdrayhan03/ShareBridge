import json
import logging
import os
import shutil

log = logging.getLogger(__name__)

# Old location: inside the app folder. On a desktop update the app folder is
# replaced, which would wipe the profile — so we now store account.json in the
# per-user data dir instead, and migrate any old copy across once.
LEGACY_PATH = "assets/account.json"


def _default_account_path():
    """account.json inside the per-user data dir (survives app updates)."""
    try:
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if app is not None:
            return os.path.join(app.user_data_dir, "account.json")
    except Exception:
        pass
    # Fallback when there's no running app (e.g. unit tests).
    return LEGACY_PATH


class AccountControl:
    def __init__(self, filename=None):
        if filename is None:
            self.filename = _default_account_path()
            self._migrate_legacy()
        else:
            self.filename = filename

    def _migrate_legacy(self):
        """One-time copy of an old assets/account.json into the user data dir."""
        try:
            if (
                self.filename != LEGACY_PATH
                and not os.path.exists(self.filename)
                and os.path.exists(LEGACY_PATH)
            ):
                directory = os.path.dirname(self.filename)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                shutil.copyfile(LEGACY_PATH, self.filename)
                log.info(f"Migrated legacy account to {self.filename}")
        except Exception as e:
            log.error(f"Account migration failed: {e}")

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
                log.info(f"Created directory: {directory}")

            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4)
            log.info(f"Account successfully written to {self.filename}")
            
        except Exception as e:
            log.error(f"Error writing account: {e}")

    def read_account(self):
        """Reads the account data if file exists; otherwise returns None."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                return data.get("username"), data.get("fullname")
            except (json.JSONDecodeError, Exception) as e:
                log.error(f"Error reading account: {e}")
                return None, None
        else:
            log.info(f"{self.filename} does not exist.")
            return None, None

    def update_account(self, username, fullname):
        """Updates the account if it exists, otherwise creates a new one."""
        if os.path.exists(self.filename):
            log.info("Updating existing account...")
        else:
            log.info("Account not found. Preparing new folder and record...")
        
        self.write_account(username, fullname)