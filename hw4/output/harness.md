# Harness — Campus Customs

This file is the running description of the shop and the chatbot. Later problems add sections under the same headings. Do not replace a section when it grows. Add to it.

**Database:** `data/campus_customs.db`  
**Model for agent calls:** `gpt-6-astra` through Portkey (`PORTKEY_API_KEY` in `.env`)

## Tables

### catalogue

One row is one product a shopper can browse or ask about. 102 rows.

| Field | Why it matters |
|---|---|
| `product_id` | Stable id the shop, the images, and the inventory all share. The chatbot uses it to point at one real item. |
| `name` | The title shoppers see and the words they are most likely to type. |
| `garment_type` | Tells the page and the bot what kind of piece it is (hoodie, crewneck, t-shirt) so a request like "quarter zip" can match. |
| `description` | The honest product copy the chatbot should use instead of inventing details. |
| `colors` | JSON text of the colors on the item, so "navy hoodie" can be checked against the real garment. |
| `search_tags` | JSON text of extra search words (college, sport, logo) that the name alone does not contain. |
| `image_file_path` | Path under `data/products/` for the picture the shop shows when this item is on screen. |
| `price` | The only price the chatbot may quote. Stored in dollars as a number. |

### inventory

One row is one size of one product. 612 rows (102 products × XS, S, M, L, XL, XXL).

| Field | Why it matters |
|---|---|
| `id` | Row id for this size line. Not what the shopper asks for. |
| `product_id` | Links the size count back to one catalogue item. |
| `size` | The size the shopper wants. Stock is per size, not one number for the whole product. |
| `quantity` | Units left in that size. Zero means that size is out. The chatbot must say so instead of promising it. |

A product and a size appear together only once.

### users

One row is one account. 3 rows in the file we were given.

| Field | Why it matters |
|---|---|
| `id` | Ties an account to that person's chat history. |
| `name` | Display name already stored for the account. |
| `email` | Login id. It must be unique. |
| `password_hash` | The only form of the password that is saved. It is a salted PBKDF2 hash. The password itself is never written, and nothing that answers the shopper may read this field back. |
| `created_at` | When the account was created. |
| `first_name` | Given name for a greeting or a new account. |
| `last_name` | Family name for the account record. |

### chat_messages

One row is one line in a shopper's conversation. 22 rows were already in the database. This table is how the bot remembers a chat.

| Field | Why it matters |
|---|---|
| `id` | Id of that one message. |
| `user_id` | Whose conversation this line belongs to. |
| `role` | Whether the line was the shopper or the assistant. |
| `content` | The text that was said. |
| `products_json` | Products the bot attached to that turn, so the page can show the same items again. |
| `created_at` | When the line was saved, so memory stays in order. |

A signed-in shopper's lines are written here, one row for the shopper and one row for the stylist. `role` is `user` or `assistant`. `user_id` is that account. `products_json` on the assistant row is the cards from that reply. A guest chat is not written. When that shopper comes back, `GET /api/chat` reads these rows in `id` order and the widget shows them again.

## API

`backend/main.py` reads `data/campus_customs.db` and serves the shop. The agent will grow inside this same app.

| Route | Why it matters |
|---|---|
| `GET /api/products` | The rack. One object per catalogue row, with sizes and stock from inventory. |
| `GET /api/products/{product_id}` | One piece, for the single-item page. |
| `GET /media/{filename}` | The catalogue photo. The filename comes from `image_file_path`. Nothing outside `data/products` is served. |
| `POST /api/stylist` | The website chat. The widget posts the shopper's message here. `main.py` calls `run_agent` and returns `reply` plus `products`. |
| `GET /api/chat` | The signed-in shopper's saved lines. A guest gets no history from this route. |
| `POST /api/register` | Creates a row in `users`. The password is hashed before it is saved. |
| `POST /api/login` | Checks email and password, then sets an httpOnly session cookie. |
| `POST /api/logout` | Clears that cookie. |
| `GET /api/me` | The signed-in shopper. It never includes the password hash. |

Prices, names, and stock in these responses are the database values. The swag mark is still computed in the browser.

The file Uvicorn runs is `backend/main.py`. From that folder the command is `uvicorn main:app --reload --port 8000`.

The chat widget posts to `POST /api/stylist` on that app. The body is the shopper's message and the turns already on screen. The JSON back is `reply` plus `products`. The widget shows `reply`.

When the shopper asks what the shop has in a type, that same response is the card contract. Each item in `products` is `productId`, `name`, `price`, `image`, and `blurb`. `blurb` is the first sentence of the catalogue description, shortened. The page renders those fields as the rack under the nav. The cards come from `lookup_product`, and `run_agent` copies them onto the reply so a price on a card is the database price.

### How search results reach the page

A type question such as "what crew necks do you have?" travels in one direction. The page never searches the database itself.

1. The shopper types in the stylist. The widget posts `{ message, history }` to `POST /api/stylist`.
2. `backend/main.py` calls `run_agent` in `backend/agent.py`.
3. The system prompt in `backend/prompts/prompt.md` tells the agent to call `lookup_product` for that kind of question. The tool reads `catalogue` in `data/campus_customs.db` and returns a `ProductLookup`. The match list is `cards`, up to 24 `ProductCard` rows: `product_id`, `name`, `price`, `image`, and `blurb`.
4. `run_agent` copies those cards onto `ChatReply.products`. It takes them from the `lookup_product` tool return in that same run. A price on the list is the catalogue price.
5. The route answers with JSON: `reply` for the words, and `products` for the cards. In that JSON the id field is `productId`.
6. The widget shows `reply`. It passes `products` to the rack under the nav. Each card on the page shows the image, the name, the price, and the blurb.
7. A click on a card opens `/products/{productId}`. That is the same single-item page as the rest of the shop. It loads `GET /api/products/{product_id}`: large image on one side, and the full description, price, colors, and sizes on the other.

If `lookup_product` finds nothing, `products` is an empty list and the rack stays off the page.

### Customer memory

Guests can chat. Their turns stay in the browser for that visit and are not written to `chat_messages`. A signed-in shopper's turns are saved and loaded again on the next visit.

**How the history is stored**

`POST /api/stylist` reads the `cc_session` cookie. If it names an account, the route inserts two `chat_messages` rows after the reply: `role` `user` with the shopper's text, then `role` `assistant` with the reply and `products_json` for the cards. `user_id` is that account. `created_at` is the database clock. If the cookie is missing, the route still answers and writes nothing.

`GET /api/chat` reads that account's rows, oldest first, and the widget replaces the greeting with them. The assistant cards on the last saved reply can come back onto the rack. Logging out leaves the rows in the table. The next login reads them again.

**Customer fields the agent sees**

The agent deps are a `ShopperDeps` on every run. For a signed-in shopper the fields are `user_id`, `name`, and `email`, taken from `users` through the session. `name` is the display name. `email` is the login address. The dynamic system prompt and `who_is_chatting` show the name and the email. `saved_chat` uses `user_id` only to read `chat_messages`. The agent does not receive `password_hash`, the password, or the session key.

A guest still gets a `ShopperDeps`. `name` and `email` are empty, and `user_id` is empty. The prompt says they are a guest and that the visit is not saved. The on-screen history for that visit is sent in the request body. It is not loaded from the table.

**How the page context is passed**

The widget sends `page.path` and `page.productId` with the message. On `/products/baseball-left-chest-crewneck`, `productId` is `baseball-left-chest-crewneck`. On any other page, `productId` is empty. Those two values are copied onto `ShopperDeps.page_path` and `ShopperDeps.product_id`. The system prompt calls `open_piece` with that id, so the run already contains the catalogue name, price, colors, description, and size counts for the piece on screen. `page_item` returns the same row when the shopper says "this" or "do you have this in pink". A color that is not on that row is not offered. The id has to match a catalogue `product_id`. The page does not send a password or a made-up price.

`main.py` calls `run_agent` in `backend/agent.py`. That module reads `backend/prompts/prompt.md` once at startup and builds a PydanticAI agent on `gpt-6-astra` through Portkey (`https://api.portkey.ai/v1`), using the Responses API. `PORTKEY_API_KEY` is read from the class `.env` files, not from a model name in those files. Tools in `backend/tools.py` are registered on the agent. Reply and product-card shapes are in `backend/models.py`.

### Front end to FastAPI

The pages live in `frontend/` and run with Vite on port 5173 (`npm run dev` from that folder). They never open the database. Vite proxies `/api` and `/media` to `http://127.0.0.1:8000`, the FastAPI app. The rack calls `GET /api/products`. A single piece calls `GET /api/products/{product_id}`. Each product's `image` is already a `/media/...` path, and the browser loads that photo through the same proxy. Create account, log in, log out, and the signed-in name call `/api/register`, `/api/login`, `/api/logout`, and `/api/me`, and those requests send the session cookie. The floating stylist posts `{ message, history, page }` to `POST /api/stylist` with the session cookie and shows the `reply` that comes back. A signed-in shopper's earlier turns come from `GET /api/chat`. FastAPI also allows the origins `http://localhost:5173` and `http://127.0.0.1:5173` if a page calls port 8000 directly.

### How the agent is loaded

Start the API from the `backend/` folder:

```
uvicorn main:app --reload --port 8000
```

That command loads `backend/main.py` as `app`. The chat route calls `run_agent` in `backend/agent.py`. When that module loads, it reads `backend/prompts/prompt.md` and uses the whole file as the system prompt. The model name is fixed in `agent.py` as `gpt-6-astra`. The client is the OpenAI Responses API through Portkey at `https://api.portkey.ai/v1`, using `PORTKEY_API_KEY` from the class `.env` files. A model name in those files is not used. The agent's output type is `ChatReply` from `backend/models.py`. `shop_facts`, `lookup_product`, `stock_by_size`, `who_is_chatting`, `page_item`, and `saved_chat` from `backend/tools.py` are registered on the same agent. `--reload` restarts the process when those files change, so a new prompt is read on the next start.


## Models

Added in a later problem. Pydantic shapes for products, stock answers, and chat turns go here.

`backend/models.py` starts the agent shapes. `ChatReply` is the stylist's answer: the words in `reply`, and `products` for real cards. `ProductCard` is one catalogue piece (`product_id`, `name`, `price`, `image`). Cards stay empty until a tool fills them. Stock shapes come later.

Size counts are not a new field on the card. `stock_by_size` returns the size and the quantity, and the stylist states them in `reply`, including when a size is out of stock.

`lookup_product` returns a `ProductLookup`: `found`, and `shown` for the description, the price, and a `SizeCount` for every size. `stock_by_size` returns a `StockLookup`: `price`, `size`, `quantity`, and `in_stock`. The prompt tells the stylist to call `lookup_product` for a price and `stock_by_size` for a stock question, and to call both when the shopper asks for both. `in_stock` false means that size is out of stock.

`ShopperDeps` is the run context. It carries `user_id`, `name`, `email`, `page_path`, and `product_id`. Name and email are the account fields the agent may say. `product_id` is the piece open on the page. The password hash is not a field on it.

## Tools

Added in a later problem. Each tool gets a name, what it reads or writes, and what it must not invent.

`shop_facts` in `backend/tools.py` tells the agent where the house is and that it must not invent a price or a size. Product info and stock tools will be added in that same file.

`lookup_product` reads `catalogue` for the description, the price, the colors, and the image, and it includes each size's quantity from `inventory`. `stock_by_size` reads `inventory` for one product, and for one size when the shopper names it. Both take those numbers from `data/campus_customs.db`. They do not write, and they do not read `users` or `password_hash`. A quantity of 0 comes back as out of stock. The agent may not invent a price or a quantity these tools did not return.

### shop_facts

House facts only. It returns a short string: the shop is at 57 Broadway, New Haven, and the rack is hoodies, crews, tees, quarter-zips, and jackets. It has no lookup model. A house question does not carry a product id, a price, or a quantity, so those fields stay on the catalogue tools.

### lookup_product

Reads `catalogue` and joins each hit to its `inventory` counts. Returns a `ProductLookup`.

| Field | Why this field |
|---|---|
| `found` | Separates a real hit from a miss. A miss leaves `shown` empty. |
| `query` | Keeps the shopper's words beside the rows that came back. |
| `match_count` | Counts every hit, including ones past the four in `shown`, so a broad ask is not treated as one piece. |
| `shown` | The rows the stylist may talk about. Each row is a `ProductRecord`. |
| `note` | Says whether this is one match, several, or none, and tells the stylist to stay inside that list. |

`ProductRecord` is the row inside `shown`.

| Field | Why this field |
|---|---|
| `product_id` | The id `stock_by_size` and a product card both use. |
| `name` | The catalogue title, so the reply uses the rack's name. |
| `garment_type` | The type stored on the row, so a hoodie and a crew stay distinct. |
| `description` | The catalogue copy. The reply uses this text. |
| `price` | The catalogue price in dollars. This is the number a price answer quotes. |
| `colors` | The color list stored on the row. |
| `image` | The `/media/` path the shop already serves, so a card can show that photo. |
| `description_is_stub` | True when the stored description is only a filename stub. The reply then stays with that stub. |
| `sizes` | A `SizeCount` for every size on that product, so a quantity in the same answer is an inventory number. |

`SizeCount` is one size.

| Field | Why this field |
|---|---|
| `size` | The size label from `inventory` (XS through XXL). |
| `quantity` | The unit count on that size row. |
| `in_stock` | True when `quantity` is above 0. False means the reply says that size is out of stock. |

### stock_by_size

Reads `inventory` for one `product_id`, and for one size when the shopper names it. Returns a `StockLookup`.

| Field | Why this field |
|---|---|
| `found` | True when one catalogue row was chosen. False on a miss or when several names still match. |
| `product_id` | The row the counts belong to. |
| `name` | The catalogue title for that row. |
| `price` | The catalogue price of that same row, so a stock answer can repeat the real price. |
| `size` | The size they asked for. Empty when the reply should cover every size. |
| `quantity` | The unit count for that size. Zero is the out-of-stock count. Empty when no single size was asked. |
| `in_stock` | False when that size's quantity is 0. The reply then says out of stock. |
| `sizes` | The full `SizeCount` list, so any other size mentioned is still an inventory number. |
| `candidates` | A short `ProductCard` list when more than one name matched. The card keeps `product_id`, `name`, `price`, and `image` so the stylist can ask which piece before quoting a quantity. |
| `note` | The instruction for this result, including the out-of-stock line when `quantity` is 0. |

`candidates` uses `ProductCard` because a choice between pieces needs the id, the name, the price, and the photo. The full description stays on `ProductRecord` until one piece is chosen.

`lookup_product` also fills `cards` for the website. A type question such as crew necks, hoodies, tees, quarter-zips, or jackets returns the rows in that garment lane. A question that names one piece still returns that one row. Each card is a `ProductCard`: `product_id` so the page can open the piece, `name` and `price` from the catalogue, `image` as the `/media/` path, and `blurb` so the card can show a short line without a new sentence from the model. Up to 24 cards go on the reply. `run_agent` copies that list onto `ChatReply.products`.

`who_is_chatting` reads the shopper's name and email from `ShopperDeps`. `page_item` reads the open `product_id` from those same deps and looks up that catalogue row. `saved_chat` reads `chat_messages` for `user_id`. A guest gets an empty identity and an empty saved thread from those tools.

## Safety

Added in a later problem. Rules for prices, stock, passwords, and what the bot refuses.

The basics live in `backend/prompts/prompt.md` under Voice and Safety. The stylist does not invent products, prices, or stock, and does not read a password hash. A purchase over $2000.00 is a large-sum purchase: the stylist sends a verification email and does not treat that purchase as complete until the shopper confirms it. That same file grows when the rules get tighter.

A price has to come from `lookup_product`. A quantity has to come from `lookup_product` or `stock_by_size`. When the quantity is 0, the reply says that size is out of stock.

### Accounts

Create account writes one `users` row. Log in checks that row. The password is protected on the way in, in the file, and on the way back out.

**What is stored for a user**

| Field | What goes in it |
|---|---|
| `id` | New number for the account. Chat lines point at this, not at the email. |
| `name` | First name and last name joined, for a display name. |
| `email` | The login address, trimmed and lowercased. Unique. |
| `first_name` | Given name from the form. |
| `last_name` | Family name from the form. |
| `created_at` | When the row was inserted. |
| `password_hash` | The salted hash described below. |

The form also asks the shopper to type the password a second time. That confirm box is checked and then thrown away. It is not a column.

**How the password is always protected**

The password is never written to the database, the session, a log, or an API response. Before the insert, it is turned into a PBKDF2-HMAC-SHA256 hash with a new random salt. New accounts run 600,000 iterations, and that count is stored inside the hash string so the check does not depend on a guess. Seed accounts already in the file use the same algorithm at 120,000 iterations. Login recomputes the hash and compares it in constant time. A missing email and a wrong password return the same sentence, so the form does not reveal which one failed.

`GET /api/me`, register, and login return id, name, email, first name, and last name only. They do not return `password_hash`. The chatbot must not read that column either.

After a good login, the browser gets an httpOnly signed cookie. The cookie holds the user id and an expiry, not the password and not the hash. The signing key lives in `backend/.session_key`, which is gitignored. Log out deletes the cookie.

## Specs

Added in a later problem. How the running site is checked.

Problem 9 is written up in `output/usability.md`. The products page can be searched. Opening a piece scrolls that photo on screen, and the stylist says whether the chat is saved. A question about “this” piece keeps the card on that catalogue row. A reply that invents a price, a discount, an order, an email, or a password is replaced before it reaches the shopper.

Each stylist run appends to `output/audit_trail.json`. A row has the time, the tool name, a short argument, a short result, and why the loop stopped (`completed`, `guarded`, `blocked`, `no_model`, or `error`). The file is read and extended. A later run does not clear the earlier rows.

