"""
Centralized logging setup for the pipeline. Every stage (extract, transform,
load) logs to both the console and a run log file, so a pipeline run can be
audited after the fact - the same "what happened and when" visibility you'd
want in any production data pipeline.
"""
import logging
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # avoid duplicate handlers if called more than once

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(LOG_DIR / "pipeline_run.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
