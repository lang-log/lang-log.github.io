"""The data table and the facts table of the record pages (dist/components/data-table/)."""

from html import escape


def cell(content, label):
    """One cell of a data table. The column's label is repeated inside the cell for
    the phone layout (dist/record.css shows each row as a block there)."""
    if not content:
        return '<td class="data-empty"></td>'
    return f'<td><span class="data-label" aria-hidden="true">{escape(label)}</span>{content}</td>'


def data_table(head, rows):
    """A table with a header row (the data table of record pages, dist/record.css).
    Each row is (cells, row class): one HTML string per column, an empty string for an
    empty cell, and "" when the row has no class of its own."""
    thead = "".join(f'<th scope="col">{escape(h)}</th>' for h in head)
    body = ""
    for cells, cls in rows:
        attr = f' class="{escape(cls)}"' if cls else ""
        body += (
            f"<tr{attr}>" + "".join(cell(x, h) for x, h in zip(cells, head, strict=True)) + "</tr>"
        )
    return f'<table class="data-table"><thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table>'


def facts_table(rows, header_html=False):
    """A table of one fact per row: the label as a row header, then the value (HTML).
    With header_html the labels are HTML too (links), otherwise plain text."""
    body = "".join(
        f'<tr><th scope="row">{k if header_html else escape(k)}</th><td>{v}</td></tr>'
        for k, v in rows
    )
    return f'<table class="data-table facts-table"><tbody>{body}</tbody></table>'
