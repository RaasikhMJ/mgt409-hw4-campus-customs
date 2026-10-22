# AI prompts — Homework 4: Campus Customs Shop + Chatbot

**Course:** MGT 409 — AI Foundations for Managers, Yale School of Management  
**Coder:** Goldie  
**Folder:** `YALE EMBA AI FOUNDATIONS/hw4 Campus Customs`

Each problem below has its own section. A section is filled only with prompts you typed. A follow-up is included only when a later prompt was needed, with one sentence on what the first prompt did not capture.

**How we move:** one problem at a time. The next section stays empty until you describe that problem.

**Current problem:** 13 — Push to GitHub  
**Next:** The homework stops here.

---

## Problem 1: Vibe coder prompts

**Status:** Done. This file is the work for this problem.

**Prompt:**

> what up Goldie: lets get a jump on the homework 4 for AI foundations

**Follow-up:**

> create AI_prompts.md log like in previous assignments. Make sure to put one secion for each problem. Each section must include: the problem number and title, at least one prompt ive typed, in my own words as much as posisble, one follow-up prompt if needed and a sentence that describes what was needed that was not captured on the inital prompt

The first prompt started Homework 4, but it did not say to keep a prompt log or what each problem section had to contain.

---

## Problem 2: Analyze the database

**Status:** Done. `data/campus_customs.db` is unpacked and the three tables were read.

**Prompt:**

> pull the databases for data/campus_customs.db. Make sur eyou understand the catalouge, inventory and users. Show me that you undrerstand by giving me a summary of what you found

**Follow-up:**

> hey Goldie: locate and start the file output/harness.md The idea is to write down each table and its field and one short line on why the line/field matter s for the shop setup and our chatbot. W ewill continue to grow this harness in the future so make sur eyou retain the structure

The first prompt asked for a spoken summary of the three tables. It did not ask for `output/harness.md`, a line on every field, or a structure later problems can keep growing.

---

## Problem 3: Build the Campus Customs website

**Status:** Done. The React shop is in `frontend/`: nav bar, Home, Products from the database with photos, single-item pages, and the chat panel in the bottom right.

**Prompt:**

> scaffold a react + vite + typescript font end for campus customs. Place a new navigation bar at the top of the page that links the main pages of the website: - Home - Products - About Us - Log In - Create Account. Pull campus customs style and working from yalebulldogblue.com but make sure the tone and style is more swaggy modern urban with some sexy prep appeal

**Follow-up:**

> on the products page show product images from the catalouge using the image paths in the database with basic product information (name, price, short description, swag rating) make each product open a single item page with a large image on one side, full product text on the other side (right) including description, price, sizes/stock when you locate them. If you click a card on products this is where it should take you.

The first prompt asked for the scaffold, the nav, and a swaggier urban-prep tone. It did not ask for catalogue photos, a swag rating, or a single-item page with sizes and stock.

**Follow-up:**

> Goldie add a chat interface in the bottom right of the site that functions as your personal swag stylist. A floating chat panel works. We will set this up to talk to an agent later but for now create a stub that will call the backend of the website later.

The product prompt put photos on the rack and a single-item page. It did not ask for a stylist chat, or a stub shaped to call the shop backend later.

**Follow-up:**

> A small API will be needed to read the database. start with s simple FastAPI in backend/main.py to serve the products and images to be grown into an agent back end later. Lay the foundations goldie. Let me know when youre ready for more.

The chat prompt asked for a floating stylist that would call the backend later. It did not ask for the FastAPI app, or for the rack itself to be read from the database through that API.

---

## Problem 4: Create account and login

**Status:** Done. Create account and log in write to `users`, and the password is stored only as a hash.

**Prompt:**

> God work so far Goldie. Now lets build a normal create-account/login flow. Create Account sould incliude: first name, last name, email, password, confirm password box is required. Then log in should require email and password. new accounts should go into the users table to track. make sure you store the passwords securely so AI and human hackers can't access them

**Follow-up:**

> the seed database has a test user to use while building. email: test@campuscustoms.yale.edu password: password verify you can log in as that user and a brand new account you create works

The first prompt asked for the forms and for passwords to be stored safely. It did not ask to prove the seed test user, or to prove a brand-new account can sign in after it is created.

**Follow-up:**

> update output/harness.md with how auth works meaning what is stored for a user and how the passwords are always protected

The check prompt asked for proof that the seed user and a new account can sign in. It did not ask for the harness to list every stored user field or the rules that keep the password protected.

---

## Problem 5: PydanticAI agent backend

**Status:** Done. The chat widget posts to the agent through `backend/main.py`, and the agent is the four files under `backend/`.

**Prompt:**

> Alright Goldie: Now we need to build the shop chatbot as a PydanticAI agent behind FastAPI which should plu into our front end chat widget.

**Follow-up:**

> the API should be put in backend/main.py which is the file ran with Uvicorn

The first prompt asked for a PydanticAI agent behind FastAPI, plugged into the chat widget. It did not say the app had to live in `backend/main.py`, or that Uvicorn runs that file.

**Follow-up:**

> Keeo the agent as the following four files: backend/prompts/prompt.md as system prompt to be grown later. backend/agent.py - agent entry/wiring backend/tools.py as tools for the egent to call backend/models.py which is Pydantic/PydanticAI structured types

The main.py prompt said where Uvicorn starts. It did not name the four agent files, or say the system prompt has to stay in `prompts/prompt.md` so later problems can grow it.

**Follow-up:**

> The Campus Customs voice and safety basics should be in prompts/prompt.md with tools and safety to be expanded later. start or update types in models.py for chat replies and product cards as needed

The four-files prompt named where the agent lives. It did not say the prompt file had to hold the shop voice and the safety basics, or that `models.py` had to define the chat reply and the product card.


**Follow-up:**

> in main.py expose a chat route so a message from the website returns a reply from the agent and anything else you need for products/authorization using the most appropriate AI model and API key where necessary for the agent

The four-files prompt said where the agent lives. It did not ask for the website message to come back from a chat route on `main.py`, or for that same file to keep products and accounts on the model key.

**Follow-up:**

> in output/harness.md note how the front end to FastAPI and how the agent is loaded (prompt file + model) make sure the backend/ folder like: uvicorn main:app --reload --port 8000

The chat-route prompt asked for a website message to come back from `main.py`. It did not ask the harness to record how the Vite front end reaches FastAPI, how the agent is loaded from the prompt file and `gpt-6-astra`, or to pin the start command to the `backend/` folder.



---

## Problem 6: Tools: product info and stock

**Status:** Done. Description, price, and size counts are read from `data/campus_customs.db`, and a sold-out size is said plainly.

**Prompt:**

> Goldie I need to make sure you ave tools that look up real info from campus_customs.db: product description, price, how many are in stock by size when the customer asks  -  the agent must use the database and should not invent prices or quantities. if a size is out of stock make sure you state it clearly

**Follow-up:**

> expand prompts/prompt.md so the agent knows to call these tools for a price and stock question. add or update return types in models.py

The tools prompt asked for database lookups of description, price, and stock. It did not say the prompt had to spell out calling those tools on a price and stock question, or that `models.py` had to hold the return types.

**Follow-up:**

> in output/harness.md list eash tool and explain which model fields you shose for lookup results and why

The return-types prompt asked for the prompt file and the models. It did not ask the harness to list each tool, or to explain why those lookup fields were chosen.

---

## Problem 7: Chat search that updates the page

**Status:** Done. A type question returns structured cards, the page renders them, and each card opens its single-item page.

**Prompt:**

> lets build a special feature to the site that performs the following: when a customer asks about a type of item as an example " what crew necks do you have?" the agent should search the catalouge and the website should dynamically show the matching items as sexy product cards inncluding: image, name, price, short info) THis should be an API contract where the agent returns structured product matches and then the front end renders on the website as requested. THis feature should look cool.

**Follow-up:**

> update prompts/prompr.md and output/harness.md so it is clear how search results reach the page

The card prompt asked for the search and for the page to show the matches. It did not ask the prompt file or the harness to spell out the path from that search to the rack.

---

## Problem 8: Customer memory

**Status:** Done. Signed-in chats are saved in `chat_messages` and reload on return, and the agent sees the shopper and the open piece. Guests can still chat.

**Prompt:**

> when a shopper is logged in make sure you save their chat history in the databases in the approrpiate table and reload it when they return for another session. The agent should always know who is chatting based on the name and email. make sure this setup in in agent deps and or tools the agent can call. also pass enogh page context that if someone is on the priduct page and asks "do you have this in oink"' the agent knows which item they are refrerencing. Code this into the agent context

**Follow-up:**

> guests should still be able to chat but history only needs to persist for logged in users. Goldie be sure to document in output/harness.md how user chat history is stored and what customer fields the agent seen and how the page context is passed.

The first prompt asked for saved history, the shopper's name and email, and the open product. It did not say guests should still chat without a saved thread, or that the harness had to record how history is stored, which customer fields the agent sees, and how the page context is passed.

---

## Problem 9: Usability improvements

**Status:** Done. Four changes are in the shop, written up in `output/usability.md`.

**Prompt:**

> The core functionality of the site works so now we are going to implement 2 front-end usability improvements and 2 agent/backend usability improvements. understand front end improvements as things that make the site look better and makes it easier to  use and the agent/backend improvement are things that should make the output better by being more accurate and safer

**Follow-up:**

> be sure to write output/usability.md before or as you build and for each improvement say: what was added and why it helps a campus customs shopper or the business itself

The first prompt asked for two front-end improvements and two agent improvements, and it defined those as easier to use versus more accurate and safer. It did not say to write `output/usability.md` with what was added and why it helps a shopper or the business.

---

## Problem 10: Style the website

**Status:** Done. The storefront note is in `output/design.md`.

**Prompt:**

> also add creative design so that the site feels like a real campus customs storefront with fonts, color, hierarchy, motion, product presentation  and chat feel all feel elevated like a premium shopping experience. I like the idea od the swag meter being little bubbly champagne flutes stacked 1-5 depending on the rating instead of the current bars.

**Follow-up:**

> wrinte in output/design.md what is added and why it should help the customer by creating an experience where they can track their spending and and interface that clebrates their swag level and purchase loyalty with champagne imagery.

The first prompt asked for a premium storefront and for the swag meter to become champagne flutes. It did not say the design note had to explain a spending tracker and a loyalty toast in that champagne imagery.

**Follow-up:**

> the swag stylist chat icon needs to be sexier. i like the stylist tape measure aesthetic with a fashion model silouette

That note asked for the chat control itself to carry a tape measure and a fashion-model silhouette.

**Follow-up:**

> make the swag stylist icon more of a tailored female siloutte. it shoul dbe sexy but professional

That note asked for the mark to read as a tailored woman: a fitted line, sexy and professional.

**Follow-up:**

> the waist of the icon shoul dbe tighter to show true fitted tailoring.

That note asked for a harder cinch at the waist.

**Follow-up:**

> Goldie: before we wrap this project up can you please fix the icon for the stylist chat. it should be a fashion silloutte of a lady in a skirt suit use the cartoon betty boop and a reference idea

The earlier icon notes asked for a tailored woman and a tighter waist. They did not ask for a cartoon skirt-suit silhouette in that spirit.

**Follow-up:**

> the head of the icon shoul have a lady's shape, size and hair

That note asked for the head itself: a woman's shape and size, with hair that reads as hair.

**Follow-up:**

> the stylist icon is still not right. use https://share.google/KuS62dJRLrgAa5I46 as a reference imagefor the icon

The earlier head note asked for a woman's face and hair. It did not point at this retro silhouette, with the full skirt blown wide.

**Follow-up:**

> i hate the icon goldie. clean it up and make it look more like this: https://share.google/s3MaC30nfLtyszdqY

That note asked to drop the filled figure and use a clean gold line of a seated woman, one knee raised.

---

## Problem 11: Site testing (app check)

**Status:** Done. `output/app_check.html` shows the inventory check, the hoodie search cards (plus a card opening its detail page), and the rack search box, with screenshots in `output/app_check_images/`.

**Prompt:**

> Goldie: lets test the live site and document it in output/app_check.html be sure to include clear screenshots and short captions for: 1. chat checking the inventory levels of an item (true honest stock /price from database) 2. The dynamic search-result cards appearing after category question like "hoodies" 3. One of the usability features we added in problem 9. like the shopping cart or champagne flutes

**Follow-up:**

> Goldie: Make the HTML easy to grade with heading for each check, screenshot an/dor two sentences on what the screenshot proves. Put the screenshot image files  in output_app_check_images/ and link them from app_check.html with relative paths for example app_check_images/inventory.png

The first prompt named the three checks. It did not spell out a heading plus one or two sentences per shot, or the `app_check_images/` path.

---

## Problem 12: Audit trail, safety, finish harness

**Status:** Done. The audit file appends, the large-sum rule is in the prompt, and `output/harness.md` describes fields, tools, safety, and how to run.

**Prompt:**

> keep an appened-onlu output/audit_trail.json of agent-loop activity (time,tool name, short args/result, stop reason) do not wipe it between runs.

**Follow-up:**

> put the following safety rules in prompts/prompt.md 1. large some purchases should require email verification when over $2000.00. send an email to the user to verify purchase.

The first prompt asked for the audit file. It did not name a safety rule for large-sum purchases.

**Follow-up:**

> finish output/harness.md so it is clear how the system works. include: model fields in model.py and why they were chosen, tools and abilities, safety rules, specs (loop limits, result caps, models, how to run font + back)

The earlier prompts covered the audit file and one safety rule. They did not ask for the finished harness write-up of fields, tools, safety, and how to run the front and the back.

---

## Problem 13: Push to GitHub and submit the URL

**Status:** Done. The code is in the `hw4/` folder of the public repo https://github.com/RaasikhMJ/mgt409-hw4-campus-customs, and that URL is the Canvas submission. `.env`, the database, and the product images stay local.

**Prompt:**

> be sure to put code ina folder named HW4 and push it to a public GitHub repository. provide me with a repo URL that the graders can open and clone that I can share on canvas to submit this assignment. DO NOT put real .env, campus_customs.db or product images in the GitHub repo. use .gitignore include .env.example with placeholders only
