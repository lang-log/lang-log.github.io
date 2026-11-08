"""The labels Lang Log gives every languoid itself: its medium (modality:
spoken, signed or written) and whether it is constructed (an artificial or
formal language). Shown on every page as "Medium".

For Glottolog records they come from the group Glottolog lists the record
under (its category in dist/data.json, read before the groups that are not
languoids are left out). tools/build_data.py writes them into dist/data.json;
the pages and languoid.json read them from there.
"""

# Glottolog group -> modality; records under no listed group are spoken.
MODALITY_OF_GROUP = {"Sign Language": "signed"}
# Glottolog groups whose records are constructed languages.
CONSTRUCTED_GROUPS = {"Artificial Language"}


def labels(category):
    """{"modality": ..., "constructed": ...} for a Glottolog category."""
    return {
        "modality": MODALITY_OF_GROUP.get(category, "spoken"),
        "constructed": category in CONSTRUCTED_GROUPS,
    }


# Domain of the signs-and-scripts data (tools/build_visual.py) -> modality.
MODALITY_OF_DOMAIN = {"sign": "signed", "scripts": "written"}


def medium_text(n):
    """The "Medium" line of a page, such as "Medium: spoken · constructed".
    dist/record.js writes the same text for records it shows."""
    return "Medium: " + " · ".join([n["modality"]] + (["constructed"] if n["constructed"] else []))
