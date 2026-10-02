"""python3 -m router [build|serve] [--data DIR] [--out DIR] [--port N]"""

import argparse
import functools
import http.server
from pathlib import Path

from .pipeline import build_output, run, write_outputs

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(prog="router", description="Score signals and route them to sellers.")
    parser.add_argument("command", nargs="?", default="build", choices=["build", "serve"])
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--out", type=Path, default=ROOT / "out")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    ds, cards, router = run(args.data)
    output = build_output(ds, cards, router)
    write_outputs(output, args.out)

    t = output["totals"]
    print(
        "Routed %d signals into %d account cards (%d customers, %d prospects). "
        "%d signals unmatched, %d cards on hold."
        % (t["signals"], t["accounts"], t["customers"], t["prospects"], t["unmatched_signals"], t["hold_queue"])
    )
    for s in output["sellers"]:
        print("  %-14s %-11s %-7s %2d cards (%d customers, %d prospects)" % (
            s["name"], s["territory"], s["status"], s["cards"], s["customers"], s["prospects"],
        ))
    print("Wrote %s/queue.json, queue.csv, index.html" % args.out)

    if args.command == "serve":
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(args.out))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
        print("Seller dashboard: http://localhost:%d" % args.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
