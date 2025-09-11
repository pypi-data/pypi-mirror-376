from nemo_library.adapter.inforcom.flow import inforcom_flow

import getpass

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the InforCom ETL flow with optional step toggles."
    )

    # Main step toggles
    parser.add_argument(
        "--extract",
        dest="bextract",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run extract step (use --no-extract to skip).",
    )
    parser.add_argument(
        "--transform",
        dest="btransform",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run transform step (use --no-transform to skip).",
    )
    parser.add_argument(
        "--load",
        dest="bload",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run load step (use --no-load to skip).",
    )

    # Convenience: run exactly one main step
    parser.add_argument(
        "--only",
        choices=["extract", "transform", "load"],
        help="Run exactly one main step and skip the others.",
    )

    # Choose exactly one: full ODBC connection string OR DSN (+ optional credentials)
    parser.add_argument(
        "--odbc_connstr",
        type=str,
        help='Full ODBC connection string, e.g. "DRIVER={Oracle in OraClient11g_home1};DBQ=PROD71.db-infor71;UID=read;PWD=read"',
    )
    parser.add_argument("--odbc_dsn", type=str, help='ODBC DSN name, e.g. "Infor Prod"')
    parser.add_argument(
        "--user",
        type=str,
        help="Username for DSN-based connection (optional if DSN stores it)",
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Password for DSN-based connection (if omitted, will prompt)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="ODBC connection/query timeout in seconds",
    )

    args = parser.parse_args()

    if args.only:
        args.bextract = args.only == "extract"
        args.btransform = args.only == "transform"
        args.bload = args.only == "load"

    # Validation: exactly one of odbc_connstr or odbc_dsn must be given
    if args.bextract:
        if bool(args.odbc_connstr) == bool(args.odbc_dsn):
            raise SystemExit("Provide exactly one of --odbc_connstr OR --odbc_dsn.")

        effective_connstr = args.odbc_connstr
        effective_password = args.password

        # Build connection string from DSN if needed
        if args.odbc_dsn:
            # Prompt for password if user is given but no password provided
            if args.user and not effective_password:
                effective_password = getpass.getpass("Database password: ")

            parts = [f"DSN={args.odbc_dsn}"]
            if args.user:
                parts.append(f"UID={args.user}")
            if effective_password:
                parts.append(f"PWD={effective_password}")
            effective_connstr = ";".join(parts)

    # Run the flow with the given arguments
    inforcom_flow(
        bextract=args.bextract,
        btransform=args.btransform,
        bload=args.bload,
        odbc_connstr=effective_connstr if args.bextract else "",
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
