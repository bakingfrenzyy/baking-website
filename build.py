"""
build.py — turns items.csv into index.html

Run it:      python build.py
Preview it:  python build.py --serve     then open http://localhost:8000

Add or change a bake by editing items.csv (a spreadsheet can open it),
then run this again. Never edit index.html by hand: this script
overwrites it every time.
"""

import csv
import html
import sys
from datetime import date
from pathlib import Path

# ============================================================
# SETTINGS — the things you'll change most often
# ============================================================

CURRENCY = "$"

# Shown above the seasonal list. Update when the season turns.
SEASON_NOTE = "Available until November 21st."

# Which CSV categories go in which tab.
# The key is what you type in the category column.
CATEGORIES = {
    "allyear": "{{ALLYEAR_ITEMS}}",
    "seasonal": "{{SEASONAL_ITEMS}}",
}

# File locations. These are relative to this script, so it works
# no matter which folder you run it from.
HERE = Path(__file__).parent
CSV_FILE = HERE / "items.csv"
TEMPLATE_FILE = HERE / "index.template.html"
OUTPUT_FILE = HERE / "index.html"
PHOTO_FOLDER = "images"

REQUIRED_COLUMNS = ["name", "description", "price", "category", "photo", "available"]


# ============================================================
# READING THE CSV
# ============================================================

def read_items():
    """Read items.csv and hand back a list of rows, checking as we go."""
    if not CSV_FILE.exists():
        quit_with_error(f"Can't find {CSV_FILE.name}. It should sit next to build.py.")

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            quit_with_error(
                f"{CSV_FILE.name} is missing these columns: {', '.join(missing)}\n"
                f"The first line must be: {','.join(REQUIRED_COLUMNS)}"
            )

        items = []
        # start=2 because line 1 is the header, so the number
        # matches what you see in your spreadsheet
        for line_number, row in enumerate(reader, start=2):
            if not row["name"].strip():
                continue  # skip blank lines at the end of the file
            check_row(row, line_number)
            items.append(row)

    if not items:
        quit_with_error(f"{CSV_FILE.name} has no items in it yet.")

    return items


def check_row(row, line_number):
    """Catch the mistakes that are easy to make in a spreadsheet."""
    category = row["category"].strip().lower()
    if category not in CATEGORIES:
        quit_with_error(
            f"Line {line_number} ({row['name']}): category is '{row['category']}'.\n"
            f"It has to be one of: {', '.join(CATEGORIES)}"
        )

    if not row["price"].strip():
        quit_with_error(f"Line {line_number} ({row['name']}): the price is empty.")

    if row["available"].strip().lower() not in ("yes", "no"):
        quit_with_error(
            f"Line {line_number} ({row['name']}): available is "
            f"'{row['available']}'. It has to be yes or no."
        )


# ============================================================
# TURNING A ROW INTO HTML
# ============================================================

def render_item(row):
    """Build the HTML for one bake."""
    # html.escape turns & into &amp; and so on. Without it, a name
    # like "Peaches & Cream" would produce broken HTML.
    name = html.escape(row["name"].strip())
    description = html.escape(row["description"].strip())
    photo = html.escape(row["photo"].strip())

    price_html = render_price(row["price"])

    sold_out = row["available"].strip().lower() == "no"
    classes = "item sold-out" if sold_out else "item"

    return f"""          <article class="{classes}">
            <div class="photo" style="background-image: url('{PHOTO_FOLDER}/{photo}')"></div>
            <div class="text">
              <h3>{name}</h3>
              <p>{description}</p>
{price_html}
            </div>
          </article>"""


def render_price(raw):
    """Turn the price column into one or more price lines.

    A plain number gets a currency sign and two decimals:
        2.5                     ->  $2.50
    Anything else is used exactly as you typed it:
        $4.00 per cookie        ->  $4.00 per cookie
    Split with a | to get several lines on one card:
        $20 - reg|$25 - oreos   ->  two lines
    """
    lines = []
    for part in raw.split("|"):
        part = part.strip()
        if not part:
            continue
        try:
            # Looks like a plain number? Format it nicely.
            part = f"{CURRENCY}{float(part):.2f}"
        except ValueError:
            pass  # Not a number, so leave the wording alone.
        lines.append(f'              <p class="price">{html.escape(part)}</p>')
    return "\n".join(lines)


def build():
    items = read_items()

    if not TEMPLATE_FILE.exists():
        quit_with_error(f"Can't find {TEMPLATE_FILE}. Is the templates folder there?")

    page = TEMPLATE_FILE.read_text(encoding="utf-8")

    # Fill each tab with the items whose category matches
    for category, placeholder in CATEGORIES.items():
        matching = [r for r in items if r["category"].strip().lower() == category]
        blocks = [render_item(row) for row in matching]
        page = page.replace(placeholder, "\n".join(blocks))
        print(f"  {category}: {len(matching)} items")

    page = page.replace("{{SEASON_NOTE}}", html.escape(SEASON_NOTE))
    from zoneinfo import ZoneInfo
    from datetime import datetime
    page = page.replace("{{BUILD_DATE}}", datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%d %B %Y"))

    OUTPUT_FILE.write_text(page, encoding="utf-8")

    sold_out = [r["name"] for r in items if r["available"].strip().lower() == "no"]
    if sold_out:
        print(f"  marked sold out: {', '.join(sold_out)}")

    print(f"\nWrote {OUTPUT_FILE.name}. Commit and push it to update the site.")
    check_photos(items)


def check_photos(items):
    """Warn about photos that aren't there yet, without stopping."""
    folder = HERE / PHOTO_FOLDER
    missing = [
        r["photo"] for r in items
        if not (folder / r["photo"].strip()).exists()
    ]
    if missing:
        print(f"\nNote: {len(missing)} photo(s) not in {PHOTO_FOLDER}/ yet:")
        for photo in missing:
            print(f"  {photo}")
        print("Those items will show a plain colour block until you add them.")


def quit_with_error(message):
    print(f"\nStopped: {message}\n")
    sys.exit(1)


# ============================================================

if __name__ == "__main__":
    print("Building the menu from items.csv\n")
    build()

    if "--serve" in sys.argv:
        import http.server
        import socketserver
        import os

        os.chdir(HERE)
        print("\nServing at http://localhost:8000 — press Ctrl+C to stop.")
        with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nStopped.")
