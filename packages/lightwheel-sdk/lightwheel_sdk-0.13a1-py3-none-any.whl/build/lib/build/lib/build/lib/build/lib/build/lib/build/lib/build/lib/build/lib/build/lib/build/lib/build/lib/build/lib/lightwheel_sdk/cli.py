import argparse
from lightwheel_sdk.loader import login_manager


def login(args):
    login_manager.login(force_login=True, username=args.username, password=args.password)


def main():
    """Main entry point for the lightwheel CLI."""
    parser = argparse.ArgumentParser(description="Lightwheel SDK CLI", prog="lightwheel")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Login subcommand
    parser_login = subparsers.add_parser("login", help="Log in to Lightwheel")
    parser_login.add_argument("--username", required=False, help="Username for login")
    parser_login.add_argument("--password", required=False, help="Password for login")

    args = parser.parse_args()

    if args.command == "login":
        login(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
