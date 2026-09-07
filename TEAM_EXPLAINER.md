# SIH26146 — Simple Team Guide & Project Explainer
**Project**: AI-Powered Bitcoin Transaction Monitoring & Analysis System  
**Agency**: National Technical Research Organisation (NTRO) • Smart India Hackathon 2026  
**Purpose of this Guide**: A simple, jargon-free explainer for every teammate to understand **how Bitcoin works**, **how our project catches criminals**, and **how to explain it to anyone in 2 minutes**.

---

## Table of Contents
1. [Part 1: How Bitcoin Actually Works (Simple Breakdown)](#part-1-how-bitcoin-actually-works-simple-breakdown)
   - [The Piggy Bank (UTXO) Model](#1-the-piggy-bank-utxo-model)
   - [How a Transaction Happens](#2-how-a-transaction-travels)
   - [The Big Myth: Is Bitcoin Anonymous?](#3-the-big-myth-is-bitcoin-anonymous)
   - [The 3 Tricks Criminals Use to Hide Money](#4-the-3-tricks-criminals-use-to-hide-money)
2. [Part 2: How Our Project Works (The Secret Sauce)](#part-2-how-our-project-works-the-secret-sauce)
   - [The Core Idea: What Was Missing?](#1-the-core-idea-what-was-missing)
   - [The 7 Steps Our System Takes](#2-the-7-step-pipeline-explained-simply)
   - [The 3 AI Detectives](#3-the-3-ai-detectives-our-ml-ensemble)
   - [Why SHAP Matters (Translating AI for Courts)](#4-why-shap-matters-translating-ai-for-courts)
3. [Part 3: 2-Minute Pitch & Teammate Cheatsheet](#part-3-2-minute-pitch--teammate-cheatsheet)
   - [The 30-Second Elevator Pitch](#the-30-second-pitch)
   - [How to Answer Judge Questions (Cheat Sheet)](#how-to-answer-judge-questions)
   - [How to Run the Project on Your Laptop](#how-to-run-the-project)

---

# Part 1: How Bitcoin Actually Works (Simple Breakdown)

### 1. The Piggy Bank (UTXO) Model
Most people think Bitcoin works like a bank account: you have an account with ₹500, you spend ₹100, and your balance becomes ₹400.  
**Bitcoin does NOT work like that.**

Bitcoin uses something called **UTXOs (Unspent Transaction Outputs)**. Think of them like **cash paper notes** in your wallet:
- Imagine you only have a **₹500 note**.
- You want to buy a ₹100 coffee.
- You cannot cut the ₹500 note into pieces. You must give the whole ₹500 note to the cashier.
- The cashier takes the ₹500 note, keeps ₹100, and hands you back a **₹400 note as change**.

In Bitcoin:
- Every transaction consumes old "notes" (inputs) and produces new "notes" (outputs).
- One output goes to the person you are paying.
- The other output comes back to you as **change** (usually sent to a brand new address that your wallet generates automatically).

```
[ Your Wallet: ₹500 Note ]  ---> [ Transaction ] ---> [ Coffee Shop: ₹100 Note ]
                                                ---> [ Your New Change Wallet: ₹400 Note ]
```

---

### 2. How a Transaction Travels
When you click "Send" on a Bitcoin wallet:
1. **Creation**: Your wallet creates a cryptographic message: *"I am spending Note A to create Note B for Alice and Note C for my change."* It signs this with your private key.
2. **Broadcast (Network Layer)**: Your phone/laptop connects to the nearest Bitcoin nodes over the internet (TCP/IP) and says: *"Hey, here is my new transaction!"*
3. **P2P Gossip**: That node checks if your signature is valid and tells 8 other nodes. Those nodes tell 8 more. Within seconds, every computer running Bitcoin around the world knows about it.
4. **Mempool (Waiting Room)**: The transaction waits in a queue called the *Mempool* (Memory Pool).
5. **Mining (Settlement)**: Miners bundle transactions from the Mempool into a block, solve a mathematical puzzle, and add it to the blockchain ledger permanently.

---

### 3. The Big Myth: Is Bitcoin Anonymous?
**No. Bitcoin is pseudonymous, NOT anonymous.**
- **The Good News for Criminals**: Your name, PAN card, or email address is not written anywhere on the blockchain. Only random-looking strings like `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` or `bc1qf44p...` appear.
- **The Bad News for Criminals**: Every single transaction since January 3, 2009 is public, permanent, and visible to anyone in the world. 

If a criminal does something wrong, their wallet address is frozen in the public ledger forever. To get real cash (rupees, dollars) out of Bitcoin, they have to use an exchange (where KYC is required) or an exit counterparty.

So how do criminals try to escape? That brings us to their laundering tricks.

---

### 4. The 3 Tricks Criminals Use to Hide Money

```
TRICK 1: PEEL CHAIN (The Salami Slicer)
[ 100 BTC ] ---> [ 95 BTC ] ---> [ 90 BTC ] ---> [ 85 BTC ] ---> ...
      |               |               |               |
   (5 BTC peel)    (5 BTC peel)    (5 BTC peel)    (5 BTC peel)
   (To Cash Exit)  (To Cash Exit)  (To Cash Exit)  (To Cash Exit)

TRICK 2: MIXER / TUMBLER (The Cocktail Coatroom)
[ Dirty BTC 1 ] \                               / [ Clean BTC 1 ]
[ Dirty BTC 2 ] ---> [ Mixing Hub (Tumbler) ] ---> [ Clean BTC 2 ]
[ Dirty BTC 3 ] /                               \ [ Clean BTC 3 ]

TRICK 3: RAPID CASH-OUT (The Smash & Grab)
[ Hack Loot: 10 BTC ] ---> [ Fresh Wallet ] ---> (Within 5 Mins) ---> [ 3 Foreign Exchanges ]
```

1. **Peel Chains (Slicing the Salami)**:
   - A criminal steals 100 BTC. If they send 100 BTC directly to an exchange, alarms ring immediately.
   - Instead, they send 95 BTC to a new address, and "peel off" 5 BTC. Then they send 90 BTC and peel off 5 BTC. They repeat this 20 times across hours or days.
   - It looks like normal people spending money, but it is actually one automated bot peeling away cash.

2. **Mixers / Tumblers (The Coatroom)**:
   - 50 people put their coats into a dark coatroom. The coats are shuffled, and everyone gets a coat of equal value back.
   - You put in 1 dirty Bitcoin, and you receive 1 clean Bitcoin that originally came from someone else.

3. **Rapid Cash-Out (The Smash & Grab)**:
   - A ransom is paid into a brand new wallet that has zero history.
   - Within 10 minutes, 98% of the money is blasted across 5 hops into crypto ATMs or foreign exchanges before police can file an injunction.

---

# Part 2: How Our Project Works (The Secret Sauce)

### 1. The Core Idea: What Was Missing?
Before our project, law enforcement had a giant blindspot:

| Tool Type | What It Sees | What It Is Blind To |
| :--- | :--- | :--- |
| **Traditional Blockchain Explorers** | Sees wallet `A` sent 5 BTC to wallet `B`. | **Zero network context**: Has no idea which computer, IP address, city, or country actually broadcast the transaction. |
| **Cyber / Network Packet Sniffers** | Sees IP `185.220.101.5` sent packets over port 8333. | **Zero crypto context**: Encrypted P2P packets look like gibberish; cannot see balances, satoshis, or wallets. |

### 💡 Our Solution: Tripartite Graph Fusion
We fuse **both worlds together** into a single 3-part graph:
1. **Wallets** (Who holds the money)
2. **Transactions** (How much was paid)
3. **IP Nodes** (Where on Earth it was broadcast from)

```
[ Wallet A ] --(funds 5.2 BTC)--> [ Transaction ] --(pays 5.1 BTC)--> [ Wallet B ]
                                         |         ^
                             (relays_to) |         | (broadcasts)
                                         v         |
                                     [ IP Node ]
                                (Country: Australia | ISP: Cloudflare)
```
Now, if a criminal moves money between 10 "different" wallets but all 10 transactions originate from the exact same foreign proxy IP within 2 minutes, **our system catches them instantly.**

---

### 2. The 7-Step Pipeline (Explained Simply)

Our backend runs an automated 11-stage pipeline in **3.4 seconds**. Here is what happens in simple terms:

```
[ Step 1: Ingest Data ]
         │
         ▼
[ Step 2: Build Tripartite Graph ] ──► (Wallets + Transactions + IP Nodes)
         │
         ▼
[ Step 3: Cluster Wallets ] ─────────► (DSU: Groups sybil addresses into 1 human actor)
         │
         ▼
[ Step 4: Extract 45 Features ] ─────► (Speed, drain velocity, hop delays, IP churn)
         │
         ▼
[ Step 5: 3 AI Detectives ] ─────────► (IForest + LOF + Mahalanobis find weird patterns)
         │
         ▼
[ Step 6: Score & Explain (SHAP) ] ──► (Risk 0-100 + Plain English reasons for court)
         │
         ▼
[ Step 7: Export SAR Report ] ───────► (Official 1-click legal filing for FIU-IND)
```

1. **Step 1 — Data Ingestion**: Loads the Bitcoin transaction records.
2. **Step 2 — Tripartite Graph Construction**: Connects Wallets $\leftrightarrow$ Transactions $\leftrightarrow$ IP addresses with strict directional flow.
3. **Step 3 — Multi-Heuristic Entity Clustering**:  
   If a criminal creates 8 different wallet addresses to hide their identity, our clustering engine uses:
   - **Common-Input Heuristic (CIOH)**: If Wallet A and Wallet B are spent together to pay for one item, the same person owns the private keys to both.
   - **Change Address Detection (CADH)**: Identifies which output is the internal change coming back to the sender.
   - *Result*: It merges those 8 fake addresses into **1 single entity cluster**.
4. **Step 4 — Feature Engineering (The 45 Clues)**:  
   For every wallet, we calculate 45 mathematical clues:
   - How fast does money leave after arriving? (e.g. 96% drained in < 10 mins).
   - What fraction was peeled off? (e.g. exactly 5% skimmed).
   - How many different countries or internet providers were hopped across?
5. **Step 5 — The 3 AI Detectives**:  
   We do not use hand-written rules. We unleash an unsupervised machine learning ensemble.
6. **Step 6 — Composite Risk Scoring (0 to 100)**:  
   We blend the AI score (50%) + Graph Structure (30%) + Community Cluster Risk (20%) into a final score:
   - 🟢 **LOW (< 35)**: Normal everyday people buying items or trading.
   - 🟡 **MEDIUM (35–49)**: Mildly suspicious; placed on surveillance watch.
   - 🟠 **HIGH (50–59)**: Priority escalation; likely automated money movement.
   - 🔴 **CRITICAL ($\ge 60$)**: **90.53% Precision**. Immediate freeze recommended; confirmed peel chain or mixer.
7. **Step 7 — 1-Click SAR / Police Report Generation**:  
   Generates an official Suspicious Activity Report (`SAR_CASE_xxxx.json`) formatted for the **Financial Intelligence Unit (FIU-IND)** under the **Prevention of Money Laundering Act (PMLA)**.

---

### 3. The 3 AI Detectives (Our ML Ensemble)
Why use 3 AI models instead of just 1? Because each model has a different "superpower":

1. **Detective 1: Isolation Forest (The Tree Isolator)**:
   - *How it works*: It randomly slices the data like a cheese grater. Normal points are packed tightly together and take 15 slices to isolate. An extreme criminal transaction sits far out alone and gets isolated in just 2 slices.
   - *Superpower*: Native tree structure allows us to run **SHAP** to explain exactly why it made the decision.
2. **Detective 2: Local Outlier Factor / LOF (The Density Checker)**:
   - *How it works*: It looks at a point's neighbors. If everyone around a wallet has high volume, it's normal. If a wallet suddenly does a strange micro-peel in an otherwise quiet area, LOF flags it.
   - *Superpower*: Catches sneaky small-value peel chains that hide from global averages.
3. **Detective 3: Robust Mahalanobis (The Ellipsoidal Geometry Checker)**:
   - *How it works*: It measures statistical distance while accounting for correlation between variables (e.g. high volume usually means high fees). If volume is high but fees are zero and speed is crazy, it calculates the geometric outlier distance.
   - *Superpower*: Immune to collinear feature distortions.

By combining all three, we achieve **defense-in-depth** — if a criminal evades one model, the other two catch them.

---

### 4. Why SHAP Matters (Translating AI for Courts)
Judges and police officers **cannot take a black-box AI score to court**. If an officer tells a judge: *"Our neural network gave this wallet a 0.98 score, so please seize their assets,"* the defense lawyer will say: *"Why? What rule was broken?"*

This is why our system uses **SHAP (SHapley Additive exPlanations)**:
- It breaks down the math into exact dollar/percentage contributions.
- We translate that into plain English:
  > *"Flagged as CRITICAL (Score 98.8/100) because 96% of funds were extracted within 10 minutes from a fresh wallet created 0.08 hours ago, routed across 3 foreign jurisdictions (Australia, US, Germany) with an asymmetric 4.8% peel-skim ratio."*
- That is **legally defensible evidence**.

---

# Part 3: 2-Minute Pitch & Teammate Cheatsheet

### The 30-Second Pitch
> *"Our project solves problem statement SIH26146 for NTRO. We built an air-gapped, offline AI system that monitors Bitcoin transactions by fusing blockchain ledger data with network IP broadcast telemetry into a tripartite graph.  
> Using an unsupervised ensemble of Isolation Forest, LOF, and Mahalanobis distance, our system clusters fake addresses into real criminal entities and detects peel chains, mixers, and rapid cash-outs with **90.53% precision** and **98.00% specificity**.  
> Every alert includes SHAP explainability and exports a 1-click legal SAR package ready for FIU-IND and law enforcement filings."*

---

### How to Answer Judge Questions

#### Q1: "Is this connected to the live internet?"
> **Answer**: *"No. It is 100% offline and air-gapped. Defense agencies like NTRO operate in secure enclaves with zero external internet egress. All GeoIP lookups, ML training, graph building, and UI dashboards run entirely locally on commodity hardware."*

#### Q2: "Why didn't you just use deep learning or Graph Convolutional Networks (GCNs)?"
> **Answer**: *"Supervised GCNs overfit to historical labels from past years. Criminals constantly change their peel fractions, delays, and mixing services. Our unsupervised anomaly ensemble detects zero-day laundering scripts that deviate mathematically from legitimate spending, without needing labeled training data."*

#### Q3: "What if an innocent person travels abroad or uses a VPN?"
> **Answer**: *"An IP hop alone never triggers an alert. We combine network metadata with financial flow dynamics—like 10-minute drain velocity, turnover ratio, and peel fractions. A legitimate traveler buying coffee will have normal wallet age and low turnover, keeping their score safely in the LOW tier."*

#### Q4: "How fast is it?"
> **Answer**: *"The full 11-stage pipeline processes 699 wallets and 683 transactions in just **3.4 seconds**. Since Bitcoin blocks arrive only once every 10 minutes (600 seconds), our system uses less than 1% of the block window, easily handling live mempool traffic."*

---

### How to Run the Project
To show a judge or run it on your laptop:

```bash
# 1. Open terminal and run the complete AI pipeline (takes ~3.4s)
python3 pipeline.py

# 2. Start the FastAPI backend
python3 -m uvicorn api.main:app --port 8000 --host 127.0.0.1

# 3. In a second terminal, start the Next.js Dashboard
cd web
npm run start
```
Then open your browser to **`http://localhost:3000`**:
- **Tab 1 (Overview)**: Big picture numbers and country charts.
- **Tab 2 (Alert Queue)**: Filter by "CRITICAL" and click the top wallet.
- **Tab 3 (Case Dossier)**: See the SHAP chart, ego-network, and click the *"Download Official SAR Package"* button!
- **Tab 4 (Network Studio)**: Show the interactive graph with gold arrows (Bitcoin flow) and dashed cyan lines (internet IP broadcasts).
