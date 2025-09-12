import json
import logging
from typing import Optional, Literal
import sys

from flask import has_request_context, request
from flask_log_request_id import current_request_id

STANDARD_FORMAT = '{"severity": "%(levelname)s", "logging.googleapis.com/trace": "%(cloud_trace)s", "component": "arbitrary", "message": %(message)s}'
def adscale_log(
    service: str,  # should be ValueOf ServiceEnum
    msg: str
    ):
    """Deprecated, should not be used anymore
    """
    request_id = None
    try:
        request_id = current_request_id()
    except KeyError:
        pass

    logging.info(f"[{service}][{request_id}] {msg}")


class RequestFormatter(logging.Formatter):
    """Logging Formatter to add request id and trace id to log records
    """
    def __init__(self,
            fmt: Optional[str] = STANDARD_FORMAT,
            datefmt: Optional[str] = None,
            style: Literal["%", "{", "$"] = "%",
            validate: bool = True,
            gcp_project: Optional[str] = None):

        super().__init__(fmt, datefmt, style, validate)
        self.gcp_project = gcp_project

    def format(self, record):
        if has_request_context():
            trace_header: str = request.headers.get("X-Cloud-Trace-Context")
            if trace_header:
                trace = trace_header.split("/")
                record.cloud_trace = f"projects/{self.gcp_project}/traces/{trace[0]}"
            else:
                record.cloud_trace = None
        else:
            record.cloud_trace = None

        # Handle exception information properly
        if record.exc_info:
            # Format the exception with stack trace as a single string
            exc_text = self.formatException(record.exc_info)
            # Combine the message with the exception info
            full_message = f"{record.getMessage()}\n{exc_text}"
        else:
            full_message = record.getMessage()

        # JSON encode the complete message to escape newlines and special characters
        record.msg = json.dumps(full_message)
        # Clear args to prevent double formatting
        record.args = None

        return super().format(record)

def setup_logging(
    fmt : Optional[str] = STANDARD_FORMAT,
    datefmt: Optional[str] = None,
    style   :  Literal["%", "{", "$"] = "%",
    validate: bool = True,
    gcp_project: Optional[str] = None,
    level = logging.INFO
):
    """
    Setup logging for the application
    """
    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setFormatter(
        RequestFormatter(
            fmt,
            datefmt,
            style,
            validate,
            gcp_project
        )
    )

    logging.basicConfig(
        level=level,
        handlers=[handler]
    )

    root = logging.getLogger()
    root.addHandler(handler)
    return root
