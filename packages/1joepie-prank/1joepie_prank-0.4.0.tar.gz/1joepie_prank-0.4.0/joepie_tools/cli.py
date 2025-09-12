"""CLI for joepie_tools pranks."""
import argparse
import logging
from joepie_tools.hackerprank import (
    fake_hack_screen, fake_matrix, fake_terminal, fake_file_dump, fake_warning_popup,
    fake_bsod, fake_update_screen, fake_virus_scan, random_popups,
    run_full_prank
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("joepie_tools")

def _positive_int(v):
    iv = int(v)
    if iv < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return iv

def _positive_float(v):
    fv = float(v)
    if fv < 0.5:
        raise argparse.ArgumentTypeError("duration must be >= 0.5")
    return fv

def main(argv=None):
    parser = argparse.ArgumentParser(prog="joepie_tools", description="Joepie prank tools CLI")
    sub = parser.add_subparsers(dest="cmd")

    p1 = sub.add_parser("hack", help="Fake hack windows")
    p1.add_argument("-n","--num", type=_positive_int, default=3)
    p1.add_argument("-d","--duration", type=_positive_float, default=8.0)

    p2 = sub.add_parser("matrix", help="Matrix effect")
    p2.add_argument("-d","--duration", type=_positive_float, default=12.0)

    p3 = sub.add_parser("term", help="Fake terminal")
    p3.add_argument("-d","--duration", type=_positive_float, default=10.0)

    p4 = sub.add_parser("dump", help="Fake file dump")
    p4.add_argument("-d","--duration", type=_positive_float, default=6.0)

    p5 = sub.add_parser("popup", help="Fake warning popup")
    p5.add_argument("-m","--message", type=str, default="Warning: Unauthorized access")
    p5.add_argument("-d","--duration", type=_positive_float, default=4.0)

    p6 = sub.add_parser("bsod", help="Fake blue screen (fullscreen)")
    p6.add_argument("-d","--duration", type=_positive_float, default=8.0)

    p7 = sub.add_parser("update", help="Fake update screen (fullscreen)")
    p7.add_argument("-d","--duration", type=_positive_float, default=15.0)

    p8 = sub.add_parser("scan", help="Fake virus scan")
    p8.add_argument("-d","--duration", type=_positive_float, default=12.0)
    p8.add_argument("--max","--max-threats", dest="max_threats", type=_positive_int, default=500)

    p9 = sub.add_parser("popups", help="Random popups")
    p9.add_argument("-c","--count", type=_positive_int, default=10)
    p9.add_argument("-d","--duration", type=_positive_float, default=8.0)

    p10 = sub.add_parser("runfull", help="Full prank runner")
    p10.add_argument("-n","--num", type=_positive_int, default=3)
    p10.add_argument("-d","--duration", type=_positive_float, default=8.0)
    p10.add_argument("--beep", action="store_true")
    p10.add_argument("--ack", dest="require_ack", action="store_true")
    p10.add_argument("--hotkey", type=str, default="F12")

    args = parser.parse_args(argv)

    if args.cmd == "hack":
        fake_hack_screen(num_windows=args.num, duration=args.duration)
    elif args.cmd == "matrix":
        fake_matrix(duration=args.duration)
    elif args.cmd == "term":
        fake_terminal(duration=args.duration)
    elif args.cmd == "dump":
        fake_file_dump(duration=args.duration)
    elif args.cmd == "popup":
        fake_warning_popup(message=args.message, duration=args.duration)
    elif args.cmd == "bsod":
        fake_bsod(duration=args.duration)
    elif args.cmd == "update":
        fake_update_screen(duration=args.duration)
    elif args.cmd == "scan":
        fake_virus_scan(duration=args.duration, max_threats=args.max_threats)
    elif args.cmd == "popups":
        random_popups(count=args.count, duration=args.duration)
    elif args.cmd == "runfull":
        run_full_prank(require_ack=args.require_ack, beep=args.beep, reveal_hotkey=args.hotkey, num_windows=args.num, duration=args.duration)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
