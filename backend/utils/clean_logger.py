"""Clean logging for minimal console output."""

class CleanLogger:
    """Wrapper for print statements that respects clean_output setting."""

    def __init__(self, verbose=False, clean=True):
        """
        Initialize logger.

        Args:
            verbose: Show verbose messages
            clean: Show only essential output
        """
        self.verbose = verbose
        self.clean = clean

    def set_modes(self, verbose=False, clean=True):
        """Update verbose and clean modes."""
        self.verbose = verbose
        self.clean = clean

    def log(self, message, level="INFO"):
        """
        Log a message based on level and mode settings.

        Args:
            message: Message to log
            level: Message level - "CRITICAL", "IMPORTANT", "INFO", "DEBUG", "VERBOSE"
        """
        # CRITICAL: Always show (red alerts, bet results, crashes)
        if level == "CRITICAL":
            print(message)
            return

        # IMPORTANT: Show unless in clean mode (bet confirmation, wins/losses)
        if level == "IMPORTANT":
            if not self.clean:
                print(message)
            return

        # INFO: Show unless in clean mode (normal operation)
        if level == "INFO":
            if not self.clean:
                print(message)
            return

        # DEBUG: Show only in verbose mode
        if level == "DEBUG":
            if self.verbose:
                print(message)
            return

        # VERBOSE: Show only in verbose mode
        if level == "VERBOSE":
            if self.verbose:
                print(message)
            return

    def section(self, title):
        """Print section header (always shown)."""
        print(f"\n{'='*80}")
        print(title)
        print(f"{'='*80}\n")

    def result(self, message):
        """Print important result (win/loss/etc - always shown)."""
        print(f"\n{message}\n")

    def bet_placed(self, position, stake):
        """Log bet placed (shows in non-clean mode)."""
        self.log(f"Position {position} bet placed (stake: {stake})", level="INFO")

    def bet_result(self, position, result, amount, mult=None):
        """Log bet result (important, usually shown)."""
        if mult:
            self.log(f"Position {position}: {result} {amount:+.2f} @ {mult:.2f}x", level="IMPORTANT")
        else:
            self.log(f"Position {position}: {result} {amount:+.2f}", level="IMPORTANT")

    def round_summary(self, round_num, p1_result, p2_result, total, p1_mult=None, p2_mult=None):
        """Print round summary (critical for visibility)."""
        sep = " | " if p2_result else ""
        msg = f"ROUND {round_num}: P1 {p1_result:+.0f}"
        if p2_result:
            msg += f"{sep}P2 {p2_result:+.0f}"
        msg += f" | Total: {total:+.0f}"
        if p1_mult:
            msg += f" | Mults: {p1_mult:.2f}"
            if p2_mult:
                msg += f", {p2_mult:.2f}"
        self.result(msg)
