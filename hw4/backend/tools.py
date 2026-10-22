"""Tools the stylist can call.

lookup_product and stock_by_size read data/campus_customs.db.
save_exchange writes chat_messages for a signed-in shopper only.
These tools never open users.password_hash.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import urllib.request

from models import ProductCard, ProductLookup, ProductRecord, SizeCount, StockLookup, WearAdvice, WearStop

CARD_CAP = 24
# The tool may run in another task, so this list is module state the request can read.
_PULLED: list[ProductCard] = []

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
_SIZE_ALIASES = {
    "xs": "XS",
    "xsmall": "XS",
    "extrasmall": "XS",
    "s": "S",
    "small": "S",
    "m": "M",
    "med": "M",
    "medium": "M",
    "l": "L",
    "large": "L",
    "xl": "XL",
    "xlarge": "XL",
    "extralarge": "XL",
    "xxl": "XXL",
    "xxlarge": "XXL",
    "2xl": "XXL",
    "extraextralarge": "XXL",
}
_SKIP = {
    "a", "an", "the", "for", "in", "on", "of", "and", "or", "with", "me", "my",
    "is", "are", "do", "you", "how", "much", "many", "what", "whats", "price",
    "cost", "stock", "size", "sizes", "have", "got", "there", "this", "that",
    "please", "tell", "about", "from", "your", "campus", "customs", "yale",
    "item", "piece", "one", "some", "any",
}
_COLORS = {
    "navy", "blue", "white", "black", "gray", "grey", "heather", "red",
    "green", "gold", "pink", "purple", "orange", "brown", "yellow",
}


def shop_facts() -> str:
    """Facts about the Campus Customs house. Use this for where the shop is, what it sells, and what you must not invent."""

    return (
        "Campus Customs is the Yale shop at 57 Broadway, New Haven. "
        "This counter is the night edit of that rack: hoodies, crews, tees, "
        "quarter-zips, and jackets from the catalogue. "
        "Description, price, and stock come only from lookup_product and stock_by_size, "
        "which read campus_customs.db. Do not invent a price or a quantity. "
        "Password hashes are never yours to read."
    )


def lookup_product(query: str) -> ProductLookup:
    """Look up catalogue rows for a price, a product, or a type of item.

    Call this before you quote a price, a description, or a color, and when
    the shopper asks what you have in a type such as crew necks, hoodies,
    tees, quarter-zips, or jackets. Returns ProductLookup. cards is the
    structured list the website renders (image, name, price, blurb).
    Read price and description from shown. found false means it is not on
    the rack. Do not invent a price or a piece.
    """

    result = _lookup(query)
    _PULLED.clear()
    _PULLED.extend(result.cards)
    return result


def clear_cards() -> None:
    """Drop cards from an earlier question in this same request."""

    _PULLED.clear()


def take_cards() -> list[ProductCard]:
    """Cards from the lookup the agent just ran."""

    return list(_PULLED)


def stock_by_size(product_id: str, size: str = "") -> StockLookup:
    """Read inventory for a stock question.

    Call this when they ask how many are left or whether a size is in,
    including when the same message also asks the price. Pass the product_id
    from lookup_product and the size they named. Returns StockLookup.
    Read quantity and in_stock. in_stock false means that size is out of stock.
    Do not invent a quantity.
    """

    return _stock(product_id, size)


def _connect() -> sqlite3.Connection | None:
    if not DATABASE.is_file():
        return None
    db = sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def _load():
    db = _connect()
    if db is None:
        return None
    try:
        catalogue = db.execute(
            "SELECT product_id, name, garment_type, description, colors, "
            "search_tags, image_file_path, price FROM catalogue"
        ).fetchall()
        inventory = db.execute(
            "SELECT product_id, size, quantity FROM inventory"
        ).fetchall()
    finally:
        db.close()
    stock: dict[str, dict[str, int]] = {}
    for row in inventory:
        stock.setdefault(row["product_id"], {})[row["size"]] = int(row["quantity"])
    return catalogue, stock


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if word not in _SKIP and word not in _COLORS and len(word) > 1]


def _color_words(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word in _COLORS]


def _json_list(raw: str | None) -> list[str]:
    try:
        value = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _flat(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _score(query: str, tokens: list[str], row: sqlite3.Row) -> int:
    name = row["name"] or ""
    product_id = row["product_id"] or ""
    phrase = _flat(query)
    name_flat = _flat(name)
    id_flat = product_id.replace("-", " ")
    if phrase and (phrase == name_flat or phrase == id_flat or phrase == product_id.lower()):
        return 1000
    score = 0
    if phrase and phrase in name_flat:
        score += 220
    if phrase and phrase in id_flat:
        score += 180
    name_tokens = set(re.findall(r"[a-z0-9]+", name.lower()))
    id_tokens = set(re.findall(r"[a-z0-9]+", product_id.lower()))
    garment_tokens = set(re.findall(r"[a-z0-9]+", (row["garment_type"] or "").lower()))
    extra = set()
    for item in _json_list(row["search_tags"]) + _json_list(row["colors"]):
        extra.update(re.findall(r"[a-z0-9]+", item.lower()))
    description_tokens = set(re.findall(r"[a-z0-9]+", (row["description"] or "").lower()))
    hits = 0
    for token in tokens:
        if token in name_tokens:
            score += 16
            hits += 1
        elif token in id_tokens:
            score += 12
            hits += 1
        elif token in garment_tokens:
            score += 8
            hits += 1
        elif token in extra:
            score += 5
            hits += 1
        elif token in description_tokens:
            score += 2
            hits += 1
    if tokens and hits == len(tokens):
        score += 36
    if hits == 0:
        return 0
    return score


def _color_ok(row: sqlite3.Row, colors: list[str]) -> bool:
    if not colors:
        return True
    blob = " ".join(
        [row["name"] or "", row["description"] or ""] + _json_list(row["colors"])
    ).lower()
    wanted = {"gray" if color == "grey" else color for color in colors}
    blob_words = set(re.findall(r"[a-z0-9]+", blob))
    if "grey" in blob_words:
        blob_words.add("gray")
    return bool(wanted & blob_words)


def _top(ranked):
    if not ranked:
        return []
    best = ranked[0][0]
    if best >= 800:
        floor = 800
    elif best >= 160:
        floor = max(160, int(best * 0.55))
    else:
        floor = max(8, int(best * 0.75))
    return [row for score, _, row in ranked if score >= floor]



_LANES = (
    ("quarter", ("quarter zip", "quarterzip", "1 4 zip")),
    ("hood", ("hoodie", "hoodies", "hooded")),
    ("crew", ("crew neck", "crew necks", "crewneck", "crews")),
    ("jacket", ("jacket", "jackets", "bomber")),
    ("tee", ("t shirt", "tshirt", "tees", "tee")),
)


def _asked_lane(query: str) -> str | None:
    text = _flat(query)
    for lane, phrases in _LANES:
        for phrase in phrases:
            if re.search(rf"(^| ){re.escape(phrase)}( |$)", text):
                return lane
    return None


def _row_in_lane(row: sqlite3.Row, lane: str) -> bool:
    kind = (row["garment_type"] or "").lower()
    name = (row["name"] or "").lower()
    if lane == "quarter":
        return "quarter" in kind or "1 4" in name or "1/4" in name
    if lane == "hood":
        return "hood" in kind or "hoodie" in name
    if lane == "crew":
        return "crew" in kind and "t-shirt" not in kind and "hood" not in kind
    if lane == "jacket":
        return "jacket" in kind or "bomber" in kind
    if lane == "tee":
        return "t-shirt" in kind or kind.strip() == "tee"
    return False


_TYPE_NOISE = {
    "what", "whats", "which", "show", "have", "got", "sell", "carry", "any",
    "some", "your", "you", "do", "does", "shop", "rack", "there", "kinds",
    "kind", "type", "types", "options", "option", "pieces", "piece", "me",
    "neck", "necks", "zip", "zips", "pullover", "pullovers",
}


def _type_ask(query: str, lane: str) -> bool:
    text = _flat(query)
    phrases = [phrase for name, phrases in _LANES if name == lane for phrase in phrases]
    for phrase in sorted(phrases, key=len, reverse=True):
        text = re.sub(rf"(^| ){re.escape(phrase)}( |$)", " ", text)
    leftovers = [
        word for word in text.split()
        if word not in _SKIP and word not in _COLORS and word not in _TYPE_NOISE and len(word) > 1
    ]
    return not leftovers


def _lane_rows(catalogue, query: str, colors: list[str]):
    lane = _asked_lane(query)
    if not lane or not _type_ask(query, lane):
        return None
    picked = [row for row in catalogue if _row_in_lane(row, lane) and _color_ok(row, colors)]
    if not picked and colors:
        picked = [row for row in catalogue if _row_in_lane(row, lane)]
    if not picked:
        return None
    picked.sort(key=lambda row: (row["name"] or "").lower())
    return picked


def _matches(catalogue, query: str):
    text = (query or "").strip()
    if not text:
        return []
    tokens = _tokens(text)
    colors = _color_words(text)
    lane_rows = _lane_rows(catalogue, text, colors)
    if lane_rows is not None:
        return lane_rows
    ranked = []
    for row in catalogue:
        score = _score(text, tokens, row)
        if score <= 0:
            continue
        if not _color_ok(row, colors):
            continue
        ranked.append((score, row["name"].lower(), row))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    if ranked:
        return _top(ranked)
    if colors:
        return _matches_without_color(catalogue, text)
    return []


def _matches_without_color(catalogue, query: str):
    tokens = _tokens(query)
    ranked = []
    for row in catalogue:
        score = _score(query, tokens, row)
        if score <= 0:
            continue
        ranked.append((score, row["name"].lower(), row))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return _top(ranked)



def _image(path: str | None) -> str:
    name = Path(path or "").name
    if not name:
        return ""
    return f"/media/{name}"


def _ordered_sizes(counts: dict[str, int]) -> list[str]:
    ordered = [size for size in SIZE_ORDER if size in counts]
    ordered.extend(size for size in counts if size not in SIZE_ORDER)
    return ordered


def _size_counts(counts: dict[str, int]) -> list[SizeCount]:
    return [
        SizeCount(size=size, quantity=counts[size], in_stock=counts[size] > 0)
        for size in _ordered_sizes(counts)
    ]


def _record(row: sqlite3.Row, stock: dict[str, dict[str, int]]) -> ProductRecord:
    description = (row["description"] or "").strip()
    return ProductRecord(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"] or "",
        description=description,
        price=float(row["price"]),
        colors=_json_list(row["colors"]),
        image=_image(row["image_file_path"]),
        description_is_stub="vision blocked" in description.lower(),
        sizes=_size_counts(stock.get(row["product_id"], {})),
    )


def _blurb(description: str, stub: bool) -> str:
    if stub:
        return "Photo on the rack. The book does not describe this one further."
    sentence = re.split(r"(?<=\.)\s", description, maxsplit=1)[0].strip()
    if len(sentence) <= 110:
        return sentence
    cut = sentence[:110]
    last = cut.rfind(" ")
    end = last if last > 48 else 110
    return cut[:end].rstrip() + "…"


def _card(row: sqlite3.Row) -> ProductCard:
    description = (row["description"] or "").strip()
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        price=float(row["price"]),
        image=_image(row["image_file_path"]),
        blurb=_blurb(description, "vision blocked" in description.lower()),
    )


def _lookup(query: str) -> ProductLookup:
    loaded = _load()
    if loaded is None:
        return ProductLookup(
            found=False,
            query=query,
            note="The catalogue file is missing. Do not invent a product, a price, or a quantity.",
        )
    catalogue, stock = loaded
    rows = _matches(catalogue, query)
    if not rows:
        return ProductLookup(
            found=False,
            query=query,
            note="NO MATCH. No catalogue row matched in campus_customs.db. Do not invent a product, a price, or a quantity.",
        )
    shown = rows[:4]
    card_rows = rows[:CARD_CAP]
    if len(rows) == 1:
        note = "ONE MATCH. Use this description, this price, and these quantities only. The card is that piece."
    else:
        note = (
            f"{len(rows)} catalogue rows matched. {len(card_rows)} cards go on the website. "
            "Introduce the set in a short line. Do not invent a piece that is not in cards. "
            "Quote a price only from shown or cards."
        )
    return ProductLookup(
        found=True,
        query=query,
        match_count=len(rows),
        shown=[_record(row, stock) for row in shown],
        cards=[_card(row) for row in card_rows],
        note=note,
    )


def _canonical_size(size: str) -> str | None:
    key = re.sub(r"[^a-z0-9]+", "", (size or "").lower())
    if not key:
        return ""
    if key in _SIZE_ALIASES:
        return _SIZE_ALIASES[key]
    upper = (size or "").strip().upper()
    if upper in SIZE_ORDER:
        return upper
    return None


def _stock(product_id: str, size: str) -> StockLookup:
    loaded = _load()
    if loaded is None:
        return StockLookup(
            found=False,
            note="The catalogue file is missing. Do not invent a quantity.",
        )
    catalogue, stock = loaded
    wanted = (product_id or "").strip()
    row = next((item for item in catalogue if item["product_id"] == wanted), None)
    if row is None:
        rows = _matches(catalogue, wanted)
        if len(rows) == 1:
            row = rows[0]
        elif not rows:
            return StockLookup(
                found=False,
                note=f"NO MATCH. No catalogue row for {wanted!r}. Do not invent a price or a quantity.",
            )
        else:
            return StockLookup(
                found=False,
                candidates=[_card(item) for item in rows[:4]],
                note="MORE THAN ONE MATCH. Pass one product_id to stock_by_size before you quote a quantity.",
            )
    counts = stock.get(row["product_id"], {})
    chosen = _canonical_size(size)
    base = dict(
        found=True,
        product_id=row["product_id"],
        name=row["name"],
        price=float(row["price"]),
    )
    if chosen is None:
        known = ", ".join(SIZE_ORDER)
        return StockLookup(
            **base,
            note=f"Size {size!r} is not a catalogue size. Sizes on the rack are {known}. Do not invent a quantity.",
        )
    sizes = _size_counts(counts)
    if chosen == "":
        if not sizes:
            return StockLookup(**base, note="No inventory rows. Do not invent a quantity.")
        return StockLookup(
            **base,
            sizes=sizes,
            note="Every size is listed. Quote a quantity only from sizes. Where in_stock is false, say that size is out of stock.",
        )
    asked = next((item for item in sizes if item.size == chosen), None)
    if asked is None:
        return StockLookup(
            **base,
            size=chosen,
            note=f"No inventory row for size {chosen}. Do not invent a quantity.",
        )
    if not asked.in_stock:
        note = f"OUT OF STOCK. Tell the shopper {chosen} is out of stock. Do not say this size is available."
    else:
        unit = "unit" if asked.quantity == 1 else "units"
        note = f"{asked.quantity} {unit} in stock."
    return StockLookup(
        **base,
        size=asked.size,
        quantity=asked.quantity,
        in_stock=asked.in_stock,
        sizes=sizes,
        note=note,
    )


def shopper_identity(name: str, email: str) -> str:
    """Name and email for the person at the counter. Empty email means a guest."""

    if not (email or "").strip():
        return (
            "Guest. No one is signed in, so you do not have a name or an email. "
            "Chat anyway. Do not invent an account, and do not claim this visit was saved."
        )
    return (
        f"Signed in as {name.strip() or 'the shopper'}, {email.strip()}. "
        "Greet them by that name. Do not ask them to repeat the email. "
        "A password is not available to you."
    )


def open_piece(product_id: str) -> str:
    """Catalogue row for the product page on screen. Empty id means no piece is open."""

    wanted = (product_id or "").strip()
    if not wanted:
        return (
            "NO OPEN PIECE. The shopper is not on a product page. "
            "'this' does not name a catalogue row. Ask which piece, or call lookup_product."
        )
    loaded = _load()
    if loaded is None:
        return "The catalogue file is missing. Do not invent the open piece."
    catalogue, stock = loaded
    row = next((item for item in catalogue if item["product_id"] == wanted), None)
    if row is None:
        return f"NO OPEN PIECE. {wanted!r} is not in the catalogue. Do not invent it."
    colors = ", ".join(_json_list(row["colors"])) or "none listed"
    description = (row["description"] or "").strip()
    price = float(row["price"])
    price_text = str(int(price)) if price == int(price) else f"{price:.2f}"
    size_bits = []
    for item in _size_counts(stock.get(row["product_id"], {})):
        if item.in_stock:
            size_bits.append(f"{item.size} {item.quantity}")
        else:
            size_bits.append(f"{item.size} OUT OF STOCK")
    sizes = ", ".join(size_bits) if size_bits else "no inventory rows"
    return (
        "OPEN PIECE. The shopper is looking at this catalogue row. "
        "'this' and 'it' mean this product_id.\n"
        f"product_id: {row['product_id']}\n"
        f"name: {row['name']}\n"
        f"garment_type: {row['garment_type']}\n"
        f"price: {price_text}\n"
        f"colors: {colors}\n"
        f"image: {_image(row['image_file_path'])}\n"
        f"description: {description}\n"
        f"stock: {sizes}\n"
        "A color that is not in colors is not offered on this piece. Say so. "
        "A size marked OUT OF STOCK must be told that way. Do not invent a price or a quantity."
    )


def _saved_card(item: object) -> dict | None:
    if not isinstance(item, dict):
        return None
    product_id = str(item.get("product_id") or item.get("productId") or "").strip()
    if not product_id:
        return None
    filename = Path(str(item.get("image_file_path") or item.get("image") or "")).name
    image = f"/media/{filename}" if filename else ""
    blurb = str(item.get("blurb") or "").strip()
    if not blurb:
        blurb = _blurb(str(item.get("description") or ""), False)
    try:
        price = float(item.get("price") or 0)
    except (TypeError, ValueError):
        price = 0.0
    return {
        "productId": product_id,
        "name": str(item.get("name") or product_id),
        "price": price,
        "image": image,
        "blurb": blurb,
    }


def load_chat(user_id: int, limit: int = 40) -> list[dict]:
    """Saved lines for one account, oldest first. Guests have no rows here."""

    db = _connect()
    if db is None:
        return []
    try:
        rows = db.execute(
            """
            SELECT role, content, products_json
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        db.close()
    turns = []
    for row in reversed(rows):
        role = "shopper" if row["role"] == "user" else "stylist"
        products = []
        if row["products_json"]:
            try:
                raw = json.loads(row["products_json"])
            except json.JSONDecodeError:
                raw = []
            if isinstance(raw, list):
                products = [card for item in raw if (card := _saved_card(item))]
        turns.append(
            {"role": role, "content": row["content"] or "", "products": products}
        )
    return turns


def recent_chat(user_id: int | None) -> str:
    """Text of the saved thread. A guest has nothing stored."""

    if not user_id:
        return (
            "No saved chat. This shopper is not signed in, so earlier visits are not stored."
        )
    turns = load_chat(user_id, limit=20)
    if not turns:
        return "Signed in, and chat_messages has no lines for this shopper yet."
    lines = []
    for turn in turns[-12:]:
        who = "Shopper" if turn["role"] == "shopper" else "Stylist"
        lines.append(f"{who}: {turn['content']}")
    return "Saved chat from chat_messages:\n" + "\n".join(lines)


def save_exchange(user_id: int, user_text: str, assistant_text: str, products: list) -> None:
    """Write one shopper line and one stylist line. Call this only for a signed-in account."""

    payload = []
    for item in products:
        if hasattr(item, "model_dump"):
            payload.append(item.model_dump())
        elif isinstance(item, dict):
            payload.append(item)
    db = sqlite3.connect(DATABASE)
    try:
        db.execute(
            """
            INSERT INTO chat_messages (user_id, role, content, products_json)
            VALUES (?, 'user', ?, NULL)
            """,
            (user_id, (user_text or "").strip()[:4000]),
        )
        db.execute(
            """
            INSERT INTO chat_messages (user_id, role, content, products_json)
            VALUES (?, 'assistant', ?, ?)
            """,
            (user_id, (assistant_text or "").strip()[:4000], json.dumps(payload)),
        )
        db.commit()
    finally:
        db.close()


def asks_for_a_type(query: str) -> bool:
    """True when the words ask for a garment lane, not one named piece."""

    lane = _asked_lane(query)
    return bool(lane and _type_ask(query, lane))


def card_for(product_id: str) -> ProductCard | None:
    """One real card for a catalogue id. None when that id is not in the book."""

    loaded = _load()
    if loaded is None or not product_id:
        return None
    catalogue, _stock = loaded
    for row in catalogue:
        if row["product_id"] == product_id:
            return _card(row)
    return None


_ICON_WORDS = {
    "sun": "sun",
    "cloud": "cloud cover",
    "rain": "rain",
    "snow": "snow",
    "wind": "wind",
    "cold": "a cold hour",
    "night": "after dark",
}

_STOPS = (
    {"kind": "restaurant", "name": "Frank Pepe Pizza Napoletana", "where": "Wooster Street", "lanes": frozenset({"hood", "crew", "quarter", "jacket", "tee"}), "indoor": True, "why": "A late pie after class."},
    {"kind": "restaurant", "name": "Louis' Lunch", "where": "Crown Street", "lanes": frozenset({"tee", "crew"}), "indoor": True, "why": "A burger between lectures."},
    {"kind": "restaurant", "name": "Ordinary", "where": "Chapel Street", "lanes": frozenset({"crew", "quarter", "jacket"}), "indoor": True, "why": "A downtown dinner."},
    {"kind": "restaurant", "name": "Barcelona Wine Bar", "where": "Temple Street", "lanes": frozenset({"quarter", "jacket", "crew"}), "indoor": True, "why": "A long table after the shop."},
    {"kind": "restaurant", "name": "Claire's Corner Copia", "where": "Chapel Street", "lanes": frozenset({"jacket", "hood", "crew"}), "indoor": True, "why": "A slow lunch out of the weather."},
    {"kind": "restaurant", "name": "Atticus Bookstore Cafe", "where": "Chapel Street", "lanes": frozenset({"hood", "jacket", "quarter"}), "indoor": True, "why": "Wait out a shower with a book."},
    {"kind": "restaurant", "name": "Shell and Bones", "where": "Long Wharf", "lanes": frozenset({"jacket", "quarter"}), "indoor": True, "why": "A waterfront dinner."},
    {"kind": "restaurant", "name": "Arethusa Farm Dairy", "where": "Chapel Street", "lanes": frozenset({"tee", "crew"}), "indoor": True, "why": "A sweet stop on Chapel."},
    {"kind": "event", "name": "College Street Music Hall", "where": "College Street", "lanes": frozenset({"hood", "crew", "jacket", "quarter"}), "indoor": True, "why": "A show night."},
    {"kind": "event", "name": "Yale Repertory Theatre", "where": "Chapel Street", "lanes": frozenset({"crew", "quarter", "jacket"}), "indoor": True, "why": "A play on Chapel."},
    {"kind": "event", "name": "Shubert Theatre", "where": "College Street", "lanes": frozenset({"quarter", "jacket"}), "indoor": True, "why": "A dressed-up night."},
    {"kind": "event", "name": "Toad's Place", "where": "York Street", "lanes": frozenset({"hood", "tee", "crew"}), "indoor": True, "why": "A late set."},
    {"kind": "event", "name": "Yale University Art Gallery", "where": "Chapel Street", "lanes": frozenset({"jacket", "crew", "quarter"}), "indoor": True, "why": "An indoor hour on Chapel."},
    {"kind": "event", "name": "New Haven Green", "where": "downtown", "lanes": frozenset({"tee", "crew"}), "indoor": False, "why": "An afternoon on the Green."},
    {"kind": "event", "name": "East Rock Park", "where": "East Rock", "lanes": frozenset({"hood", "jacket", "crew"}), "indoor": False, "why": "A cold walk up the rock."},
    {"kind": "event", "name": "Lighthouse Point Park", "where": "the harbor", "lanes": frozenset({"tee", "quarter"}), "indoor": False, "why": "Sun on the shore."},
    {"kind": "event", "name": "Wooster Square", "where": "Wooster Square", "lanes": frozenset({"crew", "tee", "hood"}), "indoor": False, "why": "A loop past the park and the ovens."},
)


def _lane_of_kind(kind: str) -> str:
    text = (kind or "").lower()
    if "quarter" in text:
        return "quarter"
    if "jacket" in text or "bomber" in text:
        return "jacket"
    if "hood" in text:
        return "hood"
    if "crew" in text and "t-shirt" not in text:
        return "crew"
    return "tee"


def _icons_for_code(code: int, temp: int, wind: float) -> list[str]:
    icons: list[str] = []
    if code == 0:
        icons.append("sun")
    elif code in {1, 2, 3}:
        icons.extend(["sun", "cloud"])
    elif code in {45, 48}:
        icons.append("cloud")
    elif code in {71, 73, 75, 77, 85, 86}:
        icons.append("snow")
    elif code >= 51:
        icons.append("rain")
    else:
        icons.append("cloud")
    if wind >= 15 and "wind" not in icons:
        icons.append("wind")
    if temp <= 45 and "cold" not in icons:
        icons.append("cold")
    return icons


def _condition_word(code: int) -> str:
    if code == 0:
        return "clear"
    if code in {1, 2, 3}:
        return "partly cloudy"
    if code in {45, 48}:
        return "foggy"
    if code in {71, 73, 75, 77, 85, 86}:
        return "snowy"
    if code >= 51:
        return "rainy"
    return "cloudy"


def new_haven_sky() -> dict:
    """Live New Haven weather from Open-Meteo. A mild October read if the sky does not answer."""

    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=41.3083&longitude=-72.9279"
        "&current=temperature_2m,weather_code,wind_speed_10m"
        "&temperature_unit=fahrenheit&wind_speed_unit=mph"
        "&timezone=America/New_York"
    )
    try:
        with urllib.request.urlopen(url, timeout=4) as response:
            payload = json.loads(response.read().decode())
        current = payload["current"]
        temp = int(round(float(current["temperature_2m"])))
        code = int(current["weather_code"])
        wind = float(current["wind_speed_10m"])
        live = True
    except Exception:
        temp, code, wind, live = 58, 2, 8.0, False
    return {
        "temp": temp,
        "code": code,
        "wind": wind,
        "live": live,
        "icons": _icons_for_code(code, temp, wind),
        "condition": _condition_word(code),
    }


def _garment_icons(lane: str) -> list[str]:
    return {
        "hood": ["cloud", "cold", "night"],
        "crew": ["cloud", "wind", "night"],
        "tee": ["sun", "cloud"],
        "quarter": ["cloud", "wind", "night"],
        "jacket": ["rain", "wind", "cold"],
    }.get(lane, ["cloud"])


def _merge_icons(lane: str, sky_icons: list[str]) -> list[str]:
    merged: list[str] = []
    for icon in _garment_icons(lane) + sky_icons:
        if icon not in merged:
            merged.append(icon)
    if lane == "tee" and "cold" in sky_icons and "cold" not in merged:
        merged.append("cold")
    if lane == "tee" and "rain" in sky_icons:
        merged = [icon for icon in merged if icon != "sun"]
        if "rain" not in merged:
            merged.insert(0, "rain")
    return merged[:4]


def _stops_for(lane: str, sky_icons: list[str]) -> list[WearStop]:
    wet = "rain" in sky_icons or "snow" in sky_icons or "cold" in sky_icons
    ranked = [row for row in _STOPS if lane in row["lanes"]]
    if wet:
        indoor = [row for row in ranked if row["indoor"]]
        if len(indoor) >= 2:
            ranked = indoor + [row for row in ranked if row not in indoor]
    chosen = []
    for row in ranked:
        if any(item.name == row["name"] for item in chosen):
            continue
        chosen.append(WearStop(kind=row["kind"], name=row["name"], where=row["where"], why=row["why"]))
        if len(chosen) == 3:
            break
    return chosen


def when_to_wear(product_id: str) -> WearAdvice:
    """Weather icons and New Haven stops for one catalogue piece in the bag.

    Call this when a shopper queues a piece. Use only the icons and the stops
    in this return. Do not invent a temperature, a restaurant, or an event.
    """

    loaded = _load()
    row = None
    if loaded is not None and product_id:
        catalogue, _stock = loaded
        for item in catalogue:
            if item["product_id"] == product_id:
                row = item
                break
    if row is None:
        return WearAdvice(product_id=product_id, when="That piece is not on the rack, so there is no wear note.")
    sky = new_haven_sky()
    lane = _lane_of_kind(row["garment_type"] or "")
    icons = _merge_icons(lane, sky["icons"])
    words = [_ICON_WORDS[icon] for icon in icons if icon in _ICON_WORDS]
    if sky["live"]:
        sky_line = f"New Haven is {sky['temp']}° and {sky['condition']} right now."
    else:
        sky_line = "The live sky did not answer. This is a mild New Haven October read, about 58° and partly cloudy."
    when = f"{sky_line} Wear the {row['name']} for {', '.join(words)}."
    return WearAdvice(
        product_id=row["product_id"],
        name=row["name"],
        icons=icons,
        when=when,
        stops=_stops_for(lane, sky["icons"]),
    )
