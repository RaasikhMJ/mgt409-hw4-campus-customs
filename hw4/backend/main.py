"""Campus Customs shop API.

This is the file Uvicorn runs. From the backend folder:

  uvicorn main:app --reload --port 8000

The agent itself stays in prompts/prompt.md, agent.py, tools.py, and models.py.
This app only calls run_agent for the chat widget.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from auth import DUMMY_HASH, hash_password, issue_session, read_session, verify_password

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "campus_customs.db"
IMAGES = (ROOT / "data" / "products").resolve()
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SizeOut(BaseModel):
    size: str
    quantity: int


class ProductOut(BaseModel):
    productId: str
    name: str
    garmentType: str
    description: str
    price: float
    image: str
    colors: list[str]
    sizes: list[SizeOut]


class StylistTurn(BaseModel):
    role: str
    content: str


class PageIn(BaseModel):
    path: str = ""
    productId: str = ""


class StylistIn(BaseModel):
    message: str = Field(min_length=1)
    history: list[StylistTurn] = []
    page: PageIn | None = None


class StylistOut(BaseModel):
    reply: str
    products: list[dict] = []


def connect() -> sqlite3.Connection:
    if not DATABASE.is_file():
        raise HTTPException(status_code=500, detail="The catalogue file is missing.")
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def sizes_for(db: sqlite3.Connection, product_id: str) -> list[SizeOut]:
    rows = db.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?",
        (product_id,),
    ).fetchall()
    by_size = {row["size"]: int(row["quantity"]) for row in rows}
    ordered = [size for size in SIZE_ORDER if size in by_size]
    ordered.extend(size for size in by_size if size not in SIZE_ORDER)
    return [SizeOut(size=size, quantity=by_size[size]) for size in ordered]


def as_product(row: sqlite3.Row, sizes: list[SizeOut]) -> ProductOut:
    try:
        colors = json.loads(row["colors"] or "[]")
    except json.JSONDecodeError:
        colors = []
    if not isinstance(colors, list):
        colors = []
    filename = Path(row["image_file_path"] or "").name
    return ProductOut(
        productId=row["product_id"],
        name=row["name"],
        garmentType=row["garment_type"],
        description=row["description"],
        price=float(row["price"]),
        image=f"/media/{filename}" if filename else "",
        colors=[str(color) for color in colors],
        sizes=sizes,
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"shop": "Campus Customs", "status": "open"}


@app.get("/api/products", response_model=list[ProductOut])
def list_products() -> list[ProductOut]:
    db = connect()
    try:
        rows = db.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        return [as_product(row, sizes_for(db, row["product_id"])) for row in rows]
    finally:
        db.close()


@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str) -> ProductOut:
    db = connect()
    try:
        row = db.execute(
            "SELECT * FROM catalogue WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="That piece is not on the rack.")
        return as_product(row, sizes_for(db, product_id))
    finally:
        db.close()


@app.get("/media/{filename}")
def product_image(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    if safe_name != filename or not safe_name.lower().endswith(".jpg"):
        raise HTTPException(status_code=404, detail="No image by that name.")
    path = (IMAGES / safe_name).resolve()
    if not path.is_relative_to(IMAGES) or not path.is_file():
        raise HTTPException(status_code=404, detail="No image by that name.")
    return FileResponse(path, media_type="image/jpeg")


def _plain(value: str, limit: int) -> str:
    return " ".join((value or "").split())[:limit]


def _open_product_id(value: str) -> str:
    import re

    text = (value or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9-]{1,80}", text):
        return ""
    return text


def _signed_in_shopper(cc_session: str | None):
    user_id = read_session(cc_session)
    if user_id is None:
        return None
    db = connect()
    try:
        return _load_public_user(db, user_id)
    finally:
        db.close()


@app.get("/api/chat")
def chat_history(cc_session: str | None = Cookie(default=None)) -> list[dict]:
    """Saved stylist lines for the signed-in shopper. Guests have none."""
    shopper = _signed_in_shopper(cc_session)
    if shopper is None:
        raise HTTPException(status_code=401, detail="Sign in to see a saved chat.")
    from tools import load_chat

    return load_chat(shopper.id)


@app.post("/api/stylist", response_model=StylistOut)
def stylist(body: StylistIn, cc_session: str | None = Cookie(default=None)) -> StylistOut:
    """The chat widget calls this. Guests can chat. Only a signed-in shopper is saved."""
    from agent import run_agent
    from models import ShopperDeps
    from tools import load_chat, save_exchange

    shopper = _signed_in_shopper(cc_session)
    if shopper is None:
        history = [turn.model_dump() for turn in body.history]
    else:
        history = [
            {"role": turn["role"], "content": turn["content"]}
            for turn in load_chat(shopper.id)
        ]
    page = body.page
    deps = ShopperDeps(
        user_id=shopper.id if shopper else None,
        name=shopper.name if shopper else "",
        email=shopper.email if shopper else "",
        page_path=_plain(page.path, 200) if page else "",
        product_id=_open_product_id(page.productId) if page else "",
    )
    try:
        result = run_agent(body.message, history, deps)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="The stylist missed that. Try once more.",
        ) from exc
    if shopper is not None:
        save_exchange(shopper.id, body.message, result.reply, result.products)
    return StylistOut(
        reply=result.reply,
        products=[item.model_dump(by_alias=True) for item in result.products],
    )


class ShopperOut(BaseModel):
    id: int
    firstName: str
    lastName: str
    email: str
    name: str


class RegisterIn(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str
    confirmPassword: str


class LoginIn(BaseModel):
    email: str
    password: str


COOKIE = "cc_session"
COOKIE_MAX_AGE = 14 * 24 * 3600


def _clean_name(value: str, label: str) -> str:
    text = " ".join(value.split())
    if not text:
        raise HTTPException(status_code=400, detail=f"{label} is required.")
    return text


def _clean_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@") or " " in email:
        raise HTTPException(status_code=400, detail="Enter a real email address.")
    return email


def _check_password(password: str, confirm: str | None = None) -> str:
    if confirm is not None and password != confirm:
        raise HTTPException(status_code=400, detail="Those passwords do not match.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Use at least 8 characters.")
    if len(password) > 128:
        raise HTTPException(status_code=400, detail="That password is too long.")
    return password


def _public_user(row: sqlite3.Row) -> ShopperOut:
    return ShopperOut(
        id=row["id"],
        firstName=row["first_name"] or "",
        lastName=row["last_name"] or "",
        email=row["email"],
        name=row["name"],
    )


def _load_public_user(db: sqlite3.Connection, user_id: int) -> ShopperOut | None:
    row = db.execute(
        "SELECT id, name, email, first_name, last_name FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return _public_user(row)


def _set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE,
        issue_session(user_id),
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


@app.post("/api/register", response_model=ShopperOut)
def register(body: RegisterIn, response: Response) -> ShopperOut:
    first = _clean_name(body.firstName, "First name")
    last = _clean_name(body.lastName, "Last name")
    email = _clean_email(body.email)
    password = _check_password(body.password, body.confirmPassword)
    password_hash = hash_password(password)
    db = connect()
    try:
        try:
            cursor = db.execute(
                """
                INSERT INTO users (name, email, password_hash, first_name, last_name)
                VALUES (?, ?, ?, ?, ?)
                """,
                (f"{first} {last}", email, password_hash, first, last),
            )
            db.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail="An account with that email already exists.",
            ) from None
        shopper = _load_public_user(db, int(cursor.lastrowid))
    finally:
        db.close()
    if shopper is None:
        raise HTTPException(status_code=500, detail="The account did not save.")
    _set_session(response, shopper.id)
    return shopper


@app.post("/api/login", response_model=ShopperOut)
def login(body: LoginIn, response: Response) -> ShopperOut:
    email = _clean_email(body.email)
    password = body.password
    db = connect()
    try:
        row = db.execute(
            "SELECT id, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None:
            verify_password(password, DUMMY_HASH)
            raise HTTPException(status_code=401, detail="Email or password is wrong.")
        if not verify_password(password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Email or password is wrong.")
        shopper = _load_public_user(db, row["id"])
    finally:
        db.close()
    if shopper is None:
        raise HTTPException(status_code=401, detail="Email or password is wrong.")
    _set_session(response, shopper.id)
    return shopper


@app.post("/api/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(COOKIE, path="/")
    return {"status": "signed-out"}


@app.get("/api/me", response_model=ShopperOut)
def me(cc_session: str | None = Cookie(default=None)) -> ShopperOut:
    user_id = read_session(cc_session)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Sign in first.")
    db = connect()
    try:
        shopper = _load_public_user(db, user_id)
    finally:
        db.close()
    if shopper is None:
        raise HTTPException(status_code=401, detail="Sign in first.")
    return shopper
