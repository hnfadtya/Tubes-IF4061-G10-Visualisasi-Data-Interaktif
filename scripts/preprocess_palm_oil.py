from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_PROVINCE_FILE = DATA_DIR / "palm_oil_area_and_production_by_province.csv"
RAW_TRADE_FILE = DATA_DIR / "ekspor_impor_palm_oil_2010_2023.csv"


def to_int(value: str) -> int:
    return int(float(value))


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def fmt_int(value: int) -> int:
    return int(value)


def fmt_float(value: float) -> str:
    return f"{value:.2f}"


def load_province_rows() -> list[dict[str, str]]:
    with RAW_PROVINCE_FILE.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_outputs() -> None:
    rows = load_province_rows()

    province_metrics: list[dict[str, object]] = []
    yearly_totals: dict[str, int] = defaultdict(int)
    yearly_area_totals: dict[str, int] = defaultdict(int)
    yearly_ownership_totals = defaultdict(lambda: {"rakyat": 0, "swasta": 0, "negara": 0})

    for row in rows:
        year = row["Tahun"]
        province = row["Provinsi"]

        area_negara = to_int(row["Luas_Area_Negara"])
        production_negara = to_int(row["Produksi_Negara"])
        area_swasta = to_int(row["Luas_Area_Swasta"])
        production_swasta = to_int(row["Produksi_Swasta"])
        area_rakyat = to_int(row["Luas_Area_Rakyat"])
        production_rakyat = to_int(row["Produksi_Rakyat"])
        total_area = to_int(row["Total_Area"])
        total_production = to_int(row["Total_Produksi"])

        productivity_negara = safe_div(production_negara, area_negara)
        productivity_swasta = safe_div(production_swasta, area_swasta)
        productivity_rakyat = safe_div(production_rakyat, area_rakyat)
        productivity_total = safe_div(total_production, total_area)

        province_metrics.append(
            {
                "Tahun": year,
                "Provinsi": province,
                "Luas_Area_Negara": fmt_int(area_negara),
                "Produksi_Negara": fmt_int(production_negara),
                "Produktivitas_Negara": fmt_float(productivity_negara),
                "Luas_Area_Swasta": fmt_int(area_swasta),
                "Produksi_Swasta": fmt_int(production_swasta),
                "Produktivitas_Swasta": fmt_float(productivity_swasta),
                "Luas_Area_Rakyat": fmt_int(area_rakyat),
                "Produksi_Rakyat": fmt_int(production_rakyat),
                "Produktivitas_Rakyat": fmt_float(productivity_rakyat),
                "Total_Area": fmt_int(total_area),
                "Total_Produksi": fmt_int(total_production),
                "Produktivitas_Total": fmt_float(productivity_total),
                "Pangsa_Produksi_Nasional_Persen": "",
            }
        )

        yearly_totals[year] += total_production
        yearly_area_totals[year] += total_area
        yearly_ownership_totals[year]["rakyat"] += production_rakyat
        yearly_ownership_totals[year]["swasta"] += production_swasta
        yearly_ownership_totals[year]["negara"] += production_negara

    for record in province_metrics:
        year_total = yearly_totals[record["Tahun"]]
        record["Pangsa_Produksi_Nasional_Persen"] = fmt_float(
            safe_div(int(record["Total_Produksi"]), year_total) * 100
        )

    province_metrics.sort(key=lambda item: (int(item["Tahun"]), item["Provinsi"]))

    yearly_trend: list[dict[str, object]] = []
    previous_total = None
    for year in sorted(yearly_totals, key=int):
        total_production = yearly_totals[year]
        year_area = yearly_area_totals[year]
        yoy_growth = ""
        if previous_total not in (None, 0):
            yoy_growth = fmt_float((total_production - previous_total) / previous_total * 100)
        yearly_trend.append(
            {
                "Tahun": year,
                "Total_Produksi": fmt_int(total_production),
                "Total_Area": fmt_int(year_area),
                "YoY_Growth_Persen": yoy_growth,
            }
        )
        previous_total = total_production

    composition_rows: list[dict[str, object]] = []
    for year in sorted(yearly_ownership_totals, key=int):
        total_production = yearly_totals[year]
        pnb = yearly_ownership_totals[year]["negara"]
        pbs = yearly_ownership_totals[year]["swasta"]
        pr = yearly_ownership_totals[year]["rakyat"]
        composition_rows.append(
            {
                "Tahun": year,
                "PBN_Produksi": fmt_int(pnb),
                "PBN_Persen": fmt_float(safe_div(pnb, total_production) * 100),
                "PBS_Produksi": fmt_int(pbs),
                "PBS_Persen": fmt_float(safe_div(pbs, total_production) * 100),
                "PR_Produksi": fmt_int(pr),
                "PR_Persen": fmt_float(safe_div(pr, total_production) * 100),
                "Total_Produksi": fmt_int(total_production),
            }
        )

    province_totals_check = {year: 0 for year in yearly_totals}
    for row in province_metrics:
        province_totals_check[row["Tahun"]] += int(row["Total_Produksi"])

    mismatch = {
        year: (province_totals_check[year], yearly_totals[year])
        for year in yearly_totals
        if province_totals_check[year] != yearly_totals[year]
    }
    if mismatch:
        raise ValueError(f"Yearly totals mismatch: {mismatch}")

    write_csv(
        PROCESSED_DIR / "palm_oil_province_metrics_by_year.csv",
        [
            "Tahun",
            "Provinsi",
            "Luas_Area_Negara",
            "Produksi_Negara",
            "Produktivitas_Negara",
            "Luas_Area_Swasta",
            "Produksi_Swasta",
            "Produktivitas_Swasta",
            "Luas_Area_Rakyat",
            "Produksi_Rakyat",
            "Produktivitas_Rakyat",
            "Total_Area",
            "Total_Produksi",
            "Produktivitas_Total",
            "Pangsa_Produksi_Nasional_Persen",
        ],
        province_metrics,
    )

    write_csv(
        PROCESSED_DIR / "palm_oil_national_trend_by_year.csv",
        ["Tahun", "Total_Produksi", "Total_Area", "YoY_Growth_Persen"],
        yearly_trend,
    )

    write_csv(
        PROCESSED_DIR / "palm_oil_ownership_composition_by_year.csv",
        [
            "Tahun",
            "PBN_Produksi",
            "PBN_Persen",
            "PBS_Produksi",
            "PBS_Persen",
            "PR_Produksi",
            "PR_Persen",
            "Total_Produksi",
        ],
        composition_rows,
    )


if __name__ == "__main__":
    build_outputs()
