import time
from unittest.mock import patch

from app import logger
from app.core.debug_helpers import log_function_enter_exit, timeit


def test_log_function_enter_exit():
    @log_function_enter_exit(entry=True, exit=True)
    def test_function(a: int, b: int) -> int:
        return a + b

    with patch.object(logger, "debug") as mock_logger:
        result = test_function(1, 2)

    assert result == 3
    assert mock_logger.called
    mock_logger.assert_any_call("Entering 'test_function' (args=(1, 2), kwargs={})")
    mock_logger.assert_any_call("Exiting 'test_function' (result=3, name=test_function)")


def test_timeit() -> None:
    @timeit
    def test_function(sleep_time: float = 0.1) -> None:
        time.sleep(sleep_time)

    with patch.object(logger, "debug") as mock_logger:
        test_function(sleep_time=0.1)
        test_function(sleep_time=0.15)
        mock_logger.assert_called()
        assert mock_logger.call_count == 2
