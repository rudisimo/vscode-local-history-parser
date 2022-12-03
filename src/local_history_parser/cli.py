import logging
from argparse import ArgumentParser, FileType
from pathlib import Path
from sys import stdout
from zoneinfo import ZoneInfo

from . import VERSION
from .history import (
    HistorySortOrder,
    HistoryStreamer,
    build_record_filter,
    build_snapshot_filter,
)
from .util import setup_logging

LOGGER = logging.getLogger(__name__)
TZINFO = ZoneInfo("America/New_York")


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="lhp", description="Parse local history files.")

    # Default arguments
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    parser.add_argument(
        "path",
        type=Path,
        # default=locate_user_storage_dir(),
        help="Path to storage location of local history files",
    )
    parser.add_argument(
        "file",
        type=FileType(mode="w", encoding="UTF-8"),
        default=stdout,
        nargs="?",
        help="Where to store the local history results (default: stdout)",
    )

    # Output options
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        default=1,
        action="count",
        help="Increase output verbosity (can be used multiple times)",
    )
    output_group.add_argument(
        "-q",
        "--quiet",
        dest="verbosity",
        const=0,
        action="store_const",
        help="Disable output verbosity",
    )

    # Snapshot filter options
    filter_group = parser.add_argument_group("snapshot filters")
    latest_group = filter_group.add_mutually_exclusive_group()
    latest_group.add_argument(
        "-o",
        "--oldest",
        dest="filter_order",
        action="store_const",
        const=HistorySortOrder.OLDEST,
        help="Show only the oldest snapshot",
    )
    latest_group.add_argument(
        "-n",
        "--newest",
        dest="filter_order",
        action="store_const",
        const=HistorySortOrder.NEWEST,
        help="Show only the newest snapshot",
    )
    filter_group.add_argument(
        "-r",
        "--regex",
        dest="filter_regex",
        help="Show snapshots matching the specified regular expression",
    )
    filter_group.add_argument(
        "-s",
        "--since",
        dest="filter_since",
        help="Show snapshots not older than the specified date",
    )
    filter_group.add_argument(
        "-u",
        "--until",
        dest="filter_until",
        help="Show snapshots not newer than the specified date",
    )

    return parser


def main():
    # Parse CLI arguments
    args_parser = build_parser()
    args = args_parser.parse_args()

    # Configure logger
    setup_logging(verbosity=args.verbosity)

    # Search local history files
    streamer = HistoryStreamer(path=args.path, out=args.file)
    LOGGER.info("Found %d history record(s) at %s", len(streamer), args.path)

    # Filter local history records
    record_filter = build_record_filter(regex=args.filter_regex)
    with streamer.filter(record_filter) as filtered_records:
        LOGGER.info("Filtered %d history record(s)", len(filtered_records))

        # Process local history records
        for _, record in enumerate(filtered_records):
            LOGGER.info("Processing history record: %s", record.source_file)
            LOGGER.debug("%s", record)
            LOGGER.info(
                "Found %d history snapshot(s) for %s", len(record), record.target_file
            )

            # Filter local history snapshots
            snapshot_filter = build_snapshot_filter(
                since=args.filter_since, until=args.filter_until
            )
            with record.filter(snapshot_filter, order=args.filter_order) as snapshots:
                LOGGER.info("Filtered %d history snapshot(s)", len(snapshots))

                # Process local history snapshots
                for snapshot_idx, snapshot in enumerate(snapshots):
                    LOGGER.info("Processing history snapshot: %s", snapshot.source_file)
                    LOGGER.debug("%s", snapshot)

                    # Write the history snapshot to the output stream
                    streamer.write(
                        f"{record.target_file},{snapshot.source_file},{snapshot.created_on}"
                    )

                    # Process a single history snapshot when using order filter
                    if snapshot_idx == 0 and args.filter_order is not None:
                        LOGGER.debug("Stopping after a single history snapshot")
                        break

    # Output stats
    LOGGER.info("Pushed %d history record(s) to stream", streamer.records_written)
