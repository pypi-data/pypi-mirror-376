# __main__.py
from nemo_library.adapter.inforcom.flow import inforcom_flow
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

    # Database credentials / connection
    parser.add_argument("--odbc-connstr", help="ODBC connection string", default=None, required=False)
    parser.add_argument("--odbc-dsn", help="ODBC DSN name", default=None, required=False)
    parser.add_argument("--user", help="Database user", default=None, required=False)
    parser.add_argument("--password", help="Database password", default=None, required=False)

    args = parser.parse_args()

    if args.only:
        args.bextract = args.only == "extract"
        args.btransform = args.only == "transform"
        args.bload = args.only == "load"

    # Run the flow with the given arguments
    inforcom_flow(
        bextract=args.bextract,
        btransform=args.btransform,
        bload=args.bload,
        odbc_connstr=args.odbc_connstr,
        odbc_dsn=args.odbc_dsn,
        user=args.user,
        password=args.password,
    )


if __name__ == "__main__":
    main()
