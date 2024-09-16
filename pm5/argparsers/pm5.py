import argparse


def get_app_args():
    parser = argparse.ArgumentParser(description="Like pm2 but without node.js.")

    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser(
        "start", help="Start the process manager daemon"
    )
    start_parser.add_argument(
        "-c",
        "--config_file",
        help="The ecosystem configuration file.",
        required=False,
        default="./ecosystem.config.json",
        type=str,
    )
    start_parser.add_argument(
        "--debug",
        action="store_true",
        help="Do not run the process manager as a daemon",
    )

    subparsers.add_parser("status", help="Get the status of the process manager daemon")

    subparsers.add_parser("stop", help="Stop the process manager daemon")

    args = vars(parser.parse_args())

    return args
