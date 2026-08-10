# Upbit Growth Command Center — Operations Dashboard Specification

> **Philosophy:** Not just a reporting dashboard, but a **"Growth War Room"**.
> The goal is not only reporting, but enabling every person in the office to immediately answer:
> 1. *Are we growing today?*
> 2. *Where is the bottleneck?*
> 3. *What should I do about it?*

---

## 1. Executive Dashboard Layout

### Today's Core Metrics
* **Inbound Users:** 1,245
* **Approved Users:** 812
* **First Deposit:** 336
* **Repeat Deposit:** 189
* **First Trade:** 254
* **Repeat Trade:** 121

---

### Conversion Funnel
$$1,245 \rightarrow 812 \rightarrow 336 \rightarrow 254 \rightarrow 121$$

| Stage | Conversion Rate |
| :--- | :--- |
| **Inbound $\rightarrow$ Approved** | 65% |
| **Approved $\rightarrow$ First Deposit** | 41% *(Largest Drop / Main Bottleneck)* |
| **First Deposit $\rightarrow$ First Trade** | 75% |
| **First Trade $\rightarrow$ Repeat Trade** | 48% |

---

### Vs. Yesterday Trends
* **Inbound Users:** `+8%`
* **Approved Users:** `-4%`
* **First Deposit:** `-12%`
* **First Trade:** `-18%`

**▲ Largest Drop:** Approved User $\rightarrow$ First Deposit

---

### AI Insight Summary
> *"Registrations are stable. First Deposits are declining. Main bottleneck today: Approved users not funding accounts."*

---

## 2. Metrics Architecture & Hierarchy

### Tier 1: Big Screen (Headline Metrics)
These are the primary numbers visible to the entire office floor:
* **Inbound Users:** Top funnel registration volume.
* **Approved Users:** KYC conversion and compliance throughput.
* **First Deposit:** User activation threshold.
* **Repeat Deposit:** Account retention and liquidity flow.
* **First Trade:** Active engagement milestone.
* **Repeat Trade:** Sustained trading activity.
* **Dormant Users:** Users who placed trades in the past but have been inactive for $>6$ months.
* **Revenue:** Real-time financial throughput.

---

### Tier 2: Conversion Rates
Conversion rates isolate operational bottlenecks faster than raw volume counts:
* **Registration $\rightarrow$ Approval**
* **Approval $\rightarrow$ First Deposit** *(e.g., Actual: 41% vs Target: 55%)*
* **First Deposit $\rightarrow$ First Trade**
* **First Trade $\rightarrow$ Repeat Trade**

---

### Tier 3: Team Leaderboards & Targets
Drives team alignment, accountability, and daily progress visibility:

| Team | Target | Actual | Achievement |
| :--- | :---: | :---: | :---: |
| **KYC Team** | 500 Approved | 812 Approved | **162%** |
| **Growth Team** | 350 First Deposits | 336 First Deposits | **96%** |

---

### Visual Color Logic
* **GREEN**: Above target
* **YELLOW**: Within 10% of target
* **RED**: Below target (e.g., First Deposit 336, -12% vs yesterday)

---

## 3. Physical TV Dashboard Requirements

To operate effectively as a live office terminal, the hardware and software layout must meet the following specs:

* **Display Hardware:** 65–85 inch TV screen.
* **Auto-Refresh:** Automatic background refresh every 60–120 seconds.
* **Display Mode:** Fullscreen kiosk mode (no browser address bar, UI chrome, or manual login requirements).
* **Visibility:** Designed for legibility from **5–10 meters away**.
* **Visual Theme:** High-contrast dark theme with large typography.
* **Design Motto:** *"Think Bloomberg Terminal, not Power BI."*

---

## 4. The Single Most Important Metric

### Center-Screen Anchor: **APPROVED $\rightarrow$ FIRST DEPOSIT RATE**
$$\text{First Deposit Rate} = \frac{\text{First Deposit Users}}{\text{Approved Users}} = 41\% \quad \text{(Target: 55\%)}$$

#### Why This Metric Matters:
$$\text{No Deposit} = \text{No Revenue} = \text{No Trader}$$

Most cryptocurrency exchanges obsess over top-of-funnel registration counts. However, the real operational bottleneck is almost always **approved users who never fund their accounts**. Focusing on this number aligns Marketing, Compliance, Operations, and Customer Support around revenue generation.

---

## 5. Data Model & Entity Specifications

Extracted from administrative entity mappings (LENS Admin):

### Entity Mapping

| Entity | Relevant Schema Fields |
| :--- | :--- |
| **User Infos** | `member_id`, `member_uuid`, `security_level`, `member_state`, `created_at`, `nationality`, `country_location` |
| **Deposit Bases** | `deposit_id`, `target_date`, `target_time`, `member_id`, `amount`, `currency_name` |
| **Trade Bases** | `trade_id`, `member_id`, `trade_date`, `volume`, `market`, `side` |

---

### KPI Definitions & Funnel Mapping

| KPI | Definition | Funnel Stage Alignment |
| :--- | :--- | :--- |
| **Inbound Users** | Total new user registrations created today. | Inbound |
| **Approved Users** | Users whose KYC / security level meets approval threshold today. | Approved |
| **First Deposit** | Users whose earliest deposit timestamp occurred today. | First Deposit (Activation) |
| **Repeat Deposit** | Users with 2+ lifetime deposits, with at least one deposit today. | Retention / Liquidity |
| **First Trade** | Users whose earliest trade execution occurred today. | First Trade |
| **Repeat Trades** | Users with 2+ lifetime trades, with at least one trade today. | Repeat Trade (Real Engagement) |
| **Dormant Users** | Users who previously traded but have zero activity for $>6$ months. | Re-engagement Target |

---

## 6. API Endpoint Specification

### `GET /api/dashboard/daily`

#### Sample JSON Response:
```json
{
  "inboundUsers": 1245,
  "approvedUsers": 812,
  "firstDeposit": 336,
  "repeatDeposit": 189,
  "firstTrade": 254,
  "repeatTrade": 121,
  "conversion": {
    "approvalRate": 65,
    "depositRate": 41,
    "firstTradeRate": 75,
    "repeatTradeRate": 48
  },
  "change": {
    "inboundUsers": 8,
    "approvedUsers": -4,
    "firstDeposit": -12,
    "repeatDeposit": 3,
    "firstTrade": -18,
    "repeatTrade": 6
  }
}
```

---

## 7. Frontend Starter Code (React + Tailwind CSS)

Below is the production-ready React component structure designed for dark kiosk displays:

```tsx
import React from "react";
import {
  Users,
  ShieldCheck,
  Wallet,
  Repeat,
  CandlestickChart,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";

const metrics = [
  {
    title: "Inbound Users",
    value: 1245,
    change: 8,
    icon: Users,
  },
  {
    title: "Approved Users",
    value: 812,
    change: -4,
    icon: ShieldCheck,
  },
  {
    title: "First Deposit",
    value: 336,
    change: -12,
    icon: Wallet,
  },
  {
    title: "Repeat Deposit",
    value: 189,
    change: 3,
    icon: Repeat,
  },
  {
    title: "First Trade",
    value: 254,
    change: -18,
    icon: CandlestickChart,
  },
  {
    title: "Repeat Trades",
    value: 121,
    change: 6,
    icon: TrendingUp,
  },
];

export default function App() {
  return (
    <div className="bg-black min-h-screen text-white p-8 font-sans">
      {/* Header Bar */}
      <div className="flex justify-between items-center mb-10">
        <div>
          <h1 className="text-5xl font-bold tracking-tight">
            UPBIT GROWTH COMMAND CENTER
          </h1>
          <p className="text-gray-400 text-xl mt-2">
            Live Performance Dashboard
          </p>
        </div>
        <div className="text-right">
          <p className="text-green-400 text-xl font-bold">● LIVE</p>
          <p className="text-gray-500">Auto refresh every 60 sec</p>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-3 gap-6 mb-10">
        {metrics.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.title}
              className="bg-zinc-900 rounded-2xl p-6 border border-zinc-800 shadow-lg"
            >
              <div className="flex justify-between items-center mb-5">
                <h2 className="text-xl text-gray-300 font-medium">{item.title}</h2>
                <Icon size={32} className="text-gray-400" />
              </div>
              <div className="text-6xl font-bold tracking-tight">
                {item.value.toLocaleString()}
              </div>
              <div
                className={`mt-3 text-2xl font-semibold ${
                  item.change > 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {item.change > 0 ? "+" : ""}
                {item.change}% vs yesterday
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Funnel & Insights */}
      <div className="grid grid-cols-2 gap-8">
        {/* Conversion Funnel Block */}
        <div className="bg-zinc-900 rounded-2xl p-8 border border-zinc-800">
          <h2 className="text-3xl font-bold mb-8">Conversion Funnel</h2>
          <div className="space-y-8">
            <FunnelStep label="Inbound Users" value="1,245" percent="100%" />
            <FunnelStep label="Approved Users" value="812" percent="65%" />
            <FunnelStep label="First Deposit" value="336" percent="41%" />
            <FunnelStep label="First Trade" value="254" percent="75%" />
            <FunnelStep label="Repeat Trade" value="121" percent="48%" />
          </div>
        </div>

        {/* Right Panel: Bottleneck, AI Insight & Monthly Target */}
        <div className="space-y-6">
          {/* Bottleneck Alert */}
          <div className="bg-zinc-900 rounded-2xl p-8 border border-zinc-800">
            <h2 className="text-3xl font-bold mb-6">Bottleneck</h2>
            <div className="flex items-center gap-4">
              <AlertTriangle size={48} className="text-yellow-400 shrink-0" />
              <div>
                <p className="text-xl text-gray-300">Biggest Drop</p>
                <p className="text-4xl font-bold text-red-400">
                  Approved → First Deposit
                </p>
                <p className="text-2xl mt-2 text-gray-200">41% Conversion</p>
              </div>
            </div>
          </div>

          {/* AI Insights & Recommended Action */}
          <div className="bg-zinc-900 rounded-2xl p-8 border border-zinc-800">
            <h2 className="text-3xl font-bold mb-6">AI Insight</h2>
            <div className="text-xl leading-relaxed text-gray-300">
              Registrations remain stable.<br /><br />
              First deposits are declining.<br /><br />
              Largest opportunity:{" "}
              <span className="text-red-400 font-bold">
                Approved Users → First Deposit
              </span>
              <br /><br />
              Recommended Actions:
              <ul className="list-disc pl-8 mt-4 space-y-2 text-gray-200">
                <li>Trigger deposit reminder within 30 minutes of approval</li>
                <li>Audit deposit friction and onboarding UX</li>
                <li>Review bank transfer completion rate</li>
              </ul>
            </div>
          </div>

          {/* Monthly Target Card */}
          <div className="bg-green-950 border border-green-800 p-8 rounded-2xl">
            <p className="text-green-300 text-lg font-semibold uppercase tracking-wider">
              Month Target
            </p>
            <div className="text-5xl font-bold mt-3 text-white">54%</div>
            <div className="text-xl mt-2 text-gray-200">First Deposit Conversion</div>
            <div className="text-green-400 text-xl mt-4 font-medium">
              Current: 41%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function FunnelStep({
  label,
  value,
  percent,
}: {
  label: string;
  value: string;
  percent: string;
}) {
  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="text-xl text-gray-300">{label}</span>
        <span className="text-xl font-bold text-white">{value}</span>
      </div>
      <div className="h-4 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className="h-4 bg-green-500 rounded-full"
          style={{ width: percent }}
        />
      </div>
      <div className="text-right text-sm text-gray-400 mt-1">{percent}</div>
    </div>
  );
}
```

---

## 8. Tactical Operational Enhancements

To further increase cross-departmental urgency and daily alignment, it is strongly recommended to add two dynamic motivational widgets to the central display:

### 1. Revenue Today Card
* **Example Output:** `Rp 183,421,000`
* **Impact:** Directly connects daily user actions with immediate business outcomes.

### 2. Gap to Target Card
* **Example Output:** `+67 First Deposits Needed Today`
* **Impact:** Translates monthly percentage targets into clear, actionable daily operational targets for Support and Growth teams.

---

## 9. DRF Implementation

The Executive Dashboard is implemented as one read endpoint backed by the SQL-owned `dashboard_daily_summary` table:

```text
GET /api/dashboard/daily/
```

The endpoint automatically reads Jakarta T-1. The user does not enter a date or query parameter. It returns the daily headline metrics, conversion percentages, percentage changes versus the previous summary row, money values, and a deterministic funnel bottleneck insight.

The summary row is refreshed by the management command below:

```bash
python manage.py refresh_dashboard
```

For a backfill or local verification, an explicit date is supported only by the command:

```bash
python manage.py refresh_dashboard --date 2026-07-13
```

The Django model is `executive_dashboard.models.DashboardDaily` and is intentionally `managed = False`; the SQL script remains the source of truth for the table schema.

### Current source-data assumptions

* Inbound users are registrations whose `user_info.created_at` falls in the target Jakarta calendar day.
* Approved users are distinct KYC members whose `member_additional_info.state` is `accept` and whose `updated_at` falls within the target Jakarta calendar day. The KYC table is the approval-event source; `security_level` is not currently used as a gating condition.
* First and repeat deposits use the full `deposit_base` history and `target_date`. First-time and repeat depositors are mutually exclusive: repeat requires a deposit before the target date.
* First and repeat trades treat both `b_customer_code` and `s_customer_code` as participants in `trade_base`. Repeat trade requires activity before the target date, so multiple same-day trades remain first-trade activity.
* Volume uses `trade_base.fiat_amount`; revenue uses the configured `DASHBOARD_REVENUE_FIELD`, which defaults to `fiat_fee`.
* Money values are returned as strings to preserve decimal precision in the API.

Configure these optional values in `.env` when the supervisor confirms different business definitions:

```dotenv
DASHBOARD_DB_ALIAS=reporter
DASHBOARD_APPROVED_STATE=accept
DASHBOARD_APPROVED_SECURITY_LEVEL=2
DASHBOARD_DORMANT_DAYS=180
DASHBOARD_REVENUE_FIELD=fiat_fee
```
