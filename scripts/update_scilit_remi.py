# scripts/update_scilit_remi.py

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests


SCILIT_URL = (
    "https://www.scilit.com/sources/"
    "019f25e40c1872ae9ebc9488e577dd65"
)

OUT_JSON = Path("remi-scilit.json")


def fetch_html(url: str) -> str:

    headers = {

        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0.0.0 "
            "Safari/537.36"
        ),

        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8"
        ),

        "Accept-Language":
            "pt-BR,pt;q=0.9,en;q=0.8",

        "Referer":
            "https://www.scilit.com/",

    }


    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )


    response.raise_for_status()

    return response.text



def parse_number_after_label(
    html: str,
    label_regex: str
) -> float | int | None:

    """
    Procura o valor numérico DEPOIS do rótulo.

    Isso evita, por exemplo, interpretar o número 5
    existente no próprio texto "h5-index" como sendo
    o valor do indicador.
    """

    match = re.search(
        label_regex,
        html,
        flags=re.IGNORECASE
    )


    if not match:
        return None


    # Procura apenas depois do label
    chunk = html[
        match.end():
        min(match.end() + 1000, len(html))
    ]


    # Remove tags simples para reduzir ruído
    text = re.sub(
        r"<[^>]+>",
        " ",
        chunk
    )


    # Espaços
    text = re.sub(
        r"\s+",
        " ",
        text
    )


    number = re.search(
        r"(-?\d+(?:[.,]\d+)?)",
        text
    )


    if not number:
        return None


    value = (
        number
        .group(1)
        .replace(",", ".")
    )


    try:

        x = float(value)

        return (
            int(x)
            if x.is_integer()
            else x
        )

    except ValueError:

        return None



def parse_series(
    html: str
) -> list[dict]:

    """
    Tenta encontrar a série do
    Monthly Citation Metric.

    Retorna:

    [
        {
            "month": "2026-01",
            "value": 0.42
        }
    ]
    """


    months = re.findall(
        r"(20\d{2}-\d{2})",
        html
    )


    # elimina meses duplicados,
    # mantendo a ordem
    seen = set()

    months = [
        month
        for month in months
        if not (
            month in seen
            or seen.add(month)
        )
    ]


    metric = re.search(
        r"Monthly\s+Citation\s+Metric",
        html,
        flags=re.IGNORECASE
    )


    if not metric:
        return []


    window = html[
        metric.start():
        metric.start() + 50000
    ]


    array_match = re.search(
        r"\[(?:\s*-?\d+(?:\.\d+)?\s*,?)+\s*\]",
        window
    )


    if not array_match:
        return []


    values = re.findall(
        r"-?\d+(?:\.\d+)?",
        array_match.group(0)
    )


    values = [
        float(value)
        for value in values
    ]


    n = min(
        len(months),
        len(values)
    )


    if n == 0:
        return []


    return [

        {
            "month": months[i],
            "value": round(
                values[i],
                4
            )
        }

        for i in range(n)

    ]



def load_old_json() -> dict:

    if not OUT_JSON.exists():
        return {}


    try:

        return json.loads(
            OUT_JSON.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        return {}



def main() -> None:

    old = load_old_json()


    try:

        html = fetch_html(
            SCILIT_URL
        )


        h5_index = (
            parse_number_after_label(
                html,
                r"\bh5[-\s]?index\b"
            )
        )


        mcm = (
            parse_number_after_label(
                html,
                r"Monthly\s+Citation\s+Metric"
            )
        )


        series = parse_series(
            html
        )


        #
        # Se o Scilit mudar o layout
        # ou bloquear o scraping,
        # NÃO apaga os dados antigos.
        #

        if h5_index is None:
            h5_index = old.get(
                "h5_index"
            )


        if mcm is None:
            mcm = old.get(
                "mcm"
            )


        if not series:

            old_series = old.get(
                "series"
            )

            if isinstance(
                old_series,
                list
            ):

                series = old_series


        payload = {

            "source":
                SCILIT_URL,

            "updated_at":
                datetime
                .now(timezone.utc)
                .date()
                .isoformat(),

            "h5_index":
                h5_index,

            "mcm":
                mcm,

            "series":
                series

        }


        OUT_JSON.write_text(

            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2
            ),

            encoding="utf-8"

        )


        print(
            "OK: métricas Scilit da REMI atualizadas."
        )


    except Exception as error:

        #
        # MUITO IMPORTANTE:
        #
        # se o Scilit bloquear a consulta,
        # mantém o JSON anterior.
        #

        print(
            "ERRO ao consultar Scilit."
        )

        print(
            "JSON anterior será mantido."
        )

        print(
            repr(error)
        )



if __name__ == "__main__":
    main()
