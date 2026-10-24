# Startup Igniter: 8-minute demo script (two presenters, one listener)

**Listener:** one non-technical person, sitting beside the laptop. Make it a conversation, not a talk.
**Roles:** **A** = works on the project: runs the laptop, types, clicks, and says what they are doing in a few plain words. **B** = explains the project: tells the story, asks the listener questions, and says why each screen matters. Both look at the listener, not at each other.
**Goal:** they understand what it does, believe the answer is checked, and see it run on *their* idea.

## Before they sit down (10 min earlier)

1. **A:** run `dev.cmd`. All four lines must say `[ OK ]`. If the vLLM lines fail, start the servers on the DGX (about 5 min to load).
2. **A:** open `http://localhost:5173` (not `127.0.0.1`) and sign in as the demo user. Zoom to 125%.
3. **A:** pre-run one analysis of the backup idea below and keep it in tab 2. A full run takes several minutes; this is your safety net.
4. **B:** if you can, ask the listener for their own idea the day before; A pre-runs that one too.
5. No real payments in the demo. Show the pricing page only.

**Backup idea (if they have none):**
> An app that lets small kirana shop owners in Tamil Nadu reorder stock by voice in Tamil from nearby wholesalers, with credit tracking.

## Script

### 0:00 - 1:00  Start with them (B)
B: "Have you ever had an idea for a business, or known someone who did?" (Let them answer. Use their words later.)
B: "How would you find out if it was any good? Usually friends say 'great idea!', you do some Googling, and months later you learn the truth. A proper study from a consultant costs ₹50,000 or more."
B: "We built something that gives you that first honest check in a few minutes. A will show you it working while I explain."

### 1:00 - 2:00  Their idea, live (A works, B explains)
B: "What's your idea? One sentence is enough." (Or: "Let's use this one.")
A types or pastes it into the new-idea box and presses **Analyze**. A says: "That's all I type. One sentence."
B: "Behind that button, 13 specialists now read it one after another: market, competitors, legal, funding, and so on. It takes a few minutes, so let's look at one that already finished."
A switches to **tab 2**.

### 2:00 - 4:30  A finished report (A clicks, B explains)
1. **Score and range.** A scrolls to it. B: "A readiness score out of 100, shown as a range, because nobody can know this exactly. Does a range feel more honest to you than one number?"
2. **Verdict.** A points at go / pivot / no-go. B: "It decides, and also says what would change its mind."
3. **Skeptic tab.** A opens it. B: "One specialist's only job is to argue against the idea: worst case, and 'imagine it failed in a year, why?' Would your friends ever tell you that?"
4. **Evidence tab (slow down, this is the point).** A opens a **supported** claim. B: "Every fact is checked against a real web page. It only counts if the exact sentence is on that page. Here it is." Then A opens an **unsupported** claim. B: "No source backs this one, so it says so. It doesn't get to bluff."
5. **Rupees.** A scrolls to a cost or pricing section. B: "Everything is in ₹."

### 4:30 - 5:30  Back to the live run (A)
A switches to tab 1 and says: "Ours is on specialist N of 13." If finished, A opens it and shows the score. If not: "Almost there; the one you saw is the same kind of report." B keeps talking meanwhile; never wait in silence.

### 5:30 - 7:00  Anything you want (A, B)
B: "Click anything, or ask it something." A hands over the laptop or asks the **co-founder chat** the listener's question (e.g. "What's the cheapest way to test this?"). If they are quiet, A asks it for them, and B explains: "It has read your whole report, so its answers are specific."

### 7:00 - 8:00  Close (B)
B: "So: one sentence in, 13 specialists, a skeptic, and a fact-check, in minutes, in rupees. Free gives you 3 tries with a preview; ₹299 unlocks one full report; ₹999 a month is for people running several ideas." (A flashes the pricing page.)
B: "The AI runs on our own college server, so your idea doesn't go to a foreign service." Then B asks: "What would you want it to do that it doesn't?" and A writes down the answer.

## If something breaks

| Problem | A does | B says |
|---|---|---|
| Live run fails or stalls | Stay on tab 2 | "Live AI sometimes needs a moment. Here is the finished one." |
| App down | Open the screenshots taken during setup | "Here's what it looked like when we ran it earlier." |
| Blank page or CORS error | Switch to `localhost:5173` | (keep talking) |
| Upgrade prompt (402) appears | Close it, move on | "That's the paywall working." |

## Likely questions (B answers; A can show the screen)

- **Is it always right?** No. That's why every fact shows its source and unchecked ones are labelled.
- **Why not just ask ChatGPT?** One chatbot answer is unchecked and agrees with you. Ours has 13 roles, an opponent, and a source check.
- **How long does it take?** A few minutes, in the background; you can close the tab.
- **Who sees my idea?** Only your account.
- **Replace a consultant?** No, it replaces the first round: it tells you whether a consultant is worth paying for.

## Rehearsal rules
- Time it twice. If over 8 minutes, cut the chat section.
- Never say "LLM", "vLLM", "pipeline" or "API". Say "the AI", "specialists", "fact-check".
- A does and names the action in a few words; B explains why it matters. If the listener asks something, B answers first, then returns to the script.
