# Usability — Campus Customs

Four changes after the core shop worked. Two make the website easier to use. Two make the stylist more accurate and safer.

## Front end

### 1. Search the rack

**What was added.** The products page has a search box beside the garment cuts. It filters the cards already on the page by name, color, garment type, and description. The line next to the box counts how many pieces are still on the glass. If nothing matches, the page says so instead of showing an empty grid.

**Why it helps.** The catalogue is 102 pieces. A shopper who wants “baseball” or “navy” should not have to scroll the whole rack. A shorter list is faster to use, and an empty search tells them to try another word instead of looking like the shop failed to load.

### 2. The open piece comes on screen, and the stylist says if the chat is kept

**What was added.** Opening a product, including a card the stylist just put under the navigation, scrolls the large photo and the full write-up up under the nav. The stylist header says “Saved for” plus the shopper’s name when they are signed in, and “This visit only” when they are a guest.

**Why it helps.** A match row can sit above the detail, so a click used to leave the large image below the fold. Bringing that photo on screen is the piece they asked to see. The header tells a guest the thread will not be here next time, and it tells a signed-in shopper the house is keeping it. That is less confusing at the counter, and it makes the saved-chat feature obvious.

## Agent and backend

### 3. “This” stays on the piece that is open

**What was added.** When a shopper is on a product page and says “this,” “it,” or “this one” — including “do you have this in pink” — the cards sent back to the page are only that open catalogue row. A type question such as “what crew necks do you have?” still returns the lane. The open row is read from the catalogue, not invented.

**Why it helps.** A question about the piece on screen was able to drop a different garment on the glass next to the right answer. Keeping the card on the open piece means the shopper sees the item they are holding, and the business does not show a second product they did not ask for.

### 4. A reply check for price, discount, orders, and passwords

**What was added.** Before the model runs, a question that asks for a password, a discount, a coupon, an order, or an email gets a fixed refusal. After the model replies, any dollar amount has to be a price a tool or the open catalogue row actually returned. A reply that invents a percent off, claims an order or an email, or states a password is replaced with a short refusal. The shopper still gets an answer. It is just not an unchecked one.

**Why it helps.** A wrong price or a made-up discount is a bad sale. Refusing passwords, orders, and emails keeps the counter from promising something the shop cannot do. The check sits in the backend, so it still holds if the model ignores the prompt.
