from argparse import ArgumentParser, ArgumentTypeError
from time import sleep

import sys

from config import Settings
from yc_module import NoInstancesException


def check_range_timedelta(value):
    ivalue = int(value)
    if ivalue < 5 or ivalue > 3600:
        raise ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue


parser: ArgumentParser = ArgumentParser(prog="batch_write_utils.py")
parser.add_argument(
    "-t",
    "--timedelta",
    type=check_range_timedelta,
    required=False,
    default=15,
    help="Время в секундах между повторными запросами от 5sec до 1h",
)
parser.add_argument(
    "-l",
    "--level",
    type=str,
    choices=["debug", "info"],
    default="info",
    help="уровень отладочной информации",
)


def main(argv):
    args = parser.parse_args()
    from logger import conf_logger

    conf_logger(args.level)

    import logging

    logger = logging.getLogger(__name__)

    from yc_module import up_instances

    config: Settings = Settings()

    try:
        while True:
            try:
                up_instances(config=config)

            except NoInstancesException as e:
                logger.info(e)
                break

            except Exception as e:
                logger.error(e)
                sleep(1)
                continue

            sleep(args.timedelta)

    except KeyboardInterrupt:
        logger.info("Background thread finished processing. Closing all threads")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
