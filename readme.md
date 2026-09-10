# Sugar & Salt Bakery site

A small static site for the bakery. The menu page is generated from a
spreadsheet by a Python script, so adding a bake means editing one row.

## Files

    items.csv                  the menu — this is the file you edit
    build.py                   reads items.csv, writes index.html
    templates/
      index.template.html      the page layout, with gaps for the items
    index.html                 GENERATED — do not edit by hand
    order.html                 the Google Form page
    styles.css                 all styling, shared by both pages
    images/                    photos, named to match the csv

## Changing the menu

1. Open `items.csv` (a spreadsheet will open it, or any text editor).
2. Add, edit or delete a row.
3. Run `python build.py`
4. Commit and push. The live site updates in about a minute.

### The columns

| column | what goes in it |
|---|---|
| name | the bake's name |
| description | one or two sentences. Put quotes around it if it contains a comma |
| price | `2.50` gets turned into `$2.50`. Anything else is used word for word, e.g. `$4.00 per cookie`. Split with `\|` for several price lines on one card |
| category | `allyear` or `seasonal` |
| photo | the filename inside `images/`, e.g. `cookies.jpg` |
| available | `yes`, or `no` to grey it out and label it sold out |

## Previewing before you push

    python build.py --serve

Then open http://localhost:8000

## Other things you might change

- Season note above the seasonal list: `SEASON_NOTE` near the top of `build.py`
- Colours and fonts: the six values at the top of `styles.css`
- Shop name, opening times, footer: `templates/index.template.html`
- The order form: the iframe in `order.html`
