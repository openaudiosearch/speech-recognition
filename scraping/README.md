# Skripte für Scraping, Parsing, und Aufbereitung von Videos und Transkripten (österr. Deutsch).

Dieser Ordner beinhaltet Python-Skripte für das Scraping, Parsing, und Aufbereitung von Videos und Transkripten (österr. Deutsch)

- Daten von Reden im Österr. Parlament

  * `crawl_nationalrat.py`: Skript zum Download von Videos und stenografischen Transkripten von Sitzungen des österr. Nationalrats.

  * `crawl_bundesrat.py`: Skript zum Download von Videos und stenografischen Transkripten von Sitzungen des österr. Bundesrats.

  * `parse_parlament.py`: Skript zum Parsing von stenografischen Transkripten von Sitzungen des österr. Nationalrats. Das Skript nimmt viele Normalisierungen der Transkripte vor, die durch das Format (HTML-Export von MS Word) bedingt sind.


- Daten von Videos der Stadt Wien

  * `crawl_wienvideos.py`: Skript zum Download von Videos und Untertiteln von Videos der Stadt Wien.
