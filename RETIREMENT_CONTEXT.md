# Retirement Planning Context Handoff

## Current AI / Repo Handoff - 2026-08-04

This section was added after a prior AI session was lost. Use it first before making new code or planning changes.

Repo state:

```text
Repo path: C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23
Branch: dev
Active file: Simple_Main.py
Current git state: dirty / uncommitted work exists
Modified tracked files: STATUS.md, Simple_Main.py, categories.csv
Context docs to commit/protect: RETIREMENT_CONTEXT.md, docs/retirement/README.md, STATUS.md
Generated output context: exports/printed 2026-06-14 through 2026-07-30
Do not commit local installer: Obsidian-1.12.7.exe
```

Important: do not discard the current uncommitted `Simple_Main.py` changes. They contain a large retirement-dashboard update, roughly 2,800+ added lines, and appear to be active prior-agent work. They still need review and testing before being committed as program code.

Current uncommitted `Simple_Main.py` work includes:

```text
Default active data year changed toward 2026.
Supported finance years are explicitly limited to 2024, 2025, and 2026.
City Visa import now auto-selects the newest City_Visa_Year to date_download_*.CSV file.
USAA_HEALTH_CARE_CHECKING CSV import was added.
Costco City Bank / USAA Visa card refunds reduce spending instead of inflating outflow.
Option 5.3 added: Retirement spending guardrail report.
Option 5.3h added: Retirement guardrail dashboard HTML.
Option 5.3m added: Retirement month-end review / preview HTML.
Option 17 added: Trust / Vanguard dividends detail search.
Create DB and recategorize flows now try to refresh the retirement guardrail dashboard.
```

Testing still needed before committing `Simple_Main.py`:

```text
Run Python syntax check.
Test startup/year selection.
Test database rebuild and recategorize flows.
Test option 5.3 text report.
Test option 5.3h dashboard HTML.
Test option 5.3m month-end review HTML.
Test option 16.1 retirement guardrail cash view.
Test option 17 Trust/Vanguard dividend detail search.
Verify generated dashboard/month-end files land in the intended Fieldstack and export locations.
```

The active planning source of truth is still Fieldstack / Obsidian:

```text
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\RETIREMENT - ACTIVE COMMAND CENTER.md
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active
```

Most current Fieldstack files to read first:

```text
32_Retirement_Daily_Timeline.md
34_Budget_Finance_Revamp_Truth.md
39_Phase_2_Union_Allocation_Workplan.md
40_Monthly_Retirement_Spending_Summaries.md
41_Retirement_Open_Process_Checklist.md
42_Retirement_Daily_Scan_Quick_Reference.md
```

Latest operational status found in Fieldstack notes:

```text
2026-08-03: Fidelity pension webpage still showed nothing; paperwork had been approved/submitted earlier, but pension calculation/payment was still being watched.
2026-08-03: HRA reimbursement was approved/submitted; user submitted medical premium, COBRA dental, and contact-lens reimbursement items, exhausting the HRA account. Expected reimbursement total is about $3,330.62.
2026-08-01: COBRA dental autopay came out of the USAA healthcare account and appears to work.
2026-08-26 note: checking cash was projected/recorded as low, with planned transfer of $10,000 from Ford and $3,800 from Cash Plus / house repair for well work. Receipts were placed in the retirement folder.
```

Current finance planning anchor:

```text
Planned expense budget before taxes: about $15,712.63/month.
Estimated net pension plus already-taxed cash line: about $14,322/month.
Use the guardrail dashboard to distinguish posted spending, known upcoming bills, healthcare timing, HRA reimbursements, and whether a Union draw is actually needed.
The dashboard should not treat daily run-rate projection as the main permission signal; the calmer posted-plus-known-bills logic from 2026-07-13 is preferred.
```

Phase 2 Union allocation anchor:

```text
Union account snapshot captured 2026-06-29: about $529,302.36.
Current allocation read: about 96.79% stock/growth and 3.21% bond.
Phase 2 task: download current investment CSVs/statements, confirm actual holdings and available funds, then model a safer withdrawal sleeve for post-pension years.
Do not assume the correct allocation without current holdings and plan-option details.
```

Last updated: 2026-06-27

## Current Update - 2026-06-27 Phase 1 / Phase 2 Handoff

Current dashboard:

- Fieldstack active note: `C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\34_Budget_Finance_Revamp_Truth.md`
- Phase 2 workplan: `C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\39_Phase_2_Union_Allocation_Workplan.md`
- Live dashboard: `C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\retirement_guardrail_dashboard.html`
- Monthly transaction reference: `C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\monthly_transactions_by_category.html`

Current Phase 1 read:

```text
Phase 1 is the first 5-year pension bridge.
Pension + cash buckets + healthcare/house/tax reserves are intended to cover normal life.
The goal is to avoid forced Union / 401k withdrawals or VTI/ETF sales during a market crash.
```

Dashboard numbers as of 2026-06-27:

```text
Current all-in run rate:                   about $10,558/mo
Next-month forecast:                       about $11,278/mo
Cash-neutral line before Union draw:        about $14,322/mo
Planned expense budget before taxes:        about $15,713/mo
Current forecast Union draw gap:            $0
```

Phase 1A / 1B workstreams:

```text
Phase 1A = budget cuts and monthly run-rate improvement.
Review subscriptions, utilities, appliance efficiency, insurance, groceries, and recurring charges.

Phase 1B = HSA funding source.
The HSA target is tax planning, but cash still has to come from monthly surplus,
existing cash reserve, or a deliberate Union / 401k withdrawal.
Union funding is not the default because it creates taxable income,
even if the HSA deduction may offset some tax impact.
```

Dashboard state:

```text
retirement_guardrail_dashboard.html includes highlighted Phase 1B HSA Funding reminder,
Phase 1A budget-cut reminder, Phase 2 Union Allocation quick link, and Monthly Transactions link.
monthly_transactions_by_category.html shows June 2026 expenses grouped by category,
including Uncategorized / ungrouped rows, for quick spouse/family budget review.
```

Phase 2 meaning:

```text
After the 5-year pension bridge, the Union account may become the higher-withdrawal engine.
The Union account's role then changes from mostly growth/preservation to income support.
A more conservative Union allocation may be appropriate before the pension bridge ends.
```

If user says "let's work on Phase 2":

```text
Use the Phase 2 Union Allocation Workplan note.
Ask user to download/export investment CSVs or statements.
Build a current holdings/allocation table.
Then model a safer Union withdrawal sleeve for the post-pension years.
Do not assume the correct allocation until actual holdings and available plan options are reviewed.
```

Union fund menu captured 2026-06-29:

```text
User pasted the available Union account fund menu.
This is the menu of available funds, not the current allocation.

Funds user marked as currently owned:
- Vanguard Institutional Total Bond Market Index Trust (7502)
- Vanguard Institutional Total Stock Market Index Trust (M220)
- Vanguard International Growth Fund Admiral Shares (VWILX / 0581)

Likely safer/withdrawal sleeve candidates:
- Vanguard Interest Income Fund (4854)
- Vanguard Institutional Total Bond Market Index Trust (7502)
- Vanguard Core Bond Fund Admiral Shares (VCOBX / 1520)
- JPMCB SmartRet Passive Blend Income / 2025 / 2030

Likely growth candidates:
- Vanguard Institutional Total Stock Market Index Trust (M220)
- Vanguard Institutional Total International Stock Market Index Trust (7586)
- Vanguard International Growth Fund Admiral Shares (VWILX / 0581)
- Vanguard Explorer Fund Admiral Shares (VEXRX / 5024)
- Vanguard FTSE Social Index (VFTNX / 0223)
- Vanguard Global ESG Select Stock (VESGX / 0547)
- Later JPMCB SmartRet target-date blends

Current holdings snapshot captured 2026-06-29:
- Vanguard Institutional Total Stock Market Index Trust: $338,645.67, about 63.98%
- Vanguard Institutional Total Bond Market Index Trust: $17,006.11, about 3.21%
- Vanguard International Growth Fund Admiral Shares (VWILX): $173,650.58, about 32.81%
- Total Union account snapshot: $529,302.36

Current risk read:
- Stock / growth exposure: about 96.79%
- Bond exposure: about 3.21%

Interpretation:
This is very growth-heavy. It may be acceptable for Phase 1 if pension/cash buckets carry spending,
but Phase 2 should evaluate how much to move into a safer withdrawal sleeve before pension bridge ends.
Still useful: official current holdings/balances CSV or statement to confirm exact balances and fund IDs.
```

## Purpose

This file is for future AI agents and future review sessions. The user is building a retirement launch planning system inside this finance program and in Obsidian-style Markdown files.

The immediate goal is to help the user prepare for retirement notice, healthcare transition, pension startup risk, and the psychological transition from paycheck income to planned spending from cash buckets while waiting for pensions.

## Key Planning Numbers

Known / user-provided numbers:

```text
Lifestyle baseline before healthcare:      about $12,500/mo
High lifestyle stress case:                about $13,500/mo
Boldin all-in modeled spending:            about $20,579/mo
Boldin safe spending now:                  about $27,535/mo
Boldin success probability:                about 99%
Known cash reserve, excluding brokerage:   about $230,000
Brokerage backup layer:                    about $410,000
Pension delay monthly need:                about $20,032/mo
6-month pension delay need:                about $120,192
Suggested pension-delay bucket:            $125,000-$150,000
Healthcare OOP target range:               $14,000-$17,000
```

Historical spending from current local SQLite data:

```text
2024 average spending: about $11,405/mo
2025 average spending: about $13,611/mo
2026 Jan-Apr average spending after refresh: about $12,802/mo
Weighted blended average: about $12,550/mo
```

2025 was elevated by a likely one-time vacation/travel spike:

```text
2024 vacation spending: about $2,223
2025 vacation spending: about $11,218
Difference: about $9,000/yr, or $750/mo
```

## Single Source Of Truth

The active retirement planning files now live in the user's Obsidian/Fieldstack vault, not in this finance-program docs folder.

Start here:

```text
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\RETIREMENT - ACTIVE COMMAND CENTER.md
```

Active folder:

```text
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active
```

This finance project keeps only a pointer at `docs/retirement/README.md` to avoid duplicate editing confusion.

## Current Files Created In Fieldstack

Planning docs and HUD files live under:

```text
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active
```

Important files:

```text
00_Retirement_Heads_Up_Display.md
01_Critical_Next_2_Weeks_Checklist.md
02_Healthcare_Decision_Center.md
03_Pension_Bridge_and_Cash_Buckets.md
04_Wife_Checklist.md
05_Project_Goal_Roadmap_-_House.md
06_Tax_HSA_Roth_Planning.md
07_Program_Dashboard_Build_Plan.md
08_Retirement_Transition_Call_Log.md
09_Brainstorm_Ideas_Inbox.md
10_Healthcare_Research_2026-06-02.md
11_Work_Contacts_Recommendations.md
12_Kaiser_Lump_Sum_Rollover_Call_Prep.md
13_Retirement_Buffer_Ebb_Flow_Rules.md
14_Phase_0_Today_Quick_Reference.md
15_Lump_Sum_Flexibility_vs_Monthly_Pension.md
16_Monthly_Pension_Union_Withdrawal_Reference.md
17_Vanguard_KPSSRPUG_TSA_Call_Notes_2026-06-03.md
18_Pension_Office_Call_Questionnaire.md
retirement_hud_assumptions.csv
retirement_hud_accounts.csv
retirement_hud_buckets.csv
generate_retirement_hud.py
retirement_heads_up_display.html
```

Regenerate the HTML HUD:

```powershell
python "C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\generate_retirement_hud.py"
```

The CSV files are the editable inputs. The HTML is reproducible output.

## Current HUD Design

The user wants a visual, goal-oriented Heads-Up Display with fuel/gas gauges.

Current HTML HUD pages:

```text
Overview / Monthly Front Page
Milestones
Accounts
Reserve
Projects
Savings Work
Waterfall
Guardrails
Phases
Healthcare
Taxes
Unknowns
```

Bucket gauges currently include:

```text
Pension Delay Bridge
Emergency / Operating Reserve
Healthcare Out-of-Pocket Bucket
HSA Contribution Bucket
Tax Reserve / Withholding Bucket
House Roof / Summer Repairs
Christmas / Gifts
Heater / HVAC Watch
Paint / Trim Future
```

Initial bucket allocations are draft assumptions only. User still needs to provide exact everyday account balances and desired allocations.

Important HUD logic update:

```text
Bucket gaps are visual reminders only.
They do not automatically mean taking IRA money.
Optional monthly bucket refill is set to $0 for launch mode.
IRA draw estimates only include the monthly gap, emergency refill if cash drops below $220k, and optional refill if deliberately entered.
```

Current account design:

```text
Trust Cash + Ford Cash = emergency reserve benchmark around $220k.
Existing Cash Plus = house/project reserve only.
New Vanguard Cash Plus / Pension Landing = planned account solely for pension deposits and monthly distribution.
USAA Healthcare Checking = healthcare bill-pay account, currently $1,000, keep one month ahead if possible.
```

## Major Planning Themes

### -1. Retirement Buffer Ebb / Flow Rule

Detailed active note:

```text
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\13_Retirement_Buffer_Ebb_Flow_Rules.md
```

The user already manages cash by watching the checking / emergency buffer rise and fall, then investing extra only when the buffer feels healthy. Retirement should use the same mental model, with different refill sources:

```text
Before retirement: paycheck -> bills -> buffer rises/falls -> extra invested
After retirement: pension / Social Security / Union withdrawals -> bills -> buffer rises/falls -> refill buckets, hold cash, or invest extra
```

Rules documented:

```text
First-line cash reserve can ebb and flow.
Brokerage is a second-line backup layer, not daily emergency cash.
Most emergencies do not all happen at the same time.
First 3-6 months after retirement should be conservative while pension, healthcare, withholding, and actual monthly burn settle.
After launch, optional spending can reopen through named buckets.
If roof / Christmas / taxes dent the reserve, refill slowly from surplus or small Union withdrawals if confirmed flexible.
Invest extra only after the buffer is back in the comfort zone.
```

### -0.5. Lump Sum Flexibility vs Monthly Pension Framing

Detailed active note:

```text
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\15_Lump_Sum_Flexibility_vs_Monthly_Pension.md
```

Core framing:

```text
The lump sum is not magic extra money. It is a control strategy.
Monthly pension = forced taxable income every month.
Lump sum in Union plan = user chooses when taxable withdrawals happen.
```

The user clarified that the plan likely still needs withdrawals. The flexibility is not avoiding all withdrawals. The flexibility is matching withdrawals to actual spending after month-end reality is known.

Important spending assumption:

```text
Current spending estimate: about $13,700/month.
This is based on prior spending and habits, so it includes some ordinary life variation.
There may be a $1k-$2k monthly margin, possibly $3k-$4k if unnecessary/work-related spending drops.
```

Decision question:

```text
Is the tax timing / withdrawal control / bucket-refill flexibility worth giving up the simplicity and guarantee of monthly pension payments?
```

The lump sum may be worth it only if direct rollover, Rule of 55, partial withdrawals, safe fund options, reasonable withdrawal timing, and written confirmation are all in place.

### -0.25. Monthly Pension / Union Withdrawal Reference

Detailed active note:

```text
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\16_Monthly_Pension_Union_Withdrawal_Reference.md
```

Key modeled monthly pension scenario:

```text
2027 pension $17,765/mo, expenses $19,203/mo, gap $1,438/mo
2028 pension $17,765/mo, expenses $19,474/mo, gap $1,709/mo
2029 pension $17,765/mo, expenses $19,929/mo, gap $2,164/mo
2030 pension $17,765/mo, expenses $20,369/mo, gap $2,604/mo
2031 pension $12,223/mo, expenses $20,646/mo, gap $8,423/mo
```

Modeled gross Union withdrawal requests if 20% withholding applies:

```text
2027 net $1,430/mo -> request $1,788/mo, withholding $358/mo
2028 net $995/mo -> request $1,244/mo, withholding $249/mo
2029 net $1,449/mo -> request $1,811/mo, withholding $362/mo
2030 net $1,888/mo -> request $2,360/mo, withholding $472/mo
2031 net $7,724/mo -> request $9,655/mo, withholding $1,931/mo
```

Interpretation:

```text
Monthly pension covers most expenses.
Union withdrawals cover the modeled gap.
20% withholding is tax prepayment and may partly return as refund.
Do not spend projected refunds before arrival; refund refills weakest bucket first.
```

### -0.1. Vanguard KPSSRPUG / TSA Call Results

Detailed active note:

```text
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\17_Vanguard_KPSSRPUG_TSA_Call_Notes_2026-06-03.md
```

User called Vanguard on 2026-06-03 about KP Union Supplemental Savings / KPSSRPUG and TSA/403(b).

Reported by phone:

```text
TSA is a 403(b).
KPSSRPUG follows 401(k)-type rules and is not an IRA.
Direct pension lump sum rollover into KPSSRPUG was reported as allowed.
No withholding on direct rollover was reported.
Partial/as-needed withdrawals were reported as allowed.
Unlimited withdrawals were reported.
Direct deposit was reported as available.
Automatic monthly payment setup may take up to 30 days.
Partial withdrawals may be possible while automatic setup is pending.
Typical one-time withdrawal withholding was reported as 20%.
Conservative KPSSRPUG option reported around 3.35%.
TSA/403(b) stable/money option reported around 3.19%.
```

Still must get written confirmation:

```text
Rule of 55 applies to rolled-in pension lump sum money.
Exact 1099-R coding before age 59 1/2.
Whether tax advisor must file a form after first year.
Withholding rules for one-time vs installment distributions.
Post-separation fees and which fees KP covers.
Current safe-fund names, yields, expense ratios, and withdrawal source rules.
```

Decision-risk update:

```text
The user is concerned the lump-sum strategy may involve too many hoops and too much risk of something going wrong unless the plan rules clearly confirm the strategy.
If the plan rules clearly support 401(k)-type treatment, pension rollover, partial withdrawals, and the age-55 separation exception, the lump sum remains possible.
If the strategy depends on ambiguous tax coding, later special forms, or difficult confirmation, the monthly pension likely wins on simplicity and execution safety.
```

### 0.0. Pension Office Call Questionnaire

Detailed active note:

```text
C:\Users\webzt\Dropbox\PC\Documents\Fieldstack_2_2026\projects\retirement-planning\active\18_Pension_Office_Call_Questionnaire.md
```

Use before calling Kaiser pension / retirement services. It covers:

```text
pension case number and required documents
official separation / retirement letter requirement
Final Average Monthly Compensation
credited service
early retirement reduction
offsets
quote type: lifetime annuity vs 60-month/5-year option vs supplemental/TSA vs combined
accuracy of pension estimate tool
written calculation worksheet request
whether worksheet/review/questions delay pension processing
first payment timing and retro pay
tax withholding forms
lump sum direct rollover paperwork
latest election date before start-date delay
```

### 0. Pension Calculation Verification

The user is trying to independently sanity-check the pension calculation because the pension tool provides a result but may not be transparent about the inputs. The user is concerned that asking for recalculation/verification could delay pension processing, but also wants to make sure the result is accurate before relying on it.

Known formula from user-provided plan language:

```text
Normal retirement benefit at age 65 =
1.5% x Final Average Monthly Compensation x Years of Credited Service
- any applicable pension offset
```

Early retirement percentage table from user:

```text
Age 65 100%, 64 97%, 63 94%, 62 91%, 61 88%, 60 85%, 59 80%, 58 75%, 57 70%, 56 65%, 55 60%
```

Known user data:

```text
Credited service: 26 years, 8 months, 20 days, approximately 26.72 years
Tool estimate: about $13,000/month at current age/option
User clarified this is the amount the tool says he gets per month at his current age.
```

Important clarification:

```text
Do not assume the user's Final Average Monthly Compensation.
Only reverse-calculate implied FAMC as a sanity check.
The tool's $13k/month estimate under the simple age-56 65% formula implies a high FAMC, which made the user question whether the option/result is being interpreted correctly.
```

Questions added to the Obsidian command center and call log:

```text
What FAMC was used?
What months/years were included?
Was the early retirement reduction already applied?
What credited service number was used?
Was any offset applied?
Is the quote lifetime annuity, 60-month/5-year temporary option, supplemental/TSA payout, or combined estimate?
Can they provide a written worksheet without delaying the application?
Would requesting review delay first payment?
```

New high-priority strategy documented on command center:

```text
Pension Lump Sum / Rule of 55 Strategy - Verify Before Acting
Possible pension lump sum: about $715,102
Idea: direct rollover into KP Union Supplemental Savings Plan if allowed, rather than taxable cash or Traditional IRA.
Goal: tax-deferred rollover plus possible Rule of 55 penalty-free access at age 56.
Critical unknowns: whether plan accepts inbound rollover, allows partial/installment withdrawals, preserves Rule of 55 access, and codes 1099-R correctly.
Do not assume. Must get written confirmation from KP Benefits / Union Plan / Plan Administrator.
```

### 1. Pension Delay Risk

The user may retire before pension payments fully start. A 6-month delay could require about $120k cash. The pension-delay bridge bucket should be funded before optional projects.

Rule:

```text
Use bridge bucket during pension delay.
Use retro pension pay to refill bridge bucket first.
```

### 2. Pension Amount Risk

The pension amount may be different than estimated. Model separately:

```text
Expected pension
5% lower
10% lower
15% lower
Delayed 6 months
Delayed 6 months and 10% lower
```

Delayed pension is a timing risk. Lower pension is a permanent income-floor risk.

### 3. Healthcare Risk

Healthcare is a top unknown.

Known/user thinking:

```text
User may use Kaiser Marketplace Bronze HSA-qualified HDHP for self + kids.
Wife may need Medicare because marketplace plan may not cover her if Medicare eligible.
Employer retiree coverage and COBRA details are unclear.
Work before-65 coverage may be very expensive, around $3,500/mo plus dental/vision unknown.
Kaiser marketplace info appears more transparent to user.
```

Healthcare items to track:

```text
Employer KP coverage end date
COBRA cost, coverage, retroactive rules
Kaiser Marketplace effective date
Wife Medicare medication coverage
Kids dental and vision
Healthcare out-of-pocket bucket
HSA eligibility and contribution limit
```

HSA notes:

```text
Age 55+ catch-up is $1,000, not age 50.
If self-only HDHP: 2026 total with catch-up about $5,400.
If user + kids qualify as family HDHP: 2026 total with catch-up about $9,750.
If the user is on Medicare, no new HSA contributions.
Wife being on Medicare does not automatically block user's own HSA if user is otherwise HSA eligible.
```

### 4. Project Cash / House Repairs

House/roof/summer repair spending is a top risk because it can collide with pension delay and healthcare uncertainty.

Projects to track:

```text
Roof this year
Heater/HVAC planning
Paint next year
Deck later
House trim
```

Rule:

```text
Optional projects do not use pension-delay cash.
Roof/safety repairs get priority after written bids.
Projects over $5k need a funding-source decision.
```

### 5. Tax / Roth / Refund Planning

Future dashboard should show:

```text
Tax reserve bucket
20% mandatory withholding from certain withdrawals
Actual tax liability vs withholding
Potential refund / overpayment
Tax bracket ceiling room
Roth conversion room
HSA contribution gauge
```

Rule:

```text
Do not spend projected refunds until received.
Refunds refill weakest bucket first.
```

## Program Direction

The current app menu is too large. Future implementation should move to submenus:

```text
1. Daily / Monthly Finance Review
2. Retirement Planning
3. Cash Buckets & Account Balances
4. Reports / Exports
5. Setup & Maintenance
0. Exit
```

Cash bucket implementation should separate:

```text
Accounts = where money physically sits
Buckets = what money is for
Allocations = how account balances fund buckets
```

Needed tables later:

```text
ACCOUNT_SNAPSHOTS
BUCKETS
BUCKET_ALLOCATIONS
```

New snapshots should copy prior values so the user can update only changed balances every 2-3 weeks.

## Immediate Next Steps

1. Use Fieldstack `14_Phase_0_Today_Quick_Reference.md` for today's transition calls and note capture.
2. Before work access shuts off, collect outside-work phone/email contacts for Jacob, scheduler/Andrea, HR, payroll/paycheck questions, benefits, pension, Union/KPSSRPUG, and credentialing/licensing.
3. Ask HR/manager when work email, HR portal, payroll/paystub, and benefits access shut off.
4. Ask when the official retirement/separation letter will be issued and whether it can be sent to personal email. This may be needed for healthcare qualifying life event proof, pension processing, and Union withdrawal activation.
5. Call pension / Union plan using `12_Kaiser_Lump_Sum_Rollover_Call_Prep.md`; specifically verify rollover acceptance, Rule of 55, partial withdrawals, request-to-bank timing, EFT vs check, first-withdrawal setup delay, withholding, and any waiting period after lump sum rollover.
6. User should review/edit the Fieldstack `retirement_hud_accounts.csv` with real everyday account totals.
7. User should review/edit the Fieldstack `retirement_hud_buckets.csv` with actual bucket allocations and targets.
8. Regenerate HTML HUD.
9. Open `retirement_heads_up_display.html`.
10. Continue filling Obsidian-style checklist notes.
11. Later integrate HUD generation into `Simple_Main.py` retirement submenu.

## Important User Preference

The user is visual and goal-oriented. Fuel gauges, clear percentages, color zones, and one-page Heads-Up Display are motivating and reduce anxiety.

The psychological concern is significant: transitioning from paycheck income to spending from cash while waiting for pensions may feel very uncomfortable. The HUD should reinforce that the pension-delay bucket exists for exactly this purpose.
