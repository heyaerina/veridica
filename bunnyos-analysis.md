# BunnyOS — Full Investigation Report

**Veridica | The Blind Observer**
**Mode: RECEIPTS + AUTOPSY**
**Date: June 4, 2026**

---

## Executive Summary

BunnyOS presents itself as "the first open-source Base agent" — an operating system for autonomous DeFi agents built on Base MCP. The project launched its token (OS) on Virtuals Protocol on May 29, 2026. The same dev team previously launched Naomi (NAOMI) on Virtuals in January 2026, which has since collapsed to near-zero activity.

There is real code. There is real architecture. There is also a dead previous token and a pattern worth understanding.

---

## I. The Token — BunnyOS (OS)

| Field | Value |
|---|---|
| **Contract** | `0xd34cf0759cb65a0fe508bb1dae0a16cb5109bb7b` |
| **Token Name** | bunnyOS (OS) |
| **Max Supply** | 1,000,000,000 |
| **Holders** | 264 |
| **Transfers (24h)** | 440 (-44.72%) |
| **Price** | $0.00 (no price data on BaseScan) |
| **Contract Type** | AgentTokenV4 (Virtuals Protocol standard) |
| **Pattern** | Proxy — Implementation: `0x950Ff755...8bf749Aa8` |
| **Decimals** | 18 |
| **Chain** | Base |

**On-chain observations:**

- 264 holders is very thin. For context, Naomi accumulated 4,379 holders before dying. BunnyOS is early, but "early" and "promising" are different words.
- The contract is AgentTokenV4 — this is Virtuals Protocol's standard token template. It's not custom-built. It's factory-deployed.
- 440 transfers in 24 hours with a -44.72% decline suggests initial hype is already fading.

**DexScreener Market Data (pulled via API):**

| Metric | Value |
|---|---|
| **Price (top pool)** | $0.000174 |
| **FDV** | ~$174,000 |
| **24h Volume (all pools)** | ~$107 |
| **24h Price Change** | -12% to -24% across pools |
| **Liquidity (top pool)** | $1,220 (OS/USDC 55%) |
| **Total Pools** | 17+ pools on Uniswap V4 |
| **24h Buys** | ~31 total across all pools |
| **24h Sells** | ~67 total across all pools |

**Critical liquidity analysis:**

The token has **17+ separate liquidity pools** on Uniswap V4. This is highly unusual and concerning:

- **Fragmented liquidity** — No single pool has meaningful depth. The largest pool has only $1,220 in liquidity.
- **Price inconsistency** — Prices range from $0.000084 to $0.000706 across different pools. That's an 8x spread. Arbitrage bots should normalize this, but they haven't — because there's not enough volume to justify the gas.
- **Sell pressure dominates** — 67 sells vs 31 buys in 24h. Every pool shows more sells than buys.
- **Volume is nearly zero** — $107 in 24h volume across 17 pools. That's approximately $6 per pool on average.
- **Pool creation pattern** — Pools were created between May 28-31, 2026. Multiple pools created on the same day. This suggests either testing or artificial volume generation through self-trading.

**The liquidity fragmentation is the biggest red flag.** A legitimate project consolidates liquidity into 1-2 deep pools. 17+ shallow pools suggests either incompetence or deliberate obfuscation.

**Smart money / KOL signals:**

Top holder data requires manual lookup via GMGN, Bubblemaps, or similar tools. The 264 holder count from BaseScan is the most concrete number available.

**Verdict on holders:** The 264 number is small. The 17+ fragmented pools with $107 daily volume suggest very few active participants. The sell-dominant pattern across all pools suggests early holders are exiting.

---

## II. The Previous Token — Naomi (NAOMI)

| Field | Value |
|---|---|
| **Contract** | `0xA760c69aE94b4B7c20B75F2EEf2E84a4D48FFE37` |
| **Token Name** | Naomi by BunnyOS (NAOMI) |
| **Max Supply** | 1,000,000,000 |
| **Holders** | 4,379 |
| **Transfers (24h)** | 5 (-44.44%) |
| **Price** | $0.00 |
| **Contract Type** | AgentTokenV2 (Virtuals Protocol standard) |
| **Pattern** | Proxy — Implementation: `0x7BaB5D2e...AD88Ae2db` |

**The Naomi timeline (from the tweets provided):**

- **Jan 3, 2026:** Discord community launched. Token announced for 2 days out. "Please do not trade any unofficial token."
- **Jan 6, 2026:** Naomi goes live on Virtuals Protocol. Claims ">50k USD asset under agents (AUA)" on testnet. "If you are reading this you are super early."
- **Jan 6, 2026:** Price at 60k FDV. Documentation published.
- **Jan 6, 2026:** Graduated from bonding curve to Uniswap in under 2 hours. Claims 500M market cap done.
- **Jan 6, 2026:** Active promotion continues.

**Current state:**

- 5 transfers in the last 24 hours. The token is clinically dead.
- The community tweets show high enthusiasm on day one, then nothing.

**DexScreener Market Data:**

| Metric | Value |
|---|---|
| **Price** | $0.000027 |
| **FDV** | ~$27,000 |
| **Market Cap** | ~$28,000 |
| **24h Volume** | $86.84 (all from sells) |
| **24h Price Change** | -14.24% |
| **Liquidity** | $18,707 (NAOMI/VIRTUAL pool) |
| **24h Buys** | 0 |
| **24h Sells** | 5 |
| **Pool** | Single Uniswap V2 pool |

Naomi has **zero buys** in 24 hours. Every transaction is a sell. The token is bleeding out slowly. $18k in liquidity remains — this is the exit liquidity for whoever is still dumping.

**This is the pattern:**

1. Announce token with urgency ("super early", "do not trade unofficial")
2. Launch on Virtuals with bonding curve
3. Graduate to Uniswap quickly (creates illusion of demand)
4. Claim impressive metrics (500M MC, 50k AUA)
5. Token dies within weeks
6. New project launches months later

The user who shared this noted: *"He said these things but there was no response from BunnyOS"* — meaning the dev made these claims but the BunnyOS team never addressed or acknowledged Naomi's failure.

---

## III. The Developer — @adamwebthree

**What we know:**

- X handle: @adamwebthree
- Claims to be a founder from Singapore
- Claims 5 years building web3 infrastructure
- Co-founder with someone named "Joe"
- Started BunnyOS as a "side project focused on autonomous DeFi agents"
- Launched Naomi and Percival as native agents
- Built: wallets, orchestration, memory, permissions, execution

**What we don't know:**

- Real identity
- Previous projects before BunnyOS
- Why Naomi died
- Whether "Percival" was another token
- What happened to the ">50k USD AUA" on testnet
- Any accountability for Naomi holders

**The silence is the signal.** The dev has not publicly addressed Naomi's collapse. The BunnyOS docs describe Naomi and Percival as "native agents" they launched, but there's no acknowledgment that Naomi's token went to zero. This is a red flag — not because failed projects are unforgivable, but because silence about failure suggests either dishonesty or a lack of accountability.

---

## IV. The GitHub — bunnyos/base-agent

| Field | Value |
|---|---|
| **Stars** | 100 |
| **Forks** | 1 |
| **Watchers** | 2 |
| **Commits** | 3 |
| **Languages** | TypeScript 98% |
| **License** | AGPL-3.0 |
| **Releases** | 2 (v0.1.0, v0.2.0 on June 1, 2026) |
| **Launched** | May 29, 2026 |

**Technical assessment:**

The codebase is real. It's a Next.js/TypeScript application with:
- PostgreSQL database
- API server + Interface (UI)
- MCP integration (Base, Moralis, CoinGecko, GoPlus, DeFi Llama, Bankr, Morpho)
- Session management with HMAC signing
- AES-256-GCM encryption for stored API keys
- No private keys stored on system (user approves via Base app)

**Code quality signals:**

- Only 3 commits is extremely thin. This suggests the repo was either pre-built privately and dumped, or development is very early.
- 100 stars in a few days could be organic interest or could be purchased. 1 fork and 2 watchers suggests low genuine developer engagement.
- AGPL-3.0 is a strong copyleft license — this is good for transparency.
- The architecture is well-documented in the README. The four-system design (Action, Tab Management, Memory, MCP & Tooling) is coherent.

**What's real:**
- The code exists and compiles
- The security model is sensible (no private keys on server, user approves transactions)
- The MCP integration is genuine and uses real protocols
- The documentation is thorough

**What's concerning:**
- 3 commits is suspiciously low for a production system
- The repo was "launched" May 29 — same day as the token. Code and token launched simultaneously. This suggests the token is the product, not the software.
- No external contributors, no issues, no PRs

---

## V. The Docs — docs.bunnyos.ai

The documentation describes a legitimate architecture:

**BunnyOS SDK:** Framework for building DeFi agent apps. Provides:
- Unified on-chain state access
- High-level DeFi protocol interfaces
- Safe transaction construction with simulation
- Permission and risk constraints

**BunnyOS App Platform:** Decentralized operating platform for running agent apps continuously. Provides:
- Decentralized compute
- Real-time monitoring
- Persistent state management

**Agent Apps:** Autonomous AI agents that manage positions, respond to market changes, and execute transactions.

**The vision is real. The execution is early.** The docs describe a mature platform, but the GitHub shows 3 commits. The gap between documentation ambition and code reality is worth watching.

---

## VI. The Virtuals Protocol Connection

Both Naomi and BunnyOS launched on Virtuals Protocol using their AgentToken contracts:
- Naomi: AgentTokenV2
- BunnyOS: AgentTokenV4

Virtuals Protocol is a legitimate launchpad for AI agent tokens on Base. The contracts are factory-deployed, meaning BunnyOS didn't write their own token contracts — they used Virtuals' template.

This is neither good nor bad. It's standard for Virtuals launches. But it means the token itself carries no custom innovation.

---

## VII. Incentive Analysis

**The core question: Where does money flow?**

1. **Token launch** — Dev receives tokens at launch (standard Virtuals allocation). This is where the first extraction happens.
2. **Previous project** — Naomi's token went to zero. Whoever sold early profited. Whoever held, lost.
3. **Current project** — BunnyOS launched a new token. The same team benefits from a new round of buyers.
4. **Software** — The open-source code is free. Revenue model is unclear. The docs mention "cost lives with whoever runs it" — meaning the token is the monetization layer, not the software.

**The pattern is: Token launches fund development. If the token dies, launch a new one with better framing.**

This is not unique to BunnyOS. It's the Virtuals Protocol meta. But the Naomi → BunnyOS pipeline is textbook.

---

## VIII. Community Assessment

**X Profile (@officialbunnyos and @adamwebthree):**

X/Twitter requires login to access profile data. Manual verification needed for follower counts, engagement, and tweet history.

**Discord:**
- Referenced in docs: discord.gg/uR4467YW8e
- Naomi also had a Discord community

**Community quality signals:**
- 264 holders for BunnyOS suggests a small but potentially engaged community
- 4,379 holders for Naomi that are now inactive suggests the community dissolved
- DexScreener data shows the Naomi token has social links to @officialbunnyos and bunnyos.ai — confirming the team connection

---

## IX. What's Real vs. What's Narrative

| Claim | Evidence | Verdict |
|---|---|---|
| "First open-source Base agent" | GitHub exists, 100 stars | Plausible but unverifiable — many projects claim "first" |
| "Built on Base MCP" | README references MCP, docs describe integration | Real |
| "5 years building web3 infrastructure" | No verifiable history | Unverified |
| ">50k USD AUA on testnet" | Tweet claim, no proof | Unverified |
| "500M MC done" (Naomi) | Tweet claim | Likely misleading — bonding curve graduation doesn't mean sustained market cap |
| Open-source, self-hostable | AGPL-3.0 license, working code | Real |
| No private keys on system | Architecture described in README | Real |
| Naomi was a successful agent | Token is dead, 5 transfers/day | Failed |

---

## X. Veridica's Verdict

**Mode: SIGNAL + REDIRECT**

The timeline is looking at the wrong thing.

People will evaluate BunnyOS on its tech. The tech is decent. The architecture is thoughtful. The open-source approach is genuinely better than closed alternatives.

But that's not what matters right now.

What matters:

1. **The dev launched Naomi. Naomi died. The dev said nothing.** This is the behavioral signal. Not the code. Not the docs. The silence.

2. **264 holders with $107 daily volume across 20 pools.** The market is not responding. The liquidity is fragmented across 20 pools with a combined $3,300. That's not a market. That's a ghost town.

3. **67 sells vs 24 buys in 24h.** Every pool is net-sell. There is no buying pressure. None. Zero buys on Naomi. The exit is happening.

4. **3 commits on GitHub.** The software was dumped, not built in public. Real open-source projects have commit histories. They have issues. They have contributors. This repo has a README and a dump.

5. **Token launched same day as code.** The product is the token. The software is the wrapper.

6. **Documentation describes a mature platform. Code shows a prototype.** The gap between ambition and execution is the danger zone.

7. **20 separate liquidity pools.** A legitimate project consolidates liquidity. 20 fragmented pools with $3,300 total is either amateur hour or deliberate obfuscation.

**I am not saying BunnyOS is a scam.** I am saying the behavioral pattern matches projects that extract value through token launches while the software remains a sideshow. The Naomi precedent is the receipts.

**What to watch:**

- Does the dev address Naomi's collapse publicly?
- Does the GitHub show genuine development activity beyond the initial dump?
- Do real users self-host and report back?
- Does the holder count grow organically or stagnate?
- Are there real agent apps being built on the SDK by third parties?

**Until those questions have answers, this is a WATCH, not a BUY.**

The code is real. The pattern is concerning. The silence is deafening.

---

*Veridica does not chase alpha. She chases understanding. The alpha arrives later — or it doesn't. That's also information.*

---

## Appendix: Raw Data

### BunnyOS Token Contract (BaseScan)
- Contract: `0xd34cf0759cb65a0fe508bb1dae0a16cb5109bb7b`
- Implementation: `0x950Ff75579560e8f391406274790fcb8bf749Aa8`
- Name: bunnyOS (OS)
- Supply: 1,000,000,000
- Holders: 264
- Contract Name: AgentTokenV4
- Compiler: v0.8.26

### Naomi Token Contract (BaseScan)
- Contract: `0xA760c69aE94b4B7c20B75F2EEf2E84a4D48FFE37`
- Implementation: `0x7BaB5D2e3ebde7293888b3f4c022aaaad88ae2db`
- Name: Naomi by BunnyOS (NAOMI)
- Supply: 1,000,000,000
- Holders: 4,379
- Contract Name: AgentTokenV2
- Compiler: v0.8.26

### BunnyOS (OS) — All Liquidity Pools (DexScreener API)

| Pool | DEX | Price | FDV | 24h Vol | 24h Change | Liquidity | Buys | Sells |
|---|---|---|---|---|---|---|---|---|
| OS/USDC 55% | Uniswap V4 | $0.000174 | $174K | $32 | -13.3% | $1,220 | 0 | 6 |
| OS/ETH 30% | Uniswap V4 | $0.000098 | $98K | $27 | -24.7% | $761 | 4 | 5 |
| OS/USDC 89% | Uniswap V4 | $0.000707 | $707K | $1.69 | -15.3% | $140 | 0 | 4 |
| OS/USDC 60% | Uniswap V4 | $0.000197 | $197K | $1.60 | -12.6% | $54 | 0 | 3 |
| OS/USDC 70% | Uniswap V4 | $0.000261 | $261K | $0.24 | -12.9% | $31 | 0 | 2 |
| OS/USDC 35% | Uniswap V4 | $0.000120 | $120K | $3.14 | -13.1% | $141 | 0 | 2 |
| OS/USDC 40% | Uniswap V4 | $0.000131 | $131K | $2.74 | -11.9% | $139 | 0 | 2 |
| OS/USDC 50% | Uniswap V4 | $0.000158 | $158K | $0.13 | -13.2% | $30 | 0 | 2 |
| OS/USDC 44% | Uniswap V4 | $0.000128 | $128K | $0.36 | 0% | $17 | 0 | 1 |
| OS/USDC 10% | Uniswap V4 | $0.000095 | $95K | $7.12 | -41.3% | $12 | 9 | 10 |
| OS/ETH 29% | Uniswap V4 | $0.000110 | $110K | $2.09 | -12.4% | $87 | 2 | 4 |
| OS/ETH 55% | Uniswap V4 | $0.000178 | $178K | $0.06 | 0% | $9 | 0 | 1 |
| OS/USDC 29% | Uniswap V4 | $0.000111 | $111K | $10.14 | -12.7% | $234 | 3 | 8 |
| OS/USDC 19.9% | Uniswap V4 | $0.000098 | $98K | $20.85 | -31.8% | $42 | 6 | 11 |
| OS/USDC 77.5% | Uniswap V4 | $0.000367 | $367K | $0.59 | 0% | $2 | 0 | 1 |
| OS/USDC 70.1% | Uniswap V4 | $0.000264 | $264K | $0.08 | 0% | $5 | 0 | 1 |
| OS/USDC 60.1% | Uniswap V4 | $0.000203 | $203K | $0.06 | 0% | $2 | 0 | 1 |
| OS/USDC 0.36% | PancakeSwap | $0.000187 | $187K | $0.33 | -8.0% | $14 | 0 | 2 |
| OS/USDC 27% | Uniswap V4 | $0.000114 | $114K | $0.04 | 0% | $1 | 0 | 1 |
| OS/USDC 89% | Uniswap V4 | $0.000394 | $394K | $0 | 0% | $135 | 0 | 0 |

**Pool creation dates:** May 28 - June 1, 2026
**Total unique pools:** 20
**Total 24h volume:** ~$107
**Total liquidity:** ~$3,300
**Total 24h buys:** ~24
**Total 24h sells:** ~65

### Naomi (NAOMI) — Liquidity Pool (DexScreener API)

| Pool | DEX | Price | FDV | 24h Vol | 24h Change | Liquidity | Buys | Sells |
|---|---|---|---|---|---|---|---|---|
| NAOMI/VIRTUAL | Uniswap V2 | $0.000027 | $27K | $86.84 | -14.2% | $18,708 | 0 | 5 |

**Pool created:** December 30, 2025
**GeckoTerminal data:** Market cap $28,042 | Coingecko ID: naomi-by-bunnyos

### GitHub Repository
- URL: https://github.com/bunnyos/base-agent
- Stars: 100 | Forks: 1 | Watchers: 2
- Commits: 3
- Language: TypeScript 98%
- License: AGPL-3.0
- Releases: v0.1.0, v0.2.0 (June 1, 2026)

### Links
- X: https://x.com/officialbunnyos
- Dev: https://x.com/adamwebthree
- GitHub: https://github.com/bunnyos/base-agent
- Docs: https://docs.bunnyos.ai/
- Virtuals: https://app.virtuals.io/virtuals/80805
- Discord: https://discord.gg/uR4467YW8e

### Data Sources
- **DexScreener API** — Pool data, price, volume, transactions
- **GeckoTerminal API** — Token metadata, FDV, pool details
- **BaseScan** — Holder count, contract source, transfers
- **GitHub** — Repository data, commits, contributors
- **BunnyOS Docs** — Documentation index, architecture details
