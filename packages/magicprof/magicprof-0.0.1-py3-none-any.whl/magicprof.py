from __future__ import annotations

import atexit
import cProfile
import functools
import logging
import os
import pathlib

logger_slug = "magicprof"
logger = logging.getLogger(logger_slug)


_prof: cProfile.Profile | None = None
_prof_file: pathlib.Path | None = None


@functools.cache
def _instrument():
    global _prof
    global _prof_file
    p = os.getenv("MAGICPROF")
    assert p is not None, (
        "magicprof: env var `MAGICPROF` must be set to enable profiling"
    )
    _prof_file = pathlib.Path(p)

    use_subcalls = os.getenv("MAGICPROF_DISABLE_SUBCALLS") is None
    use_builtins = os.getenv("MAGICPROF_DISABLE_BUILTINS") is None
    logger.debug(f"configuration: subcalls={use_subcalls} builtins={use_builtins}")

    _prof = cProfile.Profile(subcalls=use_subcalls, builtins=use_builtins)
    _prof.enable()
    logger.info("starting profiler")


@functools.cache
def _shutdown():
    global _prof
    global _prof_file
    if _prof is None:
        logger.debug("profiler was not instrumented")
        return
    _prof.disable()
    logger.debug("profiling stopped")

    _prof.dump_stats(_prof_file)
    logger.info(f"profile written to: {_prof_file!r}")


atexit.register(_shutdown)
