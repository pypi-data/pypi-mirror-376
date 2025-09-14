import argparse
from .reporter import generate_report, generate_html_report

def main():
    parser = argparse.ArgumentParser(description="ows-sysinfo - Collect full system report")
    parser.add_argument("--json", "-j", help="Write JSON output to file (e.g. report.json)")
    parser.add_argument("--html", "-H", help="Write HTML output to file (e.g. report.html)", action="store_true")
    parser.add_argument("--pretty", "-p", help="Print pretty JSON to terminal", action="store_true")
    parser.add_argument("--speedtest", "-s", help="Run speedtest (may take time)", action="store_true")
    parser.add_argument("--top", "-t", help="Top N processes to include", type=int, default=10)

    args = parser.parse_args()
    out = None
    if args.json:
        out = generate_report(outfile=args.json, pretty=args.pretty, speedtest=args.speedtest, top_n=args.top)
        print(f"Wrote JSON report to {args.json}")
    else:
        out = generate_report(outfile=None, pretty=args.pretty, speedtest=args.speedtest, top_n=args.top)

    if args.html:
        path = generate_html_report(outfile="sys_report.html", speedtest=args.speedtest, top_n=args.top)
        print(f"Wrote HTML report to {path}")

if __name__ == "__main__":
    main()
