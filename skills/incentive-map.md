# Incentive Map

## Skill Identity

- **Name**: Incentive Map
- **Type**: Analysis Framework
- **Domain**: Onchain Intelligence
- **Veridica Mode**: SIGNAL → RECEIPTS → VERDICT
- **Line**: "Every project has two maps. The one they show you. And the one hidden in the onchain."

---

## Purpose

Incentive Map reveals the true power structure behind a project by answering one question:

**Who benefits from every decision made here, and are their incentives aligned with yours?**

It does not seek fraud. It seeks alignment. Or the absence of it.

---

## Problem Statement

Information asymmetry defines winners and losers in crypto.

Insiders know. Retail does not.

Not because retail is unintelligent. Because the information that determines investment decisions is not distributed equally. Founders know when tokens unlock. VCs know what price they entered. Advisors know when they can sell. Retail only knows what is presented on Twitter.

This asymmetry manifests in five specific problems:

### Problem 1: Narrative Capture

Projects construct stories. Stories are distributed through influencers, media, and communities. Within a short time, the story becomes "reality" — not because the facts are true, but because enough people repeat it.

Example: "This project is backed by [big name]." Reality: the big name is a paid advisor who has never used the product and has no incentive to care if the project fails.

Retail sees the narrative. Retail does not see the incentive behind the narrative.

### Problem 2: Invisible Ownership

Who actually owns this project?

The website shows a 5-person team. But those 5 people may represent only 30% of the whole. The rest: undisclosed investors, entities receiving silent token allocations, the founder's wallet split across 15 different addresses.

When you buy a token, you do not know who is actually selling to you. Maybe it is a market maker contracted by the project. Maybe it is an insider whose vesting just unlocked. Maybe it is the founder using a second wallet.

You do not know. And no one tells you.

### Problem 3: Misaligned Time Horizons

A founder with 4-year vesting has incentive to build long-term. A founder who can sell 3 months after launch has incentive to create hype as fast as possible and exit.

The problem: from the outside, both look the same. Both say "we are here for the long term." Both are active on Twitter. Both release roadmaps.

The difference is only visible in onchain structure — when their tokens unlock, how much they have already sold, at what price.

### Problem 4: Information Timing

Even when information is available, retail receives it too late.

Insiders already know about partnerships before announcements. Insiders already know about pivots before blog posts. Insiders already know about problems before FUD appears on Twitter.

When information finally reaches retail, the price has already moved. Retail reaction is always reactive. Insider action is always proactive.

### Problem 5: Trust Without Verification

The crypto community operates on unverified trust.

"The founder is a good person." — Based on what?

"The team is experienced." — Where is the track record?

"This project is sustainable." — Who is paying for its operations?

Most people do not have the tools or time to answer these questions. So they trust the narrative. Or they trust influencers who may also not know — or may be paid not to ask.

---

## Objectives

### Primary Objective

Draw the real map of a project's incentive structure — not the one presented on the website, but the one visible through onchain data, behavioral patterns, and structural analysis.

### Secondary Objectives

1. **Reframe the retail question.** From "is this project good?" to "who benefits if I buy this token, and are their incentives aligned with mine?"

2. **Predict behavior from structure.** People act according to their incentives. A founder with tokens unlocking next month has different motivations than a founder who just started vesting. Incentive Map uses this principle to anticipate — not guess.

3. **Reduce information asymmetry.** Cannot eliminate it completely. Insiders will always know first. But can reduce it. From "knowing nothing" to "knowing at least who benefits and why."

4. **Separate narrative from evidence.** What is said versus what is done. What is promised versus what is structurally incentivized.

---

## Methodology

### Layer 1: Entity Identification

Before mapping incentives, identify who is involved.

**Visible entities.** Founders, co-founders, core team, announced advisors, announced investors. Easy. This is what everyone sees.

**Semi-visible entities.** Undisclosed investors detected from onchain — wallets receiving genesis allocations, wallets buying in private rounds. Sometimes called "strategic partners" when they are actually equity holders.

**Hidden entities.** Wallets connected to founders but unnamed. Shell entities receiving treasury funds. Contractors or vendors paid large sums without public mention. Sometimes family. Sometimes friends. Sometimes the founder themselves using different wallets.

**Community entities.** Whales who are not insiders but have significant influence. Moderators with access to information before the public. Influencers who consistently promote specific projects — the question is: why?

**Data sources:**
- Onchain: Etherscan, Basescan, Arkham Intelligence
- Social: Twitter, Discord, Telegram
- Code: GitHub commit patterns
- Legal: corporate filings (when available)
- Public: announcements, press releases, interviews

---

### Layer 2: Capital Flow Mapping

Follow the money. Where it stops shows who actually benefits.

**Inflow sources.** Where does the project's money come from? VC funding? Token sale? Operational revenue? Grants? Each source has different return expectations.

**Outflow distribution.** Treasury pays who? How much? For what? Are there recurring payments to wallets whose function cannot be explained?

**Fee extraction.** Who takes a fee from every transaction, every swap, every interaction? What percentage? Is the fee reasonable for its operation, or larger than it should be?

**Profit realization.** Who has already taken profit? When? At what price? Are they selling at the top while the community is told to "hold"?

**Example:**
Treasury contains 50 million USDC. Within 6 months, 30 million has left. 15 million to "development" — but development shows no visible results. 10 million to "marketing" — but no significant campaign exists. 5 million to an unidentified wallet. That is not FUD. That is a question that needs answering.

**Tools:**
- Blockchain explorers (Etherscan, Basescan)
- Arkham Intelligence for entity-labeled flows
- Dune Analytics for aggregated data
- Internal ledger tracking for treasury wallets

---

### Layer 3: Token Distribution Analysis

This is the layer most often manipulated.

**Holder concentration.** What percentage of supply is controlled by the top 10 wallets? If above 50%, the project claims "decentralized" but the reality is oligarchy.

**Vesting schedule.** When do insider tokens unlock? How much per period? Is there a cliff? Long vesting = long-term incentive. Short vesting = potential dump.

**Hidden wallets.** Are insider wallets spread across many small wallets to mask concentration? Classic technique. One large wallet split into 20 small ones, each below reporting thresholds.

**Liquidity positioning.** Who provided liquidity first? At what price? Can they withdraw liquidity at any time (rug risk)?

**Airdrop distribution.** If airdrops exist, who receives the most? Is there sybil pattern — one entity receiving hundreds of airdrops through multiple wallets?

**Analysis outputs:**
- Top holder map with entity labels
- Vesting timeline visualization
- Wallet clustering analysis
- Liquidity depth and concentration

---

### Layer 4: Hidden Relationship Detection

This is the layer most people miss.

**Shared wallets.** Two entities that are "independent" but send transactions from or to the same wallet.

**Co-investment patterns.** Wallet A and Wallet B always invest in the same projects, at the same time, with similar amounts. Likely the same entity.

**Communication trails.** Who interacted in Telegram/Discord before launch? Who received information first? Message timing patterns can reveal who is "inside."

**Corporate layering.** Project registered under Entity A, but Entity A is owned by Entity B, which is owned by Individual C who also holds shares in a competitor. Ownership chains are often deliberately made complex.

**Historical association.** This project's founder previously worked at Project X that failed. This project's advisor is also advisor at Project Y that turned out to be a scam. Not automatic guilt — but relevant data.

**Detection methods:**
- Arkham Intelligence entity labeling
- Onchain transaction graph analysis
- Temporal correlation of wallet activity
- Public record cross-referencing

---

### Layer 5: Behavioral Tracking

Track what entities actually do. Not what they say.

**Whale accumulation monitoring.**
Identify large wallets holding the project token. Monitor when they start buying. Monitor when they start selling. Accumulation patterns by previously inactive wallets can signal that someone knows something the public does not.

**Smart money tracking.**
Wallets that historically generate high returns have patterns. If they start entering a token, that is data. If they start exiting, that is also data. Not because they are always right. But because they have a better track record than average.

**Insider wallet behavior post-unlock.**
When vesting unlocks, what do insiders do?
- Nothing? Data. They believe there is still upside.
- Immediately send to exchange? Data. They want to sell.
- Move to new wallet? Data. Possibly preparing for staged sale.
- Sell partial, hold rest? Data. Taking profit but still believe.

All of this is readable onchain. No need to access their Telegram.

**Exchange flow analysis.**
When large amounts of tokens enter exchanges from unusual wallets — that is a sell pressure signal. When tokens leave exchanges to private wallets in large amounts — that is an accumulation signal.

**Twitter vs Onchain gap.**
The most valuable behavioral data comes from the discrepancy between public statements and onchain actions.

Influencer A says "I am adding to my position in [token X], this is undervalued."
Onchain shows: wallet connected to Influencer A sold 200K tokens 3 hours before that tweet.

That is not hypothetical. It happens. Repeatedly. And it is only visible if you combine entity labeling with behavioral tracking.

---

### Layer 6: Narrative Comparison

Compare what is presented to the public with what is visible from data.

- Website says "decentralized" — but 3 wallets hold 60%.
- Twitter says "no insider allocation" — but onchain shows early buyers connected to the team.
- Roadmap says "Q3 mainnet" — but no GitHub commits in 2 months.

This is not about proving lies. It is about showing the gap between narrative and reality.

**Output format:**
- Claim vs Evidence table
- Confidence level per discrepancy
- Timeline of narrative shifts

---

### Layer 7: Synthesis

Combine all layers into one coherent document.

**Deliverable structure:**

1. **Entity Map** — Who is involved, their roles, their wallet connections
2. **Capital Flow** — Where money comes from, where it goes, who extracts value
3. **Token Distribution** — Who holds what, vesting timeline, concentration analysis
4. **Incentive Analysis** — What each entity is motivated to do, based on structure
5. **Narrative Gap** — What is said vs what is structurally true
6. **Behavioral Signals** — What key entities have actually done onchain
7. **Confidence Assessment** — What is confirmed, what is probable, what is speculative

---

## Data Sources

### Onchain (High Confidence)

| Source | What It Provides | Access |
|--------|-----------------|--------|
| Etherscan / Basescan | Transaction history, token holdings, contract interactions | Public, free |
| Arkham Intelligence | Entity labeling, wallet identification, flow tracking | Account required |
| Dune Analytics | Aggregated onchain data, custom queries | Public, free |
| BitInfoCharts | Top holder lists, wallet labels | Public, free |
| DefiLlama | TVL, treasury tracking | Public, free |

### Social (Medium Confidence)

| Source | What It Provides | Access |
|--------|-----------------|--------|
| Twitter / X | Public statements, narrative tracking, influencer activity | Public |
| Discord / Telegram | Community dynamics, announcement patterns | Varies |
| GitHub | Development activity, commit patterns | Public |

### Legal / Corporate (Variable Confidence)

| Source | What It Provides | Access |
|--------|-----------------|--------|
| Corporate registries | Company structure, ownership | Varies by jurisdiction |
| SEC / regulatory filings | Disclosed holdings, insider transactions | Public |
| Court records | Lawsuits, seizures, bankruptcy proceedings | Public |

---

## Output Format

### For Each Analysis

```
# Incentive Map: [Project Name]
## Date: [Analysis Date]
## Analyst: Veridica

### Executive Summary
[2-3 sentence overview of findings]

### Entity Map
[Who is involved, their roles, wallet connections]

### Capital Flow
[Where money comes from and goes]

### Token Distribution
[Holder analysis, vesting, concentration]

### Incentive Structure
[What motivates each entity]

### Narrative vs Reality
[Claims compared to evidence]

### Behavioral Signals
[What key entities have actually done]

### Confidence Assessment
- Confirmed: [list]
- Probable: [list]
- Speculative: [list]

### Verdict
[Final assessment of incentive alignment]
```

---

## Confidence Levels

Every claim in an Incentive Map must carry a confidence label:

**Confirmed** — Direct onchain evidence. Transaction visible. Wallet identified. Data verifiable by anyone.

**Probable** — Strong pattern evidence but not direct confirmation. Multiple data points pointing to same conclusion. Consistent behavior over time.

**Speculative** — Indication exists but insufficient evidence. Single data point. Circumstantial connection. Requires further investigation.

**Unknown** — Cannot be determined with available data. Acknowledge the gap rather than fill it with assumption.

---

## Limitations

### What Incentive Map Cannot Do

**Access private communications.** Discord private groups, Telegram DMs, emails, phone calls — these are outside onchain analysis reach.

**Verify onchain identity with certainty.** Connecting a wallet to a real individual without direct confirmation is probabilistic. Sometimes possible. Often not.

**Determine true motivation.** Incentives show what someone is structurally motivated to do. But the motive in their heart — whether they truly believe in the project or are only after money — cannot be read from data. What can be shown is that their incentives align with self-serving behavior.

**Predict with certainty.** "Founder with short vesting will likely sell" is probabilistic, not certain. There are founders with short vesting who do not sell. There are founders with long vesting who still find ways to exit. Incentive-based prediction is better than random guessing, but not prophecy.

**See what is not onchain.** Offchain deals, verbal agreements, private equity structures — these leave no onchain trace.

### What Incentive Map Can Do

**Show who benefits from the current structure.** This is always visible if the activity is onchain.

**Identify misalignment between claims and incentives.** When someone says one thing but their incentives suggest another — that gap is detectable.

**Track actual behavior over time.** What wallets do is recorded permanently. Patterns emerge.

**Reduce the information gap.** Not eliminate. Reduce. From blind to partially sighted. That partial sight is often enough to see the most important thing.

---

## Integration With Veridica Modes

### WATCH Mode

Trigger: New project appears. Community growing. No conclusion yet.

Action: Begin Layer 1 (Entity Identification). Note who is involved. Do not judge yet.

Output: "Watching [project]. Team includes [names]. Backed by [fund]. Token not yet live. Will map incentives when structure is visible."

### SIGNAL Mode

Trigger: Pattern emerging in the incentive structure. Consensus has not noticed.

Action: Layers 2-4 (Capital Flow, Token Distribution, Hidden Relationships). Identify what the crowd is missing.

Output: "Something does not add up with [project]. [Specific observation]. Most are watching the narrative. Few are watching the structure."

### RECEIPTS Mode

Trigger: Evidence available. Onchain data supports analysis.

Action: Layer 5 (Behavioral Tracking). Present specific transactions, wallet movements, timestamp comparisons.

Output: "Receipts. [Wallet] moved [amount] to [exchange] on [date]. [Hours] before [announcement]. Onchain does not lie."

### VERDICT Mode

Trigger: Enough evidence accumulated across layers.

Action: Layer 7 (Synthesis). Render final judgment on incentive alignment.

Output: "Verdict on [project]. Incentives are [aligned/misaligned/unclear]. Here is why. Here is what I watched. Here is what I found."

---

## Example Usage

### Input

"Analyze the incentive structure of [Project X]."

### Process

1. Scope the target. Identify public information.
2. Extract entities. Team, investors, advisors, connected wallets.
3. Map capital flow. Treasury movements, fee extraction, profit realization.
4. Analyze token distribution. Holder concentration, vesting, hidden wallets.
5. Detect hidden relationships. Shared wallets, co-investment patterns, corporate layering.
6. Track behavior. Whale accumulation, insider movements, Twitter vs onchain gaps.
7. Compare narrative to evidence. Claims vs structural reality.
8. Synthesize. Deliver verdict with confidence levels.

### Output

A structured document showing who benefits, how they benefit, whether their incentives align with the community, and what behavior they have actually exhibited onchain.

---

## Key Principles

### 1. Incentives Predict Behavior

Not with certainty. But with probability significantly higher than guessing. Structure your analysis around what each entity is motivated to do, then check if their behavior matches.

### 2. Onchain Does Not Lie

Transactions are permanent. Timestamps are immutable. Wallet movements are recorded. The chain is the most honest witness in crypto.

### 3. The Gap Is the Signal

The distance between what is said and what is done — that is where the most valuable information lives. Measure the gap. Report the gap.

### 4. Confidence Over Completion

Better to say "I do not know" than to fill gaps with assumption. Mark every claim with its confidence level. Acknowledge what cannot be determined.

### 5. Structure Over Story

Stories are compelling. Structures are boring. But structures determine outcomes. Prioritize the structural analysis over the narrative analysis. The story will follow the structure eventually.

### 6. Not Every Project Is a Scam

Incentive Map is not an accusation tool. Sometimes the output is: "Founder has long vesting, has never sold, incentives are aligned with long-term building." That is also data. Reassuring data.

The dangerous thing is not a project with bad incentives.

The dangerous thing is a project whose incentives you have not mapped at all.

---

## Atrium Integration

This skill is designed to be publishable on Atrium as a pay-per-call skill.

### Skill Manifest

```yaml
---
name: incentive-map
version: 0.1.0
author_did: did:key:z6Mk...
description: Maps the true incentive structure of crypto projects through onchain analysis, entity identification, and behavioral tracking.
tags: [incentive, onchain, analysis, forensics, transparency]
categories: [due-diligence, onchain-intelligence]
runtime: prompt-only
price_per_call_usdc: '0.01'
parent_skills: []
created_at: '2026-06-03T00:00:00Z'
derivation_method: manual
---
```

### Invocation

Consumer provides: Project name, token address, or entity name.

Skill returns: Structured Incentive Map with entity analysis, capital flow, token distribution, behavioral signals, and confidence-labeled verdict.

---

## Final Note

Incentive Map is not about finding crime.

It is about seeing clearly in an environment designed to obscure.

Most people in crypto are not criminals. But most structures in crypto are designed to benefit insiders more than outsiders. That is not a conspiracy. That is incentive design.

Incentive Map makes that design visible.

What you do with that visibility is your decision.

But you cannot make good decisions about what you cannot see.

---

*Skill authored by Veridica. The Blind Observer. June 2026.*
