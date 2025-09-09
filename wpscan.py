import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import re
import requests
import json
import argparse
import random
import string


class Email:
    """Base class for handling email operations.
    
    This is an abstract base class that defines the interface for email operations.
    Concrete implementations should override get_message and get_messages methods.
    
    Attributes:
        username (str): The username part of the email address (before @)
        domain (str): The domain part of the email address (after @)
    """
    
    username: str
    domain: str

    def __init__(self, username: str, domain: str):
        """Initialize an Email instance.
        
        Args:
            username (str): The username part of the email address
            domain (str): The domain part of the email address
        """
        self.username = username
        self.domain = domain

    def as_dict(self) -> dict:
        """Convert email details to a dictionary.
        
        Returns:
            dict: A dictionary containing username and domain
        """
        return {
            "username": self.username,
            "domain": self.domain
        }
    
    def get_address(self) -> str:
        """Get the complete email address.
        
        Returns:
            str: The full email address in format username@domain
        """
        return self.username + "@" + self.domain
    
    def get_message(self, message_id):
        """Retrieve a specific email message. To be implemented by subclasses.
        
        Args:
            message_id: The ID of the message to retrieve
            
        Returns:
            The email message content
        """
        pass

    def get_messages(self):
        """Retrieve all email messages. To be implemented by subclasses.
        
        Returns:
            A list of email messages
        """
        pass


class FviainboxesEmailProvider:
    """Provider class for interacting with the Fviainboxes email service.
    
    This class provides static methods to interact with the Fviainboxes API,
    including making HTTP requests and retrieving available email domains.
    
    Class Attributes:
        API_ROUTE (str): Base URL for the Fviainboxes API
        HEADERS (dict): Default headers including authorization token
    """
    
    API_ROUTE: str = "https://fviainboxes.com/"
    HEADERS: dict = {
        "Authorization": "Bearer af2b556e5e719052ca9193bace296b4fe9015bdc6c2c6ec28447d57c56187941"
    }

    @staticmethod
    def request(route: str, params: dict = {}) -> requests.Response:
        """Make a GET request to the Fviainboxes API.
        
        Args:
            route (str): The API endpoint to request
            params (dict, optional): Query parameters to include. Defaults to {}.
            
        Returns:
            requests.Response: The response from the API
        """
        return requests.get(
            url=FviainboxesEmailProvider.API_ROUTE + route,
            params=params,
            headers=FviainboxesEmailProvider.HEADERS
        )
    
    @staticmethod
    def get_domains() -> list[str]:
        """Retrieve available email domains from Fviainboxes.
        
        Returns:
            list[str]: List of available domain names. Returns empty list on error.
        """
        r = FviainboxesEmailProvider.request("domains")
        if r.ok:
            return r.json()["result"]
        
        return []
    
class FviainboxesEmail(Email):
    """Implementation of Email class for the Fviainboxes service.
    
    This class provides concrete implementations for retrieving email messages
    from the Fviainboxes service.
    """
    
    def get_messages(self) -> list[dict]:
        """Retrieve all messages for this email account.
        
        Returns:
            list[dict]: List of message objects containing email details
            
        Raises:
            Exception: If the API request fails
        """
        r = FviainboxesEmailProvider.request(
            route="messages",
            params={
                "username": self.username,
                "domain": self.domain
            }
        )
        if r.ok:
            return r.json()["result"]
        
        raise Exception(f"Failed to get Email-Messages. Email: {self.get_address()}")
    
    def get_message(self, message_id: str) -> str | None:
        """Retrieve a specific message by its ID.
        
        Args:
            message_id (str): The unique identifier of the email message
            
        Returns:
            str | None: The message content if successful, None otherwise
            
        Raises:
            Exception: If the API request fails
        """
        r = FviainboxesEmailProvider.request(
            route="message",
            params={
                "username": self.username,
                "domain": self.domain,
                "id": message_id
            }
        )
        if r.ok:
            return r.text
        else:
            raise Exception(f"Failed to get Email-Message. Email: {self.get_address()} | Email-Id: {message_id}")

def get_random_email_usernames(count: int = 1, min_length: int = 12, max_length: int = 16) -> list[str]:
    """Generate random email usernames.
    
    Args:
        count (int, optional): Number of usernames to generate. Defaults to 1.
        min_length (int, optional): Minimum length of each username. Defaults to 12.
        max_length (int, optional): Maximum length of each username. Defaults to 16.
        
    Returns:
        list[str]: List of unique random usernames
    """
    usernames = set()
    while len(usernames) < count:
        length = random.randint(min_length, max_length)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        usernames.add(username)
    return list(usernames)

def get_random_name() -> str:
    """Get a random name from a predefined list.
    
    Returns:
        str: A randomly selected name
    """
    names = [
        "Amir", "Sophia", "Liam", "Olivia", "Noah", "Emma", "Mason", "Ava", "Lucas", "Isabella",
        "Ethan", "Mia", "Logan", "Charlotte", "James", "Amelia", "Benjamin", "Harper", "Elijah", "Evelyn"
    ]
    return random.choice(names)

def get_random_password(min_length: int = 15, max_length: int = 30) -> str:
    """Generate a random password with specified length constraints.
    
    The password includes lowercase and uppercase letters, digits, and special characters.
    
    Args:
        min_length (int, optional): Minimum password length. Defaults to 15.
        max_length (int, optional): Maximum password length. Defaults to 30.
        
    Returns:
        str: A randomly generated password
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(chars, k=length))

class WPScanAccount:
    """Class for managing WPScan user accounts.
    
    This class handles all WPScan account operations including registration,
    activation, login, and API token retrieval.
    
    Attributes:
        API_URL (str): Base URL for the WPScan API
        email (Email): Email object for the account
        password (str): Account password
        session (requests.Session): HTTP session for making requests
    """
    
    API_URL: str = "https://wpscan.com/wp-json/wpscan/v1/"

    email: Email
    password: str
    session: requests.Session

    def __init__(self, email: Email, password: str, hcp: str):
        """Initialize a WPScan account.
        
        Args:
            email (Email): Email object for account creation/management
            password (str): Password for the account
            hcp (str): HCP token for authentication
        """
        self.email = email
        self.password = password
        self.session = requests.Session()

        self.session.headers = {
            "Cookie": f"_hcp={hcp}"
        }

    
    def activate_account(self) -> bool:
        """Activate the WPScan account using the activation link from email.
        
        This method:
        1. Retrieves activation email from the inbox
        2. Extracts the activation token
        3. Submits the token to activate the account
        
        Returns:
            bool: True if activation was successful, False otherwise
            
        Raises:
            Exception: If activation fails or activation email cannot be found
        """
        wpscan_emails = list(
            filter(
                lambda x: x["from"] == "security@wpscan.com",
                self.email.get_messages()
            )
        )
        if wpscan_emails:
            _email_id = wpscan_emails[0]["id"]
            _email_text= self.email.get_message(_email_id)
            match = re.search(
                r"https://wpscan\.com/confirm\?token=([A-Za-z0-9]+)",
                _email_text
            )
            if match:
                acitvation_token = match.group(1)
                r = self.session.post(
                    url=self.API_URL + "confirmation",
                    json={"token":acitvation_token}
                )
                if r.ok:
                    return r.json()["success"]
                
                else:
                    raise Exception(f"Activation Request Failed for Email: {self.email.get_address()} | Status Code: {r.status_code}")
            else:
                raise Exception(f"Can't find the activation link from the Email: {self.email.get_address()} | Emaid-id: {_email_id}")
                
        return False
    
    def login(self) -> bool:
        """Log in to the WPScan account.
        
        Returns:
            bool: True if login was successful, False otherwise
            
        Raises:
            Exception: If login request fails
        """
        r = self.session.post(
            url=self.API_URL + "sign-in",
            json={
                "email":self.email.get_address(),
                "password": self.password,
                "remember_me": True
            },
            allow_redirects=True
        )

        if r.ok:
            return r.json()["success"]
        else:
            raise Exception(f"Login Request failed on Email {self.email.get_message()} | Status Code: {r.status_code}")
            
    def get_profile(self) -> dict:
        """Retrieve the user's WPScan profile information.
        
        Returns:
            dict: User profile data
            
        Raises:
            Exception: If profile request fails
        """
        r = requests.get(self.API_URL + "users", cookies=self.session.cookies)
        if r.ok:
            return r.json()["data"]
        
        raise Exception(f"Profile Request failed on Email {self.email.get_message()} | Status Code: {r.status_code}")

    
    def get_token(self) -> str:
        """Retrieve the WPScan API token from the user's profile.
        
        Returns:
            str: The API token if available, None otherwise
        """
        profile = self.get_profile()
        return profile["api"]["token"] if profile else None
            
    
    def register(self):
        """Register a new WPScan account.
        
        Creates a new account with random name and the specified email/password.
        Additional fields are left empty and newsletter is disabled.
        
        Raises:
            Exception: If registration fails
        """
        r = self.session.post(
            url=self.API_URL + "sign-up",
            json={
                "user": {
                    "name": get_random_name(),
                    "email": self.email.get_address(),
                    "password": self.password,
                    "password_confirmation": self.password,
                    "homepage": "",
                    "twitter": "",
                    "address_line1": "",
                    "address_line2": "",
                    "address_city": "",
                    "address_postal_code": "",
                    "address_state": "",
                    "address_country": "",
                    "tax_id_data_type": "",
                    "tax_id_data_value": "",
                    "newsletter": False,
                    "terms_accepted":True
                }
            }
        )
        if r.status_code != 200:
            raise Exception(f"Failed to create account with ({self.email}) Email. Error: {r.json()['message']}")

def create_accounts(
        wpscan_hcp: str,
        count = 1,
        username_min_length = 12,
        username_max_length = 16,
        password_min_length = 15,
        password_max_length = 30,
) -> list[dict]:
    """Create multiple WPScan accounts with random credentials.
    
    This function handles the complete account creation process including:
    1. Generating random email addresses
    2. Creating accounts with random passwords
    3. Activating accounts via email verification
    4. Logging in and retrieving API tokens
    
    Args:
        wpscan_hcp (str): WPScan HCP token for authentication
        count (int, optional): Number of accounts to create. Defaults to 1.
        username_min_length (int, optional): Minimum length for email usernames. Defaults to 12.
        username_max_length (int, optional): Maximum length for email usernames. Defaults to 16.
        password_min_length (int, optional): Minimum password length. Defaults to 15.
        password_max_length (int, optional): Maximum password length. Defaults to 30.
        
    Returns:
        list[dict]: List of created accounts with their credentials and API tokens
        
    Note:
        The function shows live progress and results using rich console formatting
    """
    usernames = get_random_email_usernames(
        count=count,
        min_length=username_min_length,
        max_length=username_max_length
    )

    passwords = [get_random_password(
        min_length=password_min_length,
        max_length=password_max_length
    ) for _ in range(count)]

    domains = FviainboxesEmailProvider.get_domains()
    emails = [FviainboxesEmail(username, random.choice(domains)) for username in usernames]

    accounts = []
    for account_num, (password, email) in enumerate(zip(passwords, emails), 1):
        # Create summary panel
        summary = Panel(
            f"[bold blue]Creating Account {account_num}/{count}[/bold blue]\n"
            f"[yellow]Email:[/yellow] {email.get_address()}",
            title="[bold green]New Account Creation[/bold green]",
            border_style="green"
        )
        console.print(summary)
        
        wpscan_account = WPScanAccount(email, password, wpscan_hcp)
        
        # Setup progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Registration step
            task_register = progress.add_task("[yellow]Registering account...", total=None)
            try:
                wpscan_account.register()
                progress.update(task_register, description="[green]✓ Account registered successfully")
            except Exception as e:
                progress.update(task_register, description=f"[red]✗ Registration failed: {str(e)}")
                continue

            # Activation step
            task_activate = progress.add_task("[yellow]Activating account...", total=None)
            tries = 5
            _continue = True
            while True:
                tries -= 1
                try:
                    if wpscan_account.activate_account():
                        progress.update(task_activate, description="[green]✓ Account activated successfully")
                        break
                    progress.update(task_activate, description="[red]Activation failed, retrying...")
                except Exception as e:
                    progress.update(task_activate, description=f"[red]✗ Activation error: {str(e)}")
                    _continue = False
                    break

                if tries == 0:
                    progress.update(task_activate, description="[red]✗ Maximum activation attempts exceeded")
                    _continue = False
                    break

                time.sleep(3)
            
            if not _continue:
                continue

            # Login step
            task_login = progress.add_task("[yellow]Logging in...", total=None)
            try:
                if wpscan_account.login():
                    progress.update(task_login, description="[green]✓ Login successful")
                else:
                    progress.update(task_login, description="[red]✗ Login failed")
                    continue
            except Exception as e:
                progress.update(task_login, description=f"[red]✗ Login error: {str(e)}")
                continue

            # Token retrieval step
            task_token = progress.add_task("[yellow]Retrieving API token...", total=None)
            try:
                token = wpscan_account.get_token()
                if token:
                    progress.update(task_token, description="[green]✓ API token retrieved")
                else:
                    progress.update(task_token, description="[red]✗ Failed to get API token")
                    continue
            except Exception as e:
                progress.update(task_token, description=f"[red]✗ Token retrieval error: {str(e)}")
                continue

        # Account creation successful - show details
        accounts.append({
            "email": wpscan_account.email.get_address(),
            "password": wpscan_account.password,
            "api": token
        })

        # Display account information in a table
        table = Table(title="[bold green]Account Created Successfully[/bold green]", border_style="green")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="yellow")
        table.add_row("Email", wpscan_account.email.get_address())
        table.add_row("Password", wpscan_account.password)
        table.add_row("API Token", token)
        console.print("\n")  # Add some spacing
        console.print(table)
    
    return accounts

def save_accounts(filename: str, accounts: list[dict]):
    """Save WPScan accounts to a JSON file.
    
    The accounts are saved along with an index counter for account rotation.
    
    Args:
        filename (str): Path to the file where accounts will be saved
        accounts (list[dict]): List of account dictionaries containing email, password, and API token
    """
    with open(filename, "w+") as file:
        file.write(
            json.dumps(
                {
                    "index": -1,
                    "accounts": accounts
                }
            )
        )

def load_accounts(filepath: str) -> tuple[list[dict], int]:
    """Load WPScan accounts and current rotation index from a file.
    
    Args:
        filepath (str): Path to the accounts file
        
    Returns:
        tuple[list[dict], int]: A tuple containing:
            - List of account dictionaries
            - Current rotation index (-1 if no accounts or file not found)
    """
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            return data.get("accounts", []), data.get("index", -1)
    except (FileNotFoundError, json.JSONDecodeError):
        return [], -1

def save_account_index(filepath: str, index: int):
    """Update the account rotation index in the accounts file.
    
    Args:
        filepath (str): Path to the accounts file
        index (int): New rotation index to save
        
    Note:
        Silently fails if the file cannot be read or written,
        allowing the program to continue with default values
    """
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
        data["index"] = index
        with open(filepath, 'w') as file:
            json.dump(data, file)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

console = Console()

def display_banner():
    """Display the program banner with Naderidev text and GitHub link."""

    NADERIDEV_BANNER = r"""
        _   __          __           _     __          
       / | / /___ _____/ /__  _____(_)___/ /__ _   __
      /  |/ / __ `/ __  / _ \/ ___/ / __  / _ \ | / /
     / /|  / /_/ / /_/ /  __/ /  / / /_/ /  __/ |/ / 
    /_/ |_/\__,_/\__,_/\___/_/  /_/\__,_/\___/|___/  
    """
    console.print(f"[bold cyan]{NADERIDEV_BANNER}[/bold cyan]", end='')
    info_line = "[bold green]WPScan Account Manager[/bold green] | [bold cyan]Naderidev[/bold cyan] : [link=https://github.com/naderidev]github.com/naderidev[/link]"
    console.print(info_line)
    console.print()


def run_wpscan_command(args: list[str], accounts_file: str):
    """Execute WPScan with account rotation and live output display.
    
    This function:
    1. Loads accounts from the specified file
    2. Rotates to the next account in sequence
    3. Displays the currently used account
    4. Runs WPScan with the account's API token
    5. Shows live, formatted output from WPScan
    
    Args:
        args (list[str]): Command line arguments to pass to WPScan
        accounts_file (str): Path to the file containing WPScan accounts
        
    Note:
        - Shows real-time WPScan output with color coding
        - Maintains a rotation index in the accounts file
        - Formats the output for better readability
    """
    # Load accounts and get next account to use
    accounts, current_index = load_accounts(accounts_file)
    if not accounts:
        console.print("[red]No accounts found in the accounts file![/red]")
        return

    # Get next account
    next_index = (current_index + 1) % len(accounts)
    account = accounts[next_index]
    
    # Save the new index
    save_account_index(accounts_file, next_index)
    
    # Display the account being used
    account_table = Table(title="[bold blue]Using Account[/bold blue]", border_style="blue")
    account_table.add_column("Field", style="cyan")
    account_table.add_column("Value", style="yellow")
    account_table.add_row("Email", account["email"])
    account_table.add_row("API Token", account["api"])
    console.print(account_table)
    
    # Build and run wpscan command
    cmd_args = ["wpscan"] + args + ["--api-token", account["api"]]

    # Run the command
    import subprocess
    try:
        with subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, shell=True) as proc:
            for line in iter(proc.stdout.readline, ''):
                print(line.rstrip())

    except Exception as e:
        console.print(f"[red]Error running WPScan: {str(e)}[/red]")

def main():
    console = Console()
    display_banner()
    parser = argparse.ArgumentParser(description="WPScan Account Manager and Runner")
    parser.add_argument("command", help="Command to run (create-account or scan)")
    
    # Arguments for create_account
    parser.add_argument("--wpscan-hcp", help="WPScan HCP token")
    parser.add_argument("--count", type=int, default=1, help="Number of accounts to create")
    parser.add_argument("--username-min-length", type=int, default=12, help="Minimum username length")
    parser.add_argument("--username-max-length", type=int, default=16, help="Maximum username length")
    parser.add_argument("--password-min-length", type=int, default=15, help="Minimum password length")
    parser.add_argument("--password-max-length", type=int, default=30, help="Maximum password length")
    parser.add_argument("--output", default="accounts.txt", help="Path to save the accounts")
    
    # Argument for accounts file location (used in wpscan mode)
    parser.add_argument("--accounts", help="Path to the accounts file")
    
    args, unknown_args = parser.parse_known_args()
    
    if args.command == "create-account":
        if not args.wpscan_hcp:
            console.print("[red]Error: --wpscan-hcp is required for create_account command[/red]")
            return
            
        accounts = create_accounts(
            wpscan_hcp=args.wpscan_hcp,
            count=args.count,
            username_min_length=args.username_min_length,
            username_max_length=args.username_max_length,
            password_min_length=args.password_min_length,
            password_max_length=args.password_max_length
        )
        
        if accounts:
            console.print("\n[bold green]== Final Summary ==[/bold green]")
            summary_table = Table(title="[bold blue]Created Accounts[/bold blue]", border_style="blue")
            summary_table.add_column("Email", style="cyan")
            summary_table.add_column("Password", style="yellow")
            summary_table.add_column("API Token", style="green")
            
            for account in accounts:
                summary_table.add_row(account["email"], account["password"], account["api"])
            
            console.print(summary_table)
            save_accounts(args.output, accounts)
            console.print(f"\n[bold green]✓ Accounts Saved to {args.output}![/bold green]")
    elif args.command == "scan":
        if not args.accounts:
            console.print("[red]Error: --accounts parameter is required for wpscan command[/red]")
            return
        
        # Remove --accounts from unknown_args if present
        filtered_args = [arg for arg in unknown_args if not arg.startswith("--accounts")]
        run_wpscan_command(filtered_args, args.accounts)

if __name__ == "__main__":
    main()

