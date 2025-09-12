import time
import logging
import functools
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger("todds_timer")


class Timer:
    """
    A utility class for timing code execution and tracking performance.

    This class can be used as a function decorator or as a context manager to
    measure the execution time of specific code blocks or functions. It provides
    detailed logging of start and end times, as well as methods to analyze
    the collected timing data across multiple invocations.

    The Timer class is particularly useful for:
    - Identifying performance bottlenecks in your code
    - Tracking the execution time of specific functions or code blocks
    - Analyzing performance trends over multiple runs
    - Identifying which iteration of a loop is taking the most time

    The advantage of using the class as a decorator rather than a context
    manager is that you can include formatting placeholders in the task name
    that will be printed using the args and kwargs provided to the function,
    however the task name being tracked for the purpose of statistical analysis
    will be unchanged as the formatting is only applied to the log message.

    The class also maintains a history of execution times for each named task,
    allowing for statistical analysis of performance over time.

    Attributes
    ----------
    _nesting_level : int
        Tracks the current nesting level of timers, used for indentation in logs.
    _task_times : defaultdict
        Stores timing data for each task across multiple invocations.
    task_name : str
        The name of the current task being timed.
    args : tuple
        Positional arguments used for formatting the task name.
    kwargs : dict
        Keyword arguments used for formatting the task name.
    elapsed_times : list
        List of elapsed times for the current timer instance.

    Methods
    -------
    __enter__()
        Starts the timer when entering a context.
    __exit__(exc_type, exc_value, traceback)
        Stops the timer when exiting a context and logs the results.
    __call__(fn)
        Allows the Timer to be used as a decorator.
    get_average_time(task_name)
        Calculates the average execution time for a given task.
    print_average_times(sort=None, max_count=None)
        Prints a summary of timing statistics for all tracked tasks.

    Examples
    --------
    Using Timer as a context manager:
    >>> with Timer("Querying database"):
    ...     # Perform database query here
    ...     pass

    Using Timer as a decorator:
    >>> @Timer("Calculating sum of {0} and {1}")
    ... def perform_calculation(x, y):
    ...     # Perform calculation here
    ...     return x + y

    Analyzing timing results:
    >>> Timer.print_average_times(sort="average")
    """

    _nesting_level: int = 1  # Start at 1 to distinguish from ordinary log messages
    _task_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=120))
    log_level: int = logging.DEBUG

    def __init__(self, task_name: str, args: tuple = (), kwargs: dict = {}):
        """
        Initialize the Timer instance with a task name and optional formatting arguments.

        Parameters
        ----------
        task_name : str
            A descriptive name for the task being timed. This name is used in
            log messages and when aggregating timing data.
        args : tuple, optional
            Positional arguments to be used in formatting the task name string.
            Useful for creating dynamic task names.
        kwargs : dict, optional
            Keyword arguments to be used in formatting the task name string.
            Useful for creating dynamic task names with named parameters.

        Notes
        -----
        The task_name can include format specifiers that will be filled using
        args and kwargs. This allows for dynamic task names based on function
        arguments or other runtime information.
        """
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs
        self.elapsed_times: List[float] = []

    def __enter__(self) -> "Timer":
        """
        Start timing when entering the context.

        This method is called when the Timer is used in a 'with' statement.
        It logs the start of the timed section and increments the nesting level
        for proper indentation in nested timer calls.

        Returns
        -------
        Timer
            Returns self to allow access to the Timer instance within the context.

        Notes
        -----
        The start time is recorded and a debug log message is generated indicating
        the start of the timed section.
        """
        self.start_time = time.time()
        self.indent = "----" * Timer._nesting_level
        logger.log(Timer.log_level, f"{self.indent}STARTED {self.task_name.format(*self.args, **self.kwargs)}")
        Timer._nesting_level += 1
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Exception], traceback: Optional[Any]) -> None:
        """
        Stop timing when exiting the context and log the results.

        This method is called when exiting the 'with' block. It calculates the
        elapsed time, logs the completion, and stores the timing information
        for later analysis.

        Parameters
        ----------
        exc_type : type or None
            The type of the exception that was raised in the context, if any.
        exc_value : Exception or None
            The exception instance that was raised in the context, if any.
        traceback : traceback or None
            A traceback object encapsulating the call stack at the point where
            the exception occurred.

        Notes
        -----
        - The elapsed time is calculated and added to both the instance's
          elapsed_times list and the class's _task_times dictionary.
        - A debug log message is generated with the elapsed time and task completion.
        - The nesting level is decremented to maintain proper indentation for nested timers.
        """
        Timer._nesting_level -= 1
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.elapsed_times.append(elapsed_time)
        Timer._task_times[self.task_name].append(elapsed_time)
        formatted_time = f"{elapsed_time:06.3f}"
        logger.log(
            Timer.log_level,
            f"{self.indent}COMPLETED (in {formatted_time} seconds) "
            f"{self.task_name.format(*self.args, **self.kwargs)}",
        )

    def __call__(self, fn: Callable[P, R]) -> Callable[P, R]:
        """
        Allow the Timer to be used as a decorator preserving the wrapped function's type hints.

        This method enables the Timer class to be used as a function decorator,
        automatically timing the execution of the decorated function.

        Parameters
        ----------
        fn : callable
            The function to be timed.

        Returns
        -------
        callable
            A wrapper function that encapsulates the original function with
            timing functionality.

        Notes
        -----
        - The wrapper function uses the Timer as a context manager to time
          the execution of the original function.
        - The original function's metadata (name, docstring, etc.) is preserved
          using the @functools.wraps decorator.
        """

        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with Timer(self.task_name, args=args, kwargs=kwargs):
                return fn(*args, **kwargs)

        return wrapper

    @classmethod
    def set_log_level(cls, level: int) -> None:
        """
        Set the log level for all Timer instances.

        Parameters
        ----------
        level : int
            The logging level to use for Timer messages.
            Use standard logging module constants:
            logging.DEBUG, logging.INFO, logging.WARNING, etc.
        """
        cls.log_level = level

    @classmethod
    def get_average_time(cls, task_name: str) -> float:
        """
        Calculate the average execution time for a given task.

        This method computes the mean execution time of all recorded instances
        of the specified task.

        Parameters
        ----------
        task_name : str
            The name of the task for which to calculate the average time.

        Returns
        -------
        float
            The average execution time for the task in seconds.
            Returns 0 if no timing data is available for the task.

        Notes
        -----
        This method is useful for getting a quick overview of a task's
        typical performance. However, be aware that averages can be
        skewed by outliers in the timing data.
        """
        times = cls._task_times[task_name]
        return sum(times) / len(times) if times else 0

    @classmethod
    def print_average_times(
        cls,
        sort: str = "default",
        max_count: Optional[int] = None,
        log_level: int = logging.INFO,
        fill_char: str = " ",
        number_pad_character: str = " ",
    ) -> None:
        """
        Print a summary table of timing statistics for all tracked tasks.

        This method generates a formatted table displaying average, minimum,
        and maximum execution times, as well as the number of recordings for
        each tracked task.

        Parameters
        ----------
        sort : {'default', 'name', 'average'}, optional
            Specifies how to sort the output table:
            - 'default': No sorting, tasks appear in the order they were first timed
            - 'name': Sort tasks alphabetically by name
            - 'average': Sort tasks by their average execution time
        max_count : int, optional
            If specified, only the most recent `max_count` timings for each
            task are considered in the statistics calculation.
        log_level : int, optional
            The logging level to use for the output. Defaults to logging.INFO (i.e. 10)
        fill_char : str, optional
            The character to use for padding between columns in the formatted output.
            Defaults to space (' ') however some users may prefer an underscore
        number_pad_character : str, optional
            The character to use for padding numbers to the right, sensible options
            include '0', or the same character as `fill_char`, but defaults to ' '.

        Raises
        ------
        ValueError
            If an invalid sort option is provided.

        Notes
        -----
        - This method is particularly useful for identifying which tasks are
        taking the most time on average and how consistent their execution
        times are.
        - The output is logged at the specified log_level, so ensure your logging
        configuration will display messages at this level if you want to see the output.
        - The table format uses `fill_char` for padding between columns and
        `number_pad_character` for padding within numeric fields. This allows
        for flexible formatting of the output table.
        """
        logger.log(
            log_level,
            fill_char
            + f"{fill_char}|{fill_char}".join(
                [f"{'Average':7}", f"{'Minimum':7}", f"{'Maximum':7}", f"{'Count':5}", "Task"]
            ),
        )
        if sort == "default":
            sorted_task_names = cls._task_times.keys()
        elif sort == "name":
            sorted_task_names = sorted(cls._task_times.keys())
        elif sort == "average":
            sorted_task_names = sorted(cls._task_times.keys(), key=cls.get_average_time)
        else:
            raise ValueError(f"sort must be one of None, 'name', or 'average', not {sort}")

        for task_name in sorted_task_names:
            times = list(cls._task_times[task_name])
            if times:
                if max_count is not None and len(times) > max_count:
                    times = times[-max_count:]
                avg_time = sum(times) / len(times)
                logger.log(
                    log_level,
                    "|".join(
                        [
                            fill_char + f"{avg_time:{number_pad_character}>7.3f}" + fill_char,
                            fill_char + f"{min(times):{number_pad_character}>7.3f}" + fill_char,
                            fill_char + f"{max(times):{number_pad_character}>7.3f}" + fill_char,
                            fill_char + f"{len(times):{number_pad_character}>5d}" + fill_char,
                            fill_char + task_name,
                        ]
                    ),
                )
