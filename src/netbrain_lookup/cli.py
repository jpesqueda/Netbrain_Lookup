"""CLI entry point and shared error handling."""
import sys
from . import engine


def execute(args):
    try:
        return engine.main(args)
    except KeyboardInterrupt:
        return engine.report_error("Cancelled by user.", 130)
    except engine.AuthenticationError as exc:
        engine.log_event("ERROR", str(exc))
        return engine.report_error("NetBrain authentication failed.", 3)
    except engine.NetBrainUnreachable as exc:
        engine.log_event("ERROR", str(exc))
        return engine.report_error("Unable to reach NetBrain server.", 4)
    except engine.NetBrainAPIError as exc:
        engine.log_event("ERROR", str(exc))
        return engine.report_error("NetBrain API request failed.", 5)
    except engine.NetBrainError as exc:
        return engine.report_error(str(exc), 2)
    except (OSError, EOFError, ValueError) as exc:
        engine.log_event("ERROR", type(exc).__name__)
        return engine.report_error("Input or file operation failed.", 2)
    except Exception as exc:
        engine.log_event("ERROR", type(exc).__name__)
        return engine.report_error(f"Unexpected error ({type(exc).__name__}).", 1)
    finally:
        args.password = None
        engine.SECRETS.clear()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = engine.parse_args(argv)
    if args.demo or args.interactive or not argv:
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            print("Interactive UI requires a terminal. Use CLI arguments instead.", file=sys.stderr)
            return 2
        from .tui import LookupApp
        return LookupApp(args).run() or 0
    return execute(args)
