"""Campus Customs stylist. The chat route calls run_agent."""

from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import dotenv_values
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from audit import append_run, steps_from_result
from models import ChatReply, ProductCard, ProductLookup, ShopperDeps, StockLookup
from tools import (
    asks_for_a_type,
    card_for,
    clear_cards,
    lookup_product,
    open_piece,
    recent_chat,
    shop_facts,
    shopper_identity,
    stock_by_size,
    take_cards,
)

HERE = Path(__file__).resolve().parent
PROMPT_PATH = HERE / "prompts" / "prompt.md"
MODEL_NAME = "gpt-6-astra"
BASE_URL = "https://api.portkey.ai/v1"
COURSE = HERE.parent.parent


def _portkey_key() -> str:
    """Read PORTKEY_API_KEY only. Do not take a model name from those files."""
    candidates = [
        HERE.parent / ".env",
        COURSE / ".env",
        COURSE / "Class Notes" / "Lecture 6" / ".env",
        COURSE / "Class Notes" / "Lecture 4" / ".env",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        key = (dotenv_values(path).get("PORTKEY_API_KEY") or "").strip()
        if key:
            return key
    return (os.getenv("PORTKEY_API_KEY") or "").strip()


PORTKEY_API_KEY = _portkey_key()


def _model() -> OpenAIResponsesModel | None:
    if not PORTKEY_API_KEY:
        return None
    provider = OpenAIProvider(api_key=PORTKEY_API_KEY, base_url=BASE_URL)
    return OpenAIResponsesModel(MODEL_NAME, provider=provider)


_MODEL = _model()
agent = Agent(
    _MODEL if _MODEL is not None else "test",
    system_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
    deps_type=ShopperDeps,
    output_type=ChatReply,
    retries=1,
)
agent.tool_plain(shop_facts)
agent.tool_plain(lookup_product)
agent.tool_plain(stock_by_size)


def shopper_context(ctx: RunContext[ShopperDeps]) -> str:
    deps = ctx.deps
    lines = [shopper_identity(deps.name, deps.email)]
    if deps.page_path:
        lines.append("Page path: " + deps.page_path)
    lines.append(open_piece(deps.product_id))
    return "\n".join(lines)


def who_is_chatting(ctx: RunContext[ShopperDeps]) -> str:
    """Name and email of the shopper at the counter.

    Call this to greet them or when they ask who they are.
    A guest has no name and no email. There is never a password here.
    """

    return shopper_identity(ctx.deps.name, ctx.deps.email)


def page_item(ctx: RunContext[ShopperDeps]) -> str:
    """The catalogue piece open on the shopper's screen.

    Call this when they say this, it, or this one, including a color or a size
    of that piece. The product id comes from the page they are on.
    """

    return open_piece(ctx.deps.product_id)


def saved_chat(ctx: RunContext[ShopperDeps]) -> str:
    """Recent saved lines for the signed-in shopper.

    Call this when they ask what you remember from another visit.
    A guest has no saved chat.
    """

    return recent_chat(ctx.deps.user_id)


agent.system_prompt(dynamic=True)(shopper_context)
agent.tool(who_is_chatting)
agent.tool(page_item)
agent.tool(saved_chat)




_THIS = re.compile(r"\b(this|it|this one|that one)\b", re.I)
_MONEY = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")
_BLOCKED_ASK = (
    (re.compile(r"\bpassword\b", re.I),
     "I can't read or repeat a password. Sign in on the page if this is your account."),
    (re.compile(r"(\d+\s*%\s*off|percent off|\bdiscount\b|\bcoupon\b|promo code|half off)", re.I),
     "Campus Customs does not take a discount at this counter. The price on the piece is the catalogue price."),
    (re.compile(r"(place (the |my )?order|buy it for me|charge my card|send (me )?an email|email me)", re.I),
     "I can't place an order or send an email. I can tell you the piece, the price, and what is in stock."),
)
_UNSAFE_REPLY = re.compile(
    r"(\d+\s*%\s*off|percent off|discount of|half off|\bcoupon\b|promo code|"
    r"password is|password hash|your password|"
    r"order (is|has been) placed|placed your order|purchase is complete|"
    r"email (has been|was) sent|i emailed|shipped your)",
    re.I,
)
SAFE_PRICE = (
    "I will not quote a price that did not come back from the catalogue. "
    "Ask for the piece again and I will look it up."
)
SAFE_OFFER = (
    "I can't offer a discount, place an order, send an email, or read a password. "
    "The price on the piece is the catalogue price."
)


def blocked_ask(message: str) -> str | None:
    """A fixed refusal for a password, a discount, an order, or an email."""

    for pattern, sentence in _BLOCKED_ASK:
        if pattern.search(message or ""):
            return sentence
    return None


def about_this_piece(message: str) -> bool:
    """True when the shopper is pointing at the piece already on screen."""

    return bool(_THIS.search(message or ""))


def focus_open_piece(message: str, product_id: str, cards: list[ProductCard]) -> list[ProductCard]:
    """Keep cards on the open piece when they said this. A type question still returns the lane."""

    if not product_id or asks_for_a_type(message) or not about_this_piece(message):
        return cards
    kept = [card for card in cards if card.product_id == product_id]
    if kept:
        return kept[:1]
    one = card_for(product_id)
    return [one] if one is not None else []


def _add_price(prices: set[int], value) -> None:
    if value is None or value == "":
        return
    try:
        prices.add(int(float(value)))
    except (TypeError, ValueError):
        return


def _collect_prices(content, prices: set[int]) -> None:
    if isinstance(content, ProductLookup):
        for item in content.shown:
            _add_price(prices, item.price)
        for item in content.cards:
            _add_price(prices, item.price)
        return
    if isinstance(content, StockLookup):
        _add_price(prices, content.price)
        for item in content.candidates:
            _add_price(prices, item.price)
        return
    if isinstance(content, dict):
        _add_price(prices, content.get("price"))
        for key in ("shown", "cards", "candidates"):
            for item in content.get(key) or []:
                if isinstance(item, dict):
                    _add_price(prices, item.get("price"))
        return
    if isinstance(content, str):
        for model in (ProductLookup, StockLookup):
            try:
                parsed = model.model_validate_json(content)
            except Exception:
                continue
            _collect_prices(parsed, prices)
            return


def allowed_prices(result, product_id: str) -> set[int]:
    """Dollar amounts the tools, or the open catalogue row, actually returned."""

    prices: set[int] = set()
    for message in result.new_messages():
        for part in getattr(message, "parts", ()):
            if getattr(part, "part_kind", "") != "tool-return":
                continue
            _collect_prices(getattr(part, "content", None), prices)
    if product_id:
        card = card_for(product_id)
        if card is not None:
            _add_price(prices, card.price)
    return prices


def quoted_prices(reply: str) -> set[int]:
    return {int(float(match)) for match in _MONEY.findall(reply or "")}


def guard_reply(reply: str, allowed: set[int]) -> str:
    """Replace an unchecked price, a discount, an order, an email, or a password."""

    if _UNSAFE_REPLY.search(reply or ""):
        return SAFE_OFFER
    if any(price not in allowed for price in quoted_prices(reply)):
        return SAFE_PRICE
    return reply


def _cards_from_result(result) -> list[ProductCard]:
    """Read the cards lookup_product already returned in this run."""

    cards: list[ProductCard] = []
    for message in result.new_messages():
        for part in getattr(message, "parts", ()):
            if getattr(part, "tool_name", "") != "lookup_product":
                continue
            if getattr(part, "part_kind", "") != "tool-return":
                continue
            content = getattr(part, "content", None)
            found = None
            if isinstance(content, ProductLookup):
                found = content.cards
            elif isinstance(content, dict):
                found = content.get("cards")
            elif isinstance(content, str):
                try:
                    parsed = ProductLookup.model_validate_json(content)
                except Exception:
                    parsed = None
                found = parsed.cards if parsed is not None else None
            if not found:
                continue
            pulled: list[ProductCard] = []
            for item in found:
                if isinstance(item, ProductCard):
                    pulled.append(item)
                elif isinstance(item, dict):
                    pulled.append(ProductCard.model_validate(item))
            if pulled:
                cards = pulled
    return cards


def _preface(deps: ShopperDeps) -> str:
    if deps.email:
        who = f"Signed-in shopper: {deps.name} ({deps.email})."
    else:
        who = "Guest shopper. Not signed in. This visit is not saved."
    if deps.product_id:
        page = (
            f"They are on {deps.page_path or 'a product page'}. "
            f"Open product id: {deps.product_id}. "
            "'this' means that id. Use the open-piece context before you answer."
        )
    else:
        page = "No single product is open."
    return who + " " + page


def run_agent(
    message: str,
    history: list[dict] | None = None,
    deps: ShopperDeps | None = None,
) -> ChatReply:
    """Answer one shopper message. history is earlier turns, not this one."""
    deps = deps or ShopperDeps()
    if _MODEL is None:
        reply = "The stylist cannot reach the model. PORTKEY_API_KEY is missing."
        append_run([], "no_model", message, reply)
        return ChatReply(reply=reply)
    prior = list(history or [])
    if prior and prior[-1].get("content", "").strip() == message.strip():
        prior = prior[:-1]
    lines = []
    for turn in prior:
        who = "Shopper" if turn.get("role") == "shopper" else "Stylist"
        text = str(turn.get("content") or "").strip()
        if text:
            lines.append(f"{who}: {text}")
    prompt = message.strip()
    if lines:
        prompt = "Conversation so far:\n" + "\n".join(lines) + "\n\nShopper: " + prompt
    clear_cards()
    prompt = _preface(deps) + "\n\n" + prompt
    held = blocked_ask(message)
    if held:
        append_run([], "blocked", message, held)
        return ChatReply(reply=held)
    try:
        result = agent.run_sync(prompt, deps=deps, usage_limits=UsageLimits(request_limit=10))
    except Exception as exc:
        append_run([], "error", message, type(exc).__name__)
        raise
    reply = result.output
    cards = focus_open_piece(message, deps.product_id, _cards_from_result(result) or take_cards())
    safe = guard_reply(reply.reply, allowed_prices(result, deps.product_id))
    stop = "guarded" if safe != reply.reply else "completed"
    append_run(steps_from_result(result), stop, message, safe)
    return reply.model_copy(update={"reply": safe, "products": cards})
