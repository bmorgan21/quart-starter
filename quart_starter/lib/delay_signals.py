import logging
import signal


class DelaySignals:
    def __init__(
        self,
        signals_to_delay: list[signal.Signals] = signal.SIGINT,
        unless_repeated_n_times: int = False,
    ):
        """
        A class which intercepts chosen incoming signals after __enter__ and delays them till __exit__ is reached.

        Args:
            signals_to_delay (list[signal.Signals], optional):  The signal or list/tuple of signals to delay. Defaults to signal.SIGINT.
            unless_repeated_n_times (int|bool, optional):       If a signal is received N amount of times, allow it through by exiting the class prematurely. Defaults to False.

        Example usage:
            ```py
            with DelaySignals( signal.SIGINT ):
                time.sleep(10)  # If a SIGINT signal  (KeyboardInterrupt)  is received in this scope, it is delayed until the scope is exited
            ```

        Based on:
            http://stackoverflow.com/a/21919644/487556
            https://gist.github.com/tcwalther/ae058c64d5d9078a9f333913718bba95
        """
        self.signals_to_delay = (
            signals_to_delay
            if type(signals_to_delay) in [list, tuple]
            else [signals_to_delay]
        )
        self.unless_repeated_n_times = unless_repeated_n_times

    def __enter__(self):
        self.inboxes = {}
        for sig_type in self.signals_to_delay:
            self.inboxes[sig_type] = {
                "received": [],
                "handler": signal.getsignal(sig_type),
            }
            signal.signal(sig_type, self.signal_handler)

    def signal_handler(self, sig, frame):
        self.inboxes[sig]["received"].append((sig, frame))

        if (
            self.unless_repeated_n_times
            and len(self.inboxes[sig]["received"]) >= self.unless_repeated_n_times
        ):
            logging.warn(
                f"{__class__.__name__}: Signal {sig} repeated enough times ({self.unless_repeated_n_times}) to pass through, exiting early."
            )
            self.__exit__()
        else:
            logging.info(f"{__class__.__name__}: Signal {sig} handled.")

    def __exit__(self, *_):
        for sig, inbox in self.inboxes.items():
            signal.signal(sig, inbox["handler"])
            if inbox["handler"]:
                for msg in inbox["received"]:
                    inbox["handler"](*msg)
            else:
                logging.warn(
                    f"{__class__.__name__}: Signal {sig} had no prior handler, skipping."
                )
