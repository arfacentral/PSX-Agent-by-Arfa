import csv
from pathlib import Path

from psx_agent.config import get_settings
from psx_agent.providers.demo import DemoProvider


def main() -> None:
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    provider = DemoProvider()

    for symbol in get_settings().symbols:
        rows = provider.get_history(symbol)
        with (output_dir / f"{symbol}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["date", "open", "high", "low", "close", "volume"])
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "date": row.date.isoformat(),
                        "open": row.open,
                        "high": row.high,
                        "low": row.low,
                        "close": row.close,
                        "volume": row.volume,
                    }
                )


if __name__ == "__main__":
    main()

