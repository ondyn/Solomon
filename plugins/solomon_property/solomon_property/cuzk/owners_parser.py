"""
Solomon - owners.txt parser.

Parses the text-format ownership export used by Czech SVJ managers.
Each record is one or more name/address lines followed by a "Jednotka:" line.

Format examples:
    Novák Jan, Ulice 5, 14900 Praha 4
    Jednotka: 1937/6	73/9089

    SJ Hnyk Ondřej a Hnyková Simona, Adresa, 14900 Praha 4
    Jednotka: 1937/20	779/54534

    Kubánek Petr, Adresa...
    Kubánková Blanka, Adresa...
    Jednotka: 1941/2	205/27267

    SJ Schmidt Jaroslav a Schmidtová Liběna
    Jednotka: 1938/2	388/27267
    Schmidt Jaroslav, Žitná 610/23, ...
    Schmidtová Liběna, Adresa...

An owner record ends when we see "Jednotka:".
The SJM prefix "SJ " marks joint spousal ownership.
"MCP " marks multiple co-owners (more than 2).
Titles (Mgr., Ing., JUDr., PhDr., CSc., Bc., Ph.D.) are stripped for name parsing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TITLE_BEFORE_RE = re.compile(
    r"^(Mgr\.|Ing\.|JUDr\.|PhDr\.|MUDr\.|Bc\.|doc\.|prof\.)\s*", re.IGNORECASE
)
TITLE_AFTER_RE = re.compile(
    r",?\s*(CSc\.|Ph\.D\.|PhD\.|MBA|LL\.M\.|MSc\.)\s*$", re.IGNORECASE
)


@dataclass
class ParsedPerson:
    """A single person parsed from the owners file."""
    raw_name: str            # Full name as written
    title_before: str = ""
    first_name: str = ""
    last_name: str = ""
    title_after: str = ""
    address: str = ""        # Street + city from the same line


@dataclass
class ParsedOwnerRecord:
    """
    One ownership record from owners.txt.

    display_name: canonical name from CUZK (first line of the block)
    person_type: "natural", "sjm", or "legal"
    persons: list of individual persons (may be empty if parsing failed)
    flat_numbers: list of flat numbers, e.g. ["1937/6", "1940/3"]
    share_numerator / share_denominator: ownership share of common parts
    address: address line from the owner line
    """
    display_name: str
    person_type: str = "natural"   # natural | sjm | legal
    persons: list[ParsedPerson] = field(default_factory=list)
    flat_numbers: list[str] = field(default_factory=list)
    share_numerator: int | None = None
    share_denominator: int | None = None
    address: str = ""


def _split_name_address(line: str) -> tuple[str, str]:
    """
    Split 'Name Parts, Street Number, PostalCode City' into (name, address).

    Handles legal entities where the name itself contains commas:
        'INSTALACE, spol. s r.o., Kutnohorská 579...' → ('INSTALACE, spol. s r.o.', 'Kutnohorská 579...')
        'Novák Jan, Ulice 5, 14900 Praha 4'           → ('Novák Jan', 'Ulice 5, 14900 Praha 4')
    """
    parts = line.split(", ")
    if len(parts) <= 1:
        return line.strip(), ""

    # Legal suffix fragments that are part of the name, not the address
    legal_fragments = {"spol. s r.o.", "s.r.o.", "a.s.", "v.o.s.", "k.s.", "o.p.s.", "z.s."}

    name_parts = [parts[0]]
    i = 1
    while i < len(parts):
        part = parts[i]
        part_lower = part.lower().strip()
        # If this fragment is a known legal suffix, it's still part of the name
        if part_lower in legal_fragments:
            name_parts.append(part)
            i += 1
            continue
        # If this part starts with a digit (postal code or house number), it's address
        if part and part[0].isdigit():
            break
        break

    name = ", ".join(name_parts).strip()
    address = ", ".join(parts[i:]).strip()
    return name, address


def _parse_person_name(raw_name: str) -> tuple[str, str, str, str]:
    """
    Parse 'Novák Jan Ing.' or 'Ing. Jana Nováková' into (title_before, first, last, title_after).

    Czech convention: LastName FirstName [Titles]
    Or: TitleBefore LastName FirstName [TitleAfter]
    """
    name = raw_name.strip()

    # Extract trailing title
    title_after = ""
    m = TITLE_AFTER_RE.search(name)
    if m:
        title_after = m.group(1)
        name = name[: m.start()].strip()

    # Extract leading title
    title_before = ""
    m = TITLE_BEFORE_RE.match(name)
    if m:
        title_before = m.group(1)
        name = name[m.end():].strip()

    # Check for middle titles (e.g. "Ing." appearing after last name)
    # Pattern: Word Word Ing. → extract title
    words = name.split()
    mid_titles = []
    clean_words = []
    for w in words:
        if TITLE_BEFORE_RE.match(w):
            mid_titles.append(w.rstrip(".") + ".")
        else:
            clean_words.append(w)
    if mid_titles and not title_before:
        title_before = " ".join(mid_titles)
    elif mid_titles:
        title_before += " " + " ".join(mid_titles)
    words = clean_words

    if not words:
        return title_before, "", raw_name, title_after

    if len(words) == 1:
        # Only one word - treat as last name
        return title_before, "", words[0], title_after

    # Czech convention: LastName FirstName (sometimes FirstName LastName for foreign)
    # We can't tell reliably, so we use: first word = last name, rest = first name
    last_name = words[0]
    first_name = " ".join(words[1:])
    return title_before, first_name, last_name, title_after


def _parse_sjm_names(display_name: str) -> list[tuple[str, str]]:
    """
    Parse 'SJ LastName1 First1 a Last2Name First2' into list of (raw_name, address) pairs.

    Returns list of raw name strings for the two spouses.
    """
    # Remove "SJ " prefix
    body = re.sub(r"^SJ\s+", "", display_name).strip()
    # Split on " a " (Czech "and") - separates the two spouses
    parts = re.split(r"\s+a\s+", body, maxsplit=1)
    return [p.strip() for p in parts]


def _parse_mcp_names(display_name: str) -> list[str]:
    """Parse 'MCP Name1 a Name2' into list of raw names."""
    body = re.sub(r"^MCP\s+", "", display_name).strip()
    parts = re.split(r"\s+a\s+", body)
    return [p.strip() for p in parts]


def _parse_flat_line(line: str) -> tuple[list[str], int | None, int | None]:
    """
    Parse 'Jednotka: 1937/6, 1940/3\t73/9089' into (flat_numbers, num, denom).

    Returns: list of flat numbers, share numerator, share denominator
    """
    # Remove "Jednotka:" prefix
    body = re.sub(r"^Jednotka:\s*", "", line).strip()

    # Split by tab to separate flat numbers from share
    tab_parts = body.split("\t")
    flat_part = tab_parts[0].strip()
    share_part = tab_parts[1].strip() if len(tab_parts) > 1 else ""

    # Flat numbers may be comma-separated
    flat_numbers = [f.strip() for f in flat_part.split(",") if f.strip()]

    # Parse share fraction "num/denom"
    share_num = share_den = None
    m = re.match(r"(\d+)/(\d+)", share_part)
    if m:
        share_num = int(m.group(1))
        share_den = int(m.group(2))

    return flat_numbers, share_num, share_den


def _sjm_last_names(first_line: str) -> list[str]:
    """
    Extract the two last names from an SJM first line so we can recognise
    continuation address lines that follow the Jednotka line.

    'SJ Schmidt Jaroslav a Schmidtová Liběna' -> ['Schmidt', 'Schmidtová']
    Returns an empty list for non-SJM lines.
    """
    if not first_line.startswith("SJ "):
        return []
    raw_names = _parse_sjm_names(first_line)
    last_names = []
    for rn in raw_names:
        _tb, _fn, ln, _ta = _parse_person_name(rn)
        if ln:
            last_names.append(ln)
    return last_names


def parse_owners_txt(text: str) -> list[ParsedOwnerRecord]:
    """
    Parse a full owners.txt content and return a list of ParsedOwnerRecord.

    The format is: one or more name/address lines, then a "Jednotka:" line.
    Records are NOT separated by blank lines - each "Jednotka:" line ends a record.

    Format:
        Novák Jan, Ulice 5, 14900 Praha 4
        Jednotka: 1937/6\t73/9089
        SJ Hnyk Ondřej a Hnyková Simona, Adresa...
        Jednotka: 1937/20\t779/54534

    Some SJM records omit addresses on the owner line and instead list each
    spouse on a separate line AFTER the Jednotka line:

        SJ Schmidt Jaroslav a Schmidtová Liběna
        Jednotka: 1938/2\t388/27267
        Schmidt Jaroslav, Žitná 610/23, Nové Mesto, 11000 Praha 1
        Schmidtová Liběna, Šalounova 1938/8, Chodov, 14900 Praha 4

    Those continuation lines are absorbed into the preceding block when they
    start with one of the SJM last names.
    """
    lines = [ln.rstrip() for ln in text.splitlines()]
    records: list[ParsedOwnerRecord] = []

    # Build blocks: each block is all lines belonging to one owner record.
    # A block ends on a "Jednotka:" line, but for SJM records that omit the
    # owner address we also absorb subsequent lines that are per-spouse address
    # entries (they start with one of the SJM last names).
    blocks: list[list[str]] = []
    current: list[str] = []
    # When set, the current block ended with Jednotka and we are in look-ahead
    # mode: subsequent lines that match one of these last names are absorbed.
    absorbing_last_names: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            # Blank lines may appear between records - flush if block is complete
            if current and any(l.startswith("Jednotka:") for l in current):
                if not absorbing_last_names:
                    blocks.append(current)
                    current = []
            continue

        # Are we in look-ahead mode after a Jednotka line for an SJM record?
        if absorbing_last_names:
            # Check whether this line is a spouse address line
            first_word = line.split()[0].rstrip(",") if line.split() else ""
            if any(first_word == ln for ln in absorbing_last_names):
                # Absorb this spouse address line into the current block
                current.append(line)
                continue
            else:
                # Not a continuation - flush the completed block and start fresh
                blocks.append(current)
                current = []
                absorbing_last_names = []

        current.append(line)

        if line.startswith("Jednotka:"):
            # Check whether the first line of this block is an SJM without address
            first_line = current[0] if current else ""
            sjm_names = _sjm_last_names(first_line)
            # SJM without address: the owner line has NO comma (no address part)
            if sjm_names and "," not in first_line:
                # Enter look-ahead mode to absorb spouse address lines
                absorbing_last_names = sjm_names
            else:
                blocks.append(current)
                current = []

    # Flush remaining block
    if current:
        if absorbing_last_names:
            blocks.append(current)
        elif any(l.startswith("Jednotka:") for l in current):
            blocks.append(current)

    for owner_lines in blocks:
        # Find the Jednotka line within the block
        jednotka_idx = None
        for j, ol in enumerate(owner_lines):
            if ol.startswith("Jednotka:"):
                jednotka_idx = j
                break

        if jednotka_idx is None:
            # Block without Jednotka - skip
            continue

        # Parse the Jednotka line
        flat_numbers, share_num, share_den = _parse_flat_line(owner_lines[jednotka_idx])

        # Lines before Jednotka are owner name/address lines
        name_lines = owner_lines[:jednotka_idx]
        # Lines after Jednotka may be extra person lines (SJM Schmidt pattern)
        extra_lines = owner_lines[jednotka_idx + 1:]

        if not name_lines:
            continue

        first_name_line = name_lines[0]
        raw_name, address = _split_name_address(first_name_line)

        # Determine type and parse persons
        person_type = "natural"
        persons: list[ParsedPerson] = []

        if raw_name.startswith("SJ "):
            person_type = "sjm"
            sjm_names = _parse_sjm_names(raw_name)
            for sn in sjm_names:
                tb, fn, ln, ta = _parse_person_name(sn)
                persons.append(ParsedPerson(raw_name=sn, title_before=tb, first_name=fn, last_name=ln, title_after=ta))
            # Extra lines may have addresses for each spouse
            for extra in extra_lines:
                extra = extra.strip()
                if extra and not extra.startswith("Jednotka:"):
                    en, ea = _split_name_address(extra)
                    # Match to existing person by exact last name (first word of extra line)
                    extra_last = en.split()[0].rstrip(",") if en.split() else ""
                    for p in persons:
                        if p.last_name and extra_last == p.last_name:
                            p.address = ea
                            break

        elif raw_name.startswith("MCP "):
            person_type = "natural"  # Multiple co-owners - treat as separate naturals
            mcp_names = _parse_mcp_names(raw_name)
            for mn in mcp_names:
                tb, fn, ln, ta = _parse_person_name(mn)
                persons.append(ParsedPerson(raw_name=mn, title_before=tb, first_name=fn, last_name=ln, title_after=ta, address=address))

        elif _is_legal_entity(raw_name):
            person_type = "legal"
            # No person split for legal entities - the display_name is the company name
        else:
            # Natural person
            tb, fn, ln, ta = _parse_person_name(raw_name)
            persons.append(ParsedPerson(raw_name=raw_name, title_before=tb, first_name=fn, last_name=ln, title_after=ta, address=address))

            # Additional name lines in block (before Jednotka)
            for extra in name_lines[1:]:
                extra = extra.strip()
                if extra and not extra.startswith("Jednotka:"):
                    en, ea = _split_name_address(extra)
                    etb, efn, eln, eta = _parse_person_name(en)
                    persons.append(ParsedPerson(raw_name=en, title_before=etb, first_name=efn, last_name=eln, title_after=eta, address=ea))

            # Extra lines after Jednotka
            for extra in extra_lines:
                extra = extra.strip()
                if extra and not extra.startswith("Jednotka:"):
                    en, ea = _split_name_address(extra)
                    etb, efn, eln, eta = _parse_person_name(en)
                    persons.append(ParsedPerson(raw_name=en, title_before=etb, first_name=efn, last_name=eln, title_after=eta, address=ea))

        records.append(ParsedOwnerRecord(
            display_name=raw_name,
            person_type=person_type,
            persons=persons,
            flat_numbers=flat_numbers,
            share_numerator=share_num,
            share_denominator=share_den,
            address=address,
        ))

    return records


def _is_legal_entity(name: str) -> bool:
    """Heuristic: detect legal entities (s.r.o., a.s., etc.)."""
    legal_suffixes = ["s.r.o.", "a.s.", "spol. s r.o.", "v.o.s.", "k.s.", "o.p.s.", "z.s."]
    name_lower = name.lower()
    return any(s in name_lower for s in legal_suffixes)
