import argparse


def get_app_args():
    parser = argparse.ArgumentParser(description="Like pm2 but without node.js.")

    parser.add_argument(
        "-c",
        "--config_file",
        help="The ecosystem configuration file.",
        required=False,
        default="./ecosystem.config.json",
        type=str,
    )

    args = vars(parser.parse_args())

    return args
