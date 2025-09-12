from aiohttp import ClientOSError
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

from .exceptions import str_exception
from .logger import get_logger


logger = get_logger(__name__)


def log_before_sleep(retry_state):
    attempt_number = retry_state.attempt_number
    last_exception = retry_state.outcome.exception()
    entry_point = retry_state.fn.__name__
    logger.info(f'Retry: {attempt_number=}, {entry_point=}, {last_exception=}')


def log_after_retry(retry_state):
    attempt_number = retry_state.attempt_number
    is_last_exception = (
        retry_state.retry_object.stop.max_attempt_number == attempt_number
    )
    if is_last_exception and retry_state.outcome.failed:
        last_exception = (
            retry_state.outcome.exception() if retry_state.outcome else None
        )
        exc_traceback = str_exception(last_exception) if last_exception else 'retry_exc'
        entry_point = retry_state.fn.__name__
        error_message = f"Retry final attempt {attempt_number=}, {entry_point=}, {exc_traceback=}"
        logger.error(error_message)


retry_params = dict(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    before_sleep=log_before_sleep,
    after=log_after_retry
)


retry_helper = retry(**retry_params)


retry_api_helper = retry(
    retry=retry_if_exception_type(ClientOSError),
    **retry_params
)
