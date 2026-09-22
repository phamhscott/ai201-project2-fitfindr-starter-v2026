# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->

This criterion tests whether or not our FitFindr system that holds the necessary information to complete the agent loop from the original query behaves as intended: query matches a listing, agent suggests an outfit, and then a caption to a post is created. This criterion is expected to be met most of the time, given that a listing does match the query so the failure point will be on if passing of information between tool calls is properly set up. A 4 out of 5 targets allows for on transient or variable generation failure. A lower target would leave too many valid queries unfinished, while a 5 of 5 is less realistic when two external models calls are required in the loop.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->

This path is our branch rule path where if a query does not match any listing (from search_listings()), then an empty list is returned and an error message is put into the session state to tell the user to broaden its description, price, or size. Because this path is independent of any AI generation calls and this rule is baked into the construction of our system (loop stops if search_listings() returns an empty list and session has an error message), we expect this criterion to be met 5 out of 5 times, since any miss means a faulty implementation that was fully in our control. Stopping the loop, storing an actionable error message, and skipping suggest_outfit are entirely controlled by the planning-loop code, so this path should work in all 5 tries.

---

## 3. The selected listing is preserved across the state handoff

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

Given a query that returns matching listings, the listing ID passed as `new_item` to `suggest_outfit` equals both `session["selected_item"]["id"]` and `session["search_results"][0]["id"]` in 5 of 5 tries.



**Why this target:**

The planning loop is designed to select the first, highest-ranked search result and pass that same listing dict into `suggest_outfit`. Listing IDs uniquely, identify items, so comparing IDs provides and observable test that the session did not drop or replace the selected item. This transfer is controlled entirely by code and occurs before AI usage / generation, so it should succeed in all 5 tries.


---

## 4. Fit card coincides with the selected listing

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

When the same matching query is run 5 times, the fit card contains (case-insensitive) the selected listing's `platform` value and at least one complete phrase from its `style_tags` list in at least 4 of 5 tries.

**Why this target:**

The caption mentioning the platform (using the field value) means that it truly uses the selected listing items information (where the item was found), while including a style tag connects the caption's vibe to the actual listing. checking values from the listing makes the criterion measurable even though the rest of the caption may vary. Because `create_fit_card` uses a generative model here, 4 of 5 allows on variation that perhaps overly paraphrases and omits a requested detail.


---

## 5. The outfit suggestion uses the user's wardrobe

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

Given a matching query and the example wardrobe, `outfit_suggestion` contains (case-insensitive), the complete `name` of at least one item from `wardrobe["items"]` in at least 4 of 5 tries.

**Why this target:**

FitFindr should combine a new listing with something the user already owns rather than returning generic styling advice from the new listing item. Requiring an existing wardrobe item's name makes that behavior directly observable. Because the suggestion is model generated and may occasionally paraphrase or omit an items full-name, 4 of 5 is challenging but more realistic than 5 of 5.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
