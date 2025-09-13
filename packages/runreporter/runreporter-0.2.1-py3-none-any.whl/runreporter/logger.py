import logging
from contextlib import contextmanager
from typing import List
from logging import Logger


class ErrorTrackingLogger:
	"""Wrapper around Python logger to track if any error/exception was logged.
	Поддерживает стек контекстов для пометки сообщений."""

	def __init__(self, logger: Logger) -> None:
		self._logger = logger
		self._had_error = False
		self._context_stack: List[str] = []

	def _mark_error(self) -> None:
		self._had_error = True

	@property
	def had_error(self) -> bool:
		return self._had_error

	def _with_ctx(self, msg: str) -> str:
		if not self._context_stack:
			return msg
		ctx = " > ".join(self._context_stack)
		return f"[{ctx}] {msg}"

	def debug(self, msg: str, *args, **kwargs) -> None:
		self._logger.debug(self._with_ctx(msg), *args, **kwargs)

	def info(self, msg: str, *args, **kwargs) -> None:
		self._logger.info(self._with_ctx(msg), *args, **kwargs)

	def warning(self, msg: str, *args, **kwargs) -> None:
		self._logger.warning(self._with_ctx(msg), *args, **kwargs)

	def error(self, msg: str, *args, **kwargs) -> None:
		self._mark_error()
		self._logger.error(self._with_ctx(msg), *args, **kwargs)

	def exception(self, msg: str, *args, exc_info: bool = True, **kwargs) -> None:
		self._mark_error()
		self._logger.error(self._with_ctx(msg), *args, exc_info=exc_info, **kwargs)

	def critical(self, msg: str, *args, **kwargs) -> None:
		self._mark_error()
		self._logger.critical(self._with_ctx(msg), *args, **kwargs)

	@contextmanager
	def context(self, name: str):
		self._context_stack.append(str(name))
		try:
			yield self
		finally:
			self._context_stack.pop()


def create_file_logger(name: str, log_file_path: str, level: int = logging.INFO) -> ErrorTrackingLogger:
	logger = logging.getLogger(name)
	logger.setLevel(level)
	logger.propagate = False

	# Avoid duplicate handlers if called multiple times
	if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == log_file_path for h in logger.handlers):
		file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
		formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
		file_handler.setFormatter(formatter)
		logger.addHandler(file_handler)

	return ErrorTrackingLogger(logger)