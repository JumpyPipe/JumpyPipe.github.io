#!/usr/bin/env python3
"""Turn the real dashboard data.json into an anonymized demo-data.json (same schema).

Kept OUT of the public repo on purpose. Usage: python3 make_demo_data.py real-data.json demo-data.json
"""
import json, re, sys, hashlib, math, copy
from collections import defaultdict

SEED = "demo-s37"
TARGET_TOTAL = 2684517.38          # latest total account value of the demo (must stay under $4M)
MONTHS = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
K_CHOICES = [1, 2, 2, 2, 3, 3]      # per-ticker position multiplier (shares AND contracts scale together)

def h(*parts):
    return int(hashlib.sha256((SEED + "|" + "|".join(map(str, parts))).encode()).hexdigest(), 16)

def unit(*parts):                    # deterministic uniform in [0,1)
    return (h(*parts) % 10**9) / 10**9

def jitter(span, *parts):            # deterministic multiplier in [1-span, 1+span]
    return 1 + (unit(*parts) * 2 - 1) * span

def kfor(sym):
    return K_CHOICES[h("k", sym or "-") % len(K_CHOICES)]

DESC_RE = re.compile(r"^(CALL|PUT) \(([A-Z.]+)\) .*?(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC) (\d{2}) (\d{2}) \$([\d.]+) \(100 SHS\)")
def contract_key(t):
    m = DESC_RE.match(t["desc"])
    if not m:
        return None
    typ, und, mon, dd, yy, strike = m.groups()
    return (und, "Call" if typ == "CALL" else "Put", f"20{yy}-{MONTHS[mon]:02d}-{dd}", float(strike))

STOCK_CATS = {"stock_buy", "stock_sell", "transfer_in_kind", "stock_split", "corporate_action"}
HELD_CATS = STOCK_CATS | {"assignment_stock_buy", "assignment_stock_sell"}

def held_shares(txns):
    q = defaultdict(float)
    for t in txns:
        if t["category"] in HELD_CATS and t["symbol"]:
            q[t["symbol"]] += t["qty"]
    return q

def recompute(txns, positions, chains, orig_buyhold):
    """Rebuild every derived collection from the transaction list (mirrors build_data.py)."""
    legs = defaultdict(list)
    for t in txns:
        if t["isOption"]:
            k = contract_key(t)
            if k: legs[k].append(t)
    for p in positions:
        ls = legs.get((p["underlying"], p["type"], p["expiry"], p["strike"]), [])
        p["stoSum"] = round(sum(t["amount"] for t in ls if t["category"] == "option_sto"), 2)
        p["btcSum"] = round(sum(t["amount"] for t in ls if t["category"] == "option_btc"), 2)
        p["netPnl"] = round(sum(t["amount"] for t in ls), 2)
        p["contracts"] = int(round(sum(abs(t["qty"]) for t in ls if t["category"] in ("option_sto", "option_bto"))))
    by_chain = defaultdict(float)
    for p in positions:
        by_chain[p["chainId"]] += p["netPnl"]
    for c in chains:
        c["netPnl"] = round(by_chain[c["chainId"]], 2)
    # buy & hold rows
    groups = defaultdict(list)
    for t in txns:
        if t["category"] in ("stock_buy", "stock_sell"):
            groups[(t["symbol"], t["year"])].append(t)
    desc = {(r["symbol"], r["year"]): r["description"] for r in orig_buyhold}
    bh = []
    for (sym, yr), items in groups.items():
        tb = round(-sum(t["amount"] for t in items if t["category"] == "stock_buy"), 2)
        ts = round(sum(t["amount"] for t in items if t["category"] == "stock_sell"), 2)
        ds = [t["date"] for t in items]
        bh.append({"symbol": sym, "description": desc.get((sym, yr), items[0]["desc"]), "year": yr,
                   "totalBuys": tb, "totalSells": ts,
                   "buyCount": sum(1 for t in items if t["category"] == "stock_buy"),
                   "sellCount": sum(1 for t in items if t["category"] == "stock_sell"),
                   "netQty": round(sum(t["qty"] for t in items), 3), "netInvested": round(tb - ts, 2),
                   "firstDate": min(ds), "lastDate": max(ds)})
    groups = defaultdict(list)
    for t in txns:
        if t["category"] in ("assignment_stock_buy", "assignment_stock_sell"):
            groups[(t["symbol"], t["year"])].append(t)
    asg = []
    for (sym, yr), items in groups.items():
        b = round(-sum(t["amount"] for t in items if t["category"] == "assignment_stock_buy"), 2)
        s_ = round(sum(t["amount"] for t in items if t["category"] == "assignment_stock_sell"), 2)
        asg.append({"symbol": sym, "year": yr, "bought": b, "sold": s_,
                    "buyCount": sum(1 for t in items if t["category"] == "assignment_stock_buy"),
                    "sellCount": sum(1 for t in items if t["category"] == "assignment_stock_sell"),
                    "net": round(s_ - b, 2)})
    return bh, asg

def main(src, dst):
    real = json.load(open(src))
    demo = copy.deepcopy(real)
    T = demo["transactions"]

    # ---- self-check: the recompute logic reproduces the real derived numbers --------------------
    chk_pos = copy.deepcopy(real["optionPositions"]); chk_ch = copy.deepcopy(real["optionChains"])
    recompute(real["transactions"], chk_pos, chk_ch, real["buyholdRows"])
    bad = [p["symbol"] for p, o in zip(chk_pos, real["optionPositions"])
           if abs(p["netPnl"] - o["netPnl"]) > 0.011 or p["contracts"] != o["contracts"]]
    assert not bad, f"recompute mismatch on {len(bad)} positions, e.g. {bad[:3]}"

    quotes = real["prices"]["quotes"]
    held0 = held_shares(real["transactions"])
    inv0 = sum(q * quotes.get(s, 0) for s, q in held0.items())

    # ---- transform every transaction -------------------------------------------------------------
    for i, t in enumerate(T):
        und = t["symbol"]
        k = kfor(und)
        base = (i, t["date"], t["category"], t["amount"])
        cat = t["category"]
        if cat == "cash_transfer":
            t["_cash"] = True                   # amount set after c is known
        elif t["isOption"]:
            if t["amount"] != 0:
                t["amount"] = round(t["amount"] * k * jitter(0.04, *base), 2)
            t["qty"] = t["qty"] * k
        elif cat.startswith("assignment_stock"):
            t["amount"] = round(t["amount"] * k, 2); t["qty"] = round(t["qty"] * k, 3)
        elif cat in STOCK_CATS:
            t["amount"] = round(t["amount"] * k * jitter(0.015, *base), 2); t["qty"] = round(t["qty"] * k, 3)
        elif cat == "dividend":
            t["amount"] = round(t["amount"] * k * jitter(0.05, *base), 2)
        elif cat in ("fee", "foreign_tax"):
            t["amount"] = round(t["amount"] * k * jitter(0.05, *base), 2)
        else:
            t["_cash"] = True

    held1 = held_shares(T)
    inv1 = sum(q * quotes.get(s, 0) for s, q in held1.items())
    inv_factor = inv1 / inv0

    # ---- balances: choose the cash factor c so the latest total hits the target ------------------
    b_latest = real["balances"]["latest"]
    cash_target = TARGET_TOTAL - b_latest["investmentsValue"] * inv_factor
    c = cash_target / b_latest["cashAndCredits"]
    for t in T:
        if t.pop("_cash", False):
            a = t["amount"]
            t["amount"] = round(a * c * (jitter(0.10, i_ := t["date"], t["amount"], "x") if abs(a) >= 5 else 1), 2)

    # open short-put collateral, exactly as the dashboard computes it
    legs_open = [p for p in demo["optionPositions"] if p["outcome"] == "Still open" and p["type"] == "Put"]
    # (recompute first so contracts are the new ones)
    bh, asg = recompute(T, demo["optionPositions"], demo["optionChains"], real["buyholdRows"])
    demo["buyholdRows"], demo["assignedRows"] = bh, asg
    collateral = sum(p["strike"] * 100 * p["contracts"] for p in demo["optionPositions"]
                     if p["outcome"] == "Still open" and p["type"] == "Put")

    def rebalance(s, latest=False):
        s = dict(s)
        inv = s["investmentsValue"] * inv_factor
        cash = s["cashAndCredits"] * c
        s["investmentsValue"] = round(inv, 2); s["cashAndCredits"] = round(cash, 2)
        s["totalValue"] = round(inv + cash, 2)
        s["settledCash"] = round(s["settledCash"] * c, 2)
        s["availableToWithdraw"] = round(s["availableToWithdraw"] * c, 2)
        s["availableToTrade"] = round(s["availableToTrade"] * c, 2)
        s["dayChangeInvestments"] = round(s["dayChangeInvestments"] * inv_factor, 2)
        s["dayChangeTotal"] = round(s["dayChangeTotal"] * (s["totalValue"] / (b_latest["totalValue"])) * (b_latest["totalValue"] / (b_latest["cashAndCredits"] + b_latest["investmentsValue"])), 2)
        return s
    new_hist = [rebalance(x) for x in real["balances"]["history"]]
    latest = rebalance(b_latest)
    latest["availableToTrade"] = round(latest["cashAndCredits"] - collateral, 2)   # matches the "tied up in puts" check
    if new_hist and new_hist[-1]["asOf"] == latest["asOf"]:
        new_hist[-1] = latest
    demo["balances"] = {"latest": latest, "history": new_hist}

    # ---- Fidelity's running cash balance column (2026 rows only) --------------------------------
    NONCASH = {"transfer_in_kind", "stock_split", "corporate_action"}
    idx = [i for i, t in enumerate(T) if t.get("cashBalance") is not None]
    if idx:
        D, run = {}, 0.0
        for i in range(idx[0], len(T)):
            t, o = T[i], real["transactions"][i]
            if t["category"] not in NONCASH:
                run += t["amount"] - c * o["amount"]
            D[i] = run
        last = D[idx[-1]]
        for i in idx:
            T[i]["cashBalance"] = round(real["transactions"][i]["cashBalance"] * c + D[i] - last, 2)

    # ---- in-kind transfer rows (mirror their transactions) --------------------------------------
    tk = {(t["symbol"], t["date"]): t for t in T if t["category"] == "transfer_in_kind"}
    for r in demo["transferRows"]:
        k = kfor(r["symbol"])
        t = tk.get((r["symbol"], r["date"]))
        r["qty"] = round(r["qty"] * k, 3)
        r["value"] = t["amount"] if t else round(r["value"] * k, 2)

    demo["meta"]["cashTransferTotal"] = round(sum(t["amount"] for t in T if t["category"] == "cash_transfer"), 2)

    json.dump(demo, open(dst, "w"), separators=(",", ":"))
    print(f"inv_factor={inv_factor:.3f} cash_factor c={c:.3f}")
    print(f"latest total {latest['totalValue']:,.2f}  cash {latest['cashAndCredits']:,.2f}  inv {latest['investmentsValue']:,.2f}  collateral {collateral:,.0f}")
    print("cashTransferTotal", demo["meta"]["cashTransferTotal"])
    print("k by ticker:", {s: kfor(s) for s in sorted(quotes)})

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
