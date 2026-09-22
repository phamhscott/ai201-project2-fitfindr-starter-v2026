"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


_WORD_RE = re.compile(r"[a-z0-9]+")
_SIZE_TOKEN_RE = re.compile(r"[a-z]+\d+(?:\.\d+)?|\d+(?:\.\d+)?|[a-z]+")
_SEARCH_FILLER_WORDS = {
    "a",
    "an",
    "and",
    "find",
    "for",
    "i",
    "item",
    "looking",
    "me",
    "please",
    "the",
    "want",
}


def _search_terms(text: str) -> set[str]:
    """Normalize meaningful words used by the plain keyword search."""
    normalized = (
        text.casefold()
        .replace("'", "")
       .replace("’", "")
    )
    return {
        word
        for word in _WORD_RE.findall(normalized)
        if word not in _SEARCH_FILLER_WORDS
    }


def _size_tokens(size: str) -> set[str]:
    """Split sizes into complete tokens without making ``L`` match ``XL``."""
    return set(_SIZE_TOKEN_RE.findall(size.casefold()))


def _size_matches(listing_size: str, requested_size: str) -> bool:
    """Match a requested size against complete, case-insensitive size tokens."""
    requested = _size_tokens(requested_size)
    available = _size_tokens(listing_size)
    return bool(requested) and requested.issubset(available)


def _listing_text(listing: dict) -> str:
    """Collect the descriptive listing fields searched by keyword overlap."""
    values = [
        listing.get("title", ""),
        listing.get("description", ""),
        listing.get("category", ""),
        listing.get("condition", ""),
        listing.get("brand") or "",
        listing.get("platform", ""),
        " ".join(listing.get("style_tags") or []),
        " ".join(listing.get("colors") or []),
    ]
    return " ".join(str(value) for value in values)


def _format_listing(listing: dict) -> str:
    """Format the listing fields a styling prompt needs."""
    return "\n".join(
        [
            f"- title: {listing.get('title', '')}",
            f"- description: {listing.get('description', '')}",
            f"- category: {listing.get('category', '')}",
            f"- style tags: {', '.join(listing.get('style_tags') or [])}",
            f"- size: {listing.get('size', '')}",
            f"- condition: {listing.get('condition', '')}",
            f"- price: ${float(listing.get('price', 0)):.2f}",
            f"- colors: {', '.join(listing.get('colors') or [])}",
            f"- brand: {listing.get('brand') or 'unknown'}",
            f"- platform: {listing.get('platform', '')}",
        ]
    )


def _format_wardrobe(items: list[dict]) -> str:
    """Format wardrobe pieces while preserving their exact saved names."""
    lines = []
    for item in items:
        line = (
            f"- {item.get('name', '')} | category: {item.get('category', '')} | "
            f"colors: {', '.join(item.get('colors') or [])} | "
            f"style tags: {', '.join(item.get('style_tags') or [])}"
        )
        if item.get("notes"):
            line += f" | notes: {item['notes']}"
        lines.append(line)
    return "\n".join(lines)


# ── Tool 1: search_listings ───────────────────────────────────────────────────


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """

    listings = load_listings()
    query_terms = _search_terms(description)
    if not query_terms:
        return []

    scored = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if (
            size is not None
            and size.strip()
            and not _size_matches(listing["size"], size)
        ):
            continue

        searchable_text = _listing_text(listing)
        overlap = query_terms & _search_terms(searchable_text)
        if not overlap:
            continue

        # Exact phrases break ties in favor of closer matches. Python's sort is
        # stable, so equal scores retain the source file's deterministic order.
        phrase_bonus = int(description.strip().casefold() in searchable_text.casefold())
        scored.append((len(overlap) + phrase_bonus, listing))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    wardrobe_items = wardrobe.get("items") or []
    listing_text = _format_listing(new_item)

    if wardrobe_items:
        prompt = f"""New thrift listing:
{listing_text}

User's saved wardrobe:
{_format_wardrobe(wardrobe_items)}

Suggest one or two outfits that combine the new listing with pieces from the
saved wardrobe. Use the complete, exact saved name of at least one wardrobe
item so the user can identify it. Do not invent pieces the user owns. Keep the
answer concise and return only the outfit suggestion."""
    else:
        prompt = f"""New thrift listing:
{listing_text}

The user's wardrobe is empty. Suggest one or two general ways to style this
item, including garment, shoe, or accessory types that would pair with it. Do
not claim the user already owns any suggested piece. Keep the answer concise
and return only the styling advice."""

    response = generate(
        prompt,
        system=(
            "You are FitFindr's suggest_outfit tool. Base every suggestion on "
            "the supplied listing and wardrobe data, and do not add analysis "
            "outside the requested outfit advice."
        ),
    ).strip()
    if response:
        return response

    if wardrobe_items:
        return (
            f"Pair {new_item.get('title', 'the new item')} with "
            f"{wardrobe_items[0].get('name', 'a saved wardrobe piece')}."
        )
    return (
        f"Pair {new_item.get('title', 'the new item')} with neutral basics, "
        "comfortable shoes, and a simple accessory that complements its colors."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "A fit card could not be created because an outfit suggestion is required."

    style_tags = new_item.get("style_tags") or []
    prompt = f"""New thrift listing:
{_format_listing(new_item)}

Outfit suggestion:
{outfit.strip()}

Write a ready-to-post social caption of two to four sentences. It must mention
the item, its exact price, its exact platform value, and at least one complete
style-tag phrase from the listing. Describe the outfit's vibe naturally rather
than sounding like a product description. Do not invent listing details, and
return only the caption."""

    response = generate(
        prompt,
        system=(
            "You are FitFindr's create_fit_card tool. Return only a concise, "
            "ready-to-post caption that follows every supplied content rule."
        ),
    ).strip()
    if response:
        return response

    tag = style_tags[0] if style_tags else "thrifted"
    return (
        f"Found {new_item.get('title', 'this piece')} for "
        f"${float(new_item.get('price', 0)):.2f} on "
        f"{new_item.get('platform', 'the resale platform')}. "
        f"Its {tag} vibe works with the suggested outfit."
    )
