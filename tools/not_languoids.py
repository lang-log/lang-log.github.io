"""Groups that a source lists but that are not languoids, such as Glottolog's
"Sign Language" and "L1 Sign Language" (source-data/lang-log/not-languoids.json).

Every script that builds the tree reads the list from here and calls lift(), so
the groups are left out in one way everywhere: each member's parent becomes its
nearest ancestor that is a languoid, or none (a top-level languoid).
"""

import json

from locations import ROOT

_LIST = json.loads(
    (ROOT / "source-data" / "lang-log" / "not-languoids.json").read_text(encoding="utf-8")
)

# {source: {record id: name}} of the groups to leave out.
NOT_LANGUOIDS = {source: ids for source, ids in _LIST.items() if not source.startswith("_")}


def lift(parents, source):
    """Return ({child: parent}, {child: grouping}) without the source's groups.

    parents maps each record id to its parent id in the source (None or a
    missing key at the top). The groups themselves are left out of the result.
    grouping maps each record that was listed under a group to the name of the
    nearest such group, so the source's claim is kept as a label.
    """
    groups = NOT_LANGUOIDS.get(source, {})
    lifted, grouping = {}, {}
    for child, parent in parents.items():
        if child in groups:
            continue
        while parent in groups:
            grouping.setdefault(child, groups[parent])
            parent = parents.get(parent)
        lifted[child] = parent
    return lifted, grouping
