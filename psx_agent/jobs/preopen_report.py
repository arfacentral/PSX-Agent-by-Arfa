import json
from pathlib import Path

from psx_agent.report import build_morning_report


def main() -> None:
    report = build_morning_report()
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "latest_preopen_report.json"
    output_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()

