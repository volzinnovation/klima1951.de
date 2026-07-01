#!/usr/bin/env python3
"""Read-only inventory for the local HYRAS JSON and NetCDF artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any


HYRAS_FILE_RE = re.compile(r"^(?P<metric>[a-z]+)_hyras_1_(?P<year>\d{4})_.*\.nc$")
UTC = timezone.utc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a read-only status snapshot for generated HYRAS artifacts.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to this script's parent repository.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--max-missing",
        type=int,
        default=10,
        help="Maximum missing city artifacts to include in the report.",
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Remove local filesystem roots from JSON output for public frontend use.",
    )
    parser.add_argument(
        "--as-of-date",
        help=(
            "UTC date or datetime used for freshness calculations. "
            "Defaults to the current UTC time."
        ),
    )
    parser.add_argument(
        "--freshness-grace-days",
        type=int,
        default=45,
        help=(
            "Days after January 1 before the previous calendar year is required "
            "as complete. Defaults to 45."
        ),
    )
    parser.add_argument(
        "--require-fresh",
        action="store_true",
        help="Exit with a non-zero status when the freshness check is not OK.",
    )
    return parser.parse_args()


def parse_as_of(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return datetime.combine(date.fromisoformat(value), time.min, UTC)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def expected_complete_year(as_of: datetime, grace_days: int) -> int:
    grace_days = max(0, grace_days)
    year_cutover = datetime(as_of.year, 1, 1, tzinfo=UTC) + timedelta(days=grace_days)
    if as_of < year_cutover:
        return as_of.year - 2
    return as_of.year - 1


def load_cities(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    cities = payload.get("cities", [])
    if not isinstance(cities, list):
        return []
    return [city for city in cities if isinstance(city, dict)]


def file_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "bytes": stat.st_size,
        "modified_at_utc": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
    }


def read_stats_years(path: Path) -> list[int]:
    if not path.exists():
        return []
    years: list[int] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            value = row.get("Jahr")
            if value and value.isdigit():
                years.append(int(value))
    return years


def summarize_city_outputs(root: Path, max_missing: int) -> dict[str, Any]:
    cities = load_cities(root / "misc" / "cities.json")
    complete = 0
    missing: list[dict[str, Any]] = []
    stats_latest_years: list[int] = []
    stats_earliest_years: list[int] = []
    total_all_years_bytes = 0

    for city in cities:
        name = str(city.get("city", ""))
        longitude = city.get("longitude")
        latitude = city.get("latitude")
        city_dir = root / "data" / "json" / str(longitude) / str(latitude)
        all_years_path = city_dir / "all-years.json"
        stats_path = city_dir / "stats.csv"
        all_years_exists = all_years_path.exists()
        stats_exists = stats_path.exists()

        if all_years_exists:
            total_all_years_bytes += all_years_path.stat().st_size
        years = read_stats_years(stats_path)
        if years:
            stats_earliest_years.append(min(years))
            stats_latest_years.append(max(years))

        if all_years_exists and stats_exists:
            complete += 1
        elif len(missing) < max_missing:
            missing.append(
                {
                    "city": name,
                    "longitude": longitude,
                    "latitude": latitude,
                    "missing": [
                        label
                        for label, exists in (
                            ("all-years.json", all_years_exists),
                            ("stats.csv", stats_exists),
                        )
                        if not exists
                    ],
                }
            )

    return {
        "configured_cities": len(cities),
        "complete_city_outputs": complete,
        "missing_city_outputs": len(cities) - complete,
        "missing_examples": missing,
        "stats_min_year": min(stats_earliest_years) if stats_earliest_years else None,
        "stats_max_year": max(stats_latest_years) if stats_latest_years else None,
        "stats_latest_complete_year": min(stats_latest_years) if stats_latest_years else None,
        "stats_latest_year_counts": dict(sorted(Counter(stats_latest_years).items())),
        "stats_files_with_years": len(stats_latest_years),
        "all_years_total_bytes": total_all_years_bytes,
    }


def summarize_hyras_files(root: Path) -> dict[str, Any]:
    hyras_dir = root / "data" / "hyras"
    metrics: dict[str, list[int]] = defaultdict(list)
    files = []
    if hyras_dir.exists():
        for path in sorted(hyras_dir.glob("*.nc")):
            match = HYRAS_FILE_RE.match(path.name)
            if not match:
                continue
            metric = match.group("metric")
            year = int(match.group("year"))
            metrics[metric].append(year)
            files.append(file_status(path))

    metric_summary = {
        metric: {
            "file_count": len(years),
            "min_year": min(years),
            "max_year": max(years),
        }
        for metric, years in sorted(metrics.items())
        if years
    }
    return {
        "hyras_file_count": len(files),
        "metrics": metric_summary,
        "files": files,
    }


def build_freshness(
    city_outputs: dict[str, Any],
    hyras: dict[str, Any],
    expected_metrics: set[str],
    as_of: datetime,
    grace_days: int,
) -> dict[str, Any]:
    expected_year = expected_complete_year(as_of, grace_days)
    stats_year = city_outputs.get("stats_latest_complete_year")
    stats_files_with_years = city_outputs.get("stats_files_with_years") or 0
    latest_year_counts = city_outputs.get("stats_latest_year_counts") or {}
    stats_files_behind = sum(
        count
        for year, count in latest_year_counts.items()
        if int(year) < expected_year
    )

    metric_years = {
        metric: summary.get("max_year")
        for metric, summary in (hyras.get("metrics") or {}).items()
        if isinstance(summary, dict)
    }
    missing_metrics = sorted(metric for metric in expected_metrics if metric not in metric_years)
    stale_metrics = sorted(
        metric
        for metric in expected_metrics
        if not metric_years.get(metric) or int(metric_years[metric]) < expected_year
    )
    present_expected_years = [
        int(metric_years[metric])
        for metric in expected_metrics
        if metric_years.get(metric)
    ]
    hyras_year = min(present_expected_years) if present_expected_years else None

    problems: list[str] = []
    if stats_year is None:
        problems.append("keine Stadt-Statistiken mit Jahreswerten gefunden")
    elif int(stats_year) < expected_year:
        problems.append(
            f"Stadt-Statistiken reichen nur bis {stats_year}, erwartet ist {expected_year}"
        )
    if stale_metrics:
        problems.append(
            "HYRAS-Metriken hinter dem erwarteten Jahr: " + ", ".join(stale_metrics)
        )

    if problems:
        status = (
            "missing"
            if stats_year is None or len(missing_metrics) == len(expected_metrics)
            else "warn"
        )
        detail = "; ".join(problems)
    else:
        status = "ok"
        detail = (
            f"Alle Stadt-Statistiken und HYRAS-Metriken reichen bis zum "
            f"erwarteten vollstaendigen Jahr {expected_year}."
        )

    return {
        "as_of_utc": as_of.isoformat(),
        "freshness_grace_days": max(0, grace_days),
        "expected_latest_complete_year": expected_year,
        "stats_latest_complete_year": stats_year,
        "stats_files_checked": stats_files_with_years,
        "stats_files_behind_expected_year": stats_files_behind,
        "hyras_latest_complete_year": hyras_year,
        "hyras_metric_years": metric_years,
        "missing_hyras_metrics": missing_metrics,
        "stale_hyras_metrics": stale_metrics,
        "status": status,
        "detail": detail,
    }


def build_status(root: Path, max_missing: int, as_of: datetime, grace_days: int) -> dict[str, Any]:
    root = root.resolve()
    city_outputs = summarize_city_outputs(root, max_missing)
    hyras = summarize_hyras_files(root)
    expected_metrics = {"hurs", "pr", "tas", "tasmax", "tasmin"}
    observed_metrics = set(hyras["metrics"])
    missing_metrics = expected_metrics - observed_metrics
    freshness = build_freshness(city_outputs, hyras, expected_metrics, as_of, grace_days)

    checks = [
        {
            "name": "cities_configured",
            "status": "ok" if city_outputs["configured_cities"] > 0 else "missing",
            "detail": f"{city_outputs['configured_cities']} cities in misc/cities.json",
        },
        {
            "name": "city_json_outputs_complete",
            "status": "ok" if city_outputs["missing_city_outputs"] == 0 else "warn",
            "detail": (
                f"{city_outputs['complete_city_outputs']} of "
                f"{city_outputs['configured_cities']} city outputs complete"
            ),
        },
        {
            "name": "hyras_metric_files_present",
            "status": "ok" if not missing_metrics else "warn",
            "detail": (
                "observed metrics: "
                + ", ".join(sorted(observed_metrics))
                + "; missing: "
                + (", ".join(sorted(missing_metrics)) if missing_metrics else "none")
            ),
        },
        {
            "name": "data_freshness",
            "status": freshness["status"],
            "detail": freshness["detail"],
        },
    ]

    return {
        "generated_at_utc": as_of.isoformat(),
        "root": str(root),
        "city_outputs": city_outputs,
        "hyras": hyras,
        "freshness": freshness,
        "files": {
            "cities_json": file_status(root / "misc" / "cities.json"),
        },
        "checks": checks,
    }


def scrub_local_paths(status: dict[str, Any], root: Path) -> None:
    """Mutate a status snapshot so it is safe to publish as static JSON."""

    root = root.resolve()
    status.pop("root", None)
    status["public"] = True

    def scrub_file_info(file_info: dict[str, Any]) -> None:
        raw_path = file_info.get("path")
        if not raw_path:
            return
        path = Path(str(raw_path))
        try:
            file_info["path"] = path.resolve().relative_to(root).as_posix()
        except ValueError:
            file_info["path"] = path.name

    for file_info in status.get("files", {}).values():
        if isinstance(file_info, dict):
            scrub_file_info(file_info)

    hyras_files = status.get("hyras", {}).get("files", [])
    if isinstance(hyras_files, list):
        for file_info in hyras_files:
            if isinstance(file_info, dict):
                scrub_file_info(file_info)


def render_bytes(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GiB"
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MiB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.2f} KiB"
    return f"{num_bytes} B"


def render_markdown(status: dict[str, Any]) -> str:
    city = status["city_outputs"]
    hyras = status["hyras"]
    freshness = status["freshness"]
    lines = [
        "# HYRAS Data Status",
        "",
        f"- Generated at: `{status['generated_at_utc']}`",
        f"- Configured cities: `{city['configured_cities']}`",
        f"- Complete city outputs: `{city['complete_city_outputs']}`",
        f"- Missing city outputs: `{city['missing_city_outputs']}`",
        f"- Stats year span: `{city['stats_min_year'] or 'n/a'}` to `{city['stats_max_year'] or 'n/a'}`",
        f"- all-years.json total size: `{render_bytes(city['all_years_total_bytes'])}`",
        f"- HYRAS NetCDF files: `{hyras['hyras_file_count']}`",
        "",
        "## Freshness",
        "",
        f"- Status: `{freshness['status']}`",
        f"- Expected latest complete year: `{freshness['expected_latest_complete_year']}`",
        f"- City statistics latest complete year: `{freshness['stats_latest_complete_year'] or 'n/a'}`",
        f"- HYRAS latest complete year: `{freshness['hyras_latest_complete_year'] or 'n/a'}`",
        f"- Detail: {freshness['detail']}",
        "",
        "## HYRAS Metrics",
        "",
        "| Metric | Files | Min year | Max year |",
        "| --- | ---: | ---: | ---: |",
    ]
    for metric, summary in hyras["metrics"].items():
        lines.append(
            f"| `{metric}` | {summary['file_count']} | {summary['min_year']} | {summary['max_year']} |"
        )

    if city["missing_examples"]:
        lines.extend(["", "## Missing Output Examples", ""])
        for entry in city["missing_examples"]:
            missing = ", ".join(entry["missing"])
            lines.append(
                f"- `{entry['city']}` ({entry['longitude']}/{entry['latitude']}): {missing}"
            )

    lines.extend(["", "## Checks", ""])
    for check in status["checks"]:
        lines.append(f"- `{check['status']}` {check['name']}: {check['detail']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    as_of = parse_as_of(args.as_of_date)
    status = build_status(args.root, args.max_missing, as_of, args.freshness_grace_days)
    if args.public:
        scrub_local_paths(status, args.root)
    if args.format == "json":
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(status), end="")
    if args.require_fresh and status["freshness"]["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
