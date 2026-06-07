---
generated: "2026-06-06"
source: "docs/converted/client-spec/terrafurn-business-system-specification.md"
chapter: 9
title: "Order Management and Client Communication"
coverage:
  total: 58
  covered: 27
  partial: 17
  missing: 11
  deferred: 3
coverage_score: "80%"
---

# 9. Order Management and Client Communication — Coverage

**Coverage: 80%** — 27 covered, 17 partial, 11 missing, 3 deferred (58 total)

---

## 9.1 Order Channels

primary order channel: B2B portal

> [!trace-deferred]
> ⏭️ `CS-9-001` Primary order channel: B2B portal — *00-overview.md §2 "Out of scope": B2B portal M2+*

> [!trace-covered]
> ✅ `CS-9-002` B2B context: not end-consumer *(implicit)* — *00-overview.md §1, interior designers and office furnishers as partners*

secondary order channel: email

> [!trace-covered]
> ✅ `CS-9-003` Secondary order channel: email — *01-order-intake.md §2.1*

> [!trace-partial]
> ⚠️ `CS-9-004` Priority ordering: portal > email *(implicit)* — *06-data-model.md §2.4 Order.source* — data model lists channels but does not define priority between them

email orders are interpreted by the system using AI-based processing

> [!trace-covered]
> ✅ `CS-9-005` AI-based email processing — *01-order-intake.md §2.1 + 02-order-processing.md §2*

---

## 9.2 Email Processing

email processing

> [!trace-covered]
> ✅ `CS-9-006` Email processing capability — *01-order-intake.md §2, 02-order-processing.md §2*

order recognition

> [!trace-covered]
> ✅ `CS-9-007` Order recognition — *01-order-intake.md §2.1 "order" category*

AI-based data extraction

> [!trace-covered]
> ✅ `CS-9-008` AI-based data extraction — *02-order-processing.md §2.1*

product code recognition

> [!trace-covered]
> ✅ `CS-9-009` Product code recognition — *02-order-processing.md §2.2 "product_code extraction"*

quantity recognition

> [!trace-covered]
> ✅ `CS-9-010` Quantity recognition — *02-order-processing.md §2.2 "quantity extraction"*

deadline recognition

> [!trace-covered]
> ✅ `CS-9-011` Deadline recognition — *02-order-processing.md §2.2 "deadline extraction"*

---

## 9.3 Confirmation and Feasibility

the system may send automatic confirmation to the client

> [!trace-partial]
> ⚠️ `CS-9-012` Automatic confirmation — may send (optional) — *03-confirmation.md §1* — spec says "sends" not "may send" — optionality not reflected

confirmation must consider wood stock levels, CNC capacity, finishing time, and delivery schedule

> [!trace-covered]
> ✅ `CS-9-013` Confirmation: wood stock consideration — *03-confirmation.md §2.1*

> [!trace-covered]
> ✅ `CS-9-014` Confirmation: CNC capacity consideration — *03-confirmation.md §2.2*

> [!trace-partial]
> ⚠️ `CS-9-015` Confirmation: finishing time consideration — *03-confirmation.md §2.3* — only lacquering mentioned, staining and oiling not covered

> [!trace-covered]
> ✅ `CS-9-016` Confirmation: delivery schedule consideration — *03-confirmation.md §2.4*

when raw material is in stock, immediate confirmation can be given

> [!trace-covered]
> ✅ `CS-9-017` Stock-based immediate confirmation — *03-confirmation.md §3*

when deadline cannot be met: propose alternative date or send warning to client

> [!trace-covered]
> ✅ `CS-9-018` Alternative date proposal — *03-confirmation.md §4.1*

> [!trace-partial]
> ⚠️ `CS-9-019` Warning sent to client — *03-confirmation.md §4.2* — spec mentions only internal alert, client-facing notification not specified

request project manager approval when needed

> [!trace-covered]
> ✅ `CS-9-020` Project manager approval — *03-confirmation.md §5*

> [!trace-missing]
> ⬜ `CS-9-021` Decision logic: when is project manager approval needed *(implicit)* — Not verified

---

## 9.4 Communication Scope

system will NOT have a general communication module

> [!trace-covered]
> ✅ `CS-9-022` No general communication module — *00-overview.md §3 scope exclusions*

not a goal: general CRM communication or general email template editing

> [!trace-covered]
> ✅ `CS-9-023` Not a goal: general CRM communication — *00-overview.md §3*

> [!trace-missing]
> ⬜ `CS-9-024` Not a goal: general email template editing — Not verified

communication is exclusively tied to order intake and order fulfillment

> [!trace-covered]
> ✅ `CS-9-025` Communication scope: order intake + fulfillment — *04-communication.md §1*

permitted communication topics: order intake, order clarification, order confirmation, production deadline, feasibility, delivery/pickup coordination, status communication, proforma/advance/billing

> [!trace-covered]
> ✅ `CS-9-026` Topic: order intake — *04-communication.md §2.1*

> [!trace-covered]
> ✅ `CS-9-027` Topic: order clarification (material, color, dimensions) — *04-communication.md §2.2*

> [!trace-covered]
> ✅ `CS-9-028` Topic: order confirmation — *04-communication.md §2.3*

> [!trace-covered]
> ✅ `CS-9-029` Topic: production deadline — *04-communication.md §2.4*

> [!trace-partial]
> ⚠️ `CS-9-030` Topic: feasibility (materials/production/finishing) — *04-communication.md §2.5* — only materials and production handled separately, finishing not

> [!trace-covered]
> ✅ `CS-9-031` Topic: delivery/pickup coordination — *04-communication.md §2.6*

> [!trace-covered]
> ✅ `CS-9-032` Topic: status communication — *04-communication.md §2.7*

> [!trace-partial]
> ⚠️ `CS-9-033` Topic: proforma/advance/billing — *04-communication.md §2.8* — proforma and billing covered, advance payment not specified

---

## 9.5 Client Management

client management is not a classic sales CRM

> [!trace-covered]
> ✅ `CS-9-034` Not a sales CRM — *05-client-management.md §1*

no AI feature needed: next step suggestion, general email draft generation, or proactive sales suggestions

> [!trace-covered]
> ✅ `CS-9-035` AI exclusion: next step suggestion — *05-client-management.md §2 scope*

> [!trace-covered]
> ✅ `CS-9-036` AI exclusion: general email draft generation — *05-client-management.md §2 scope*

> [!trace-missing]
> ⬜ `CS-9-037` AI exclusion: proactive sales suggestions — Not verified

client data management scope: order intake, production tracking, delivery, and partner relationship management

> [!trace-covered]
> ✅ `CS-9-038` Client scope: order intake — *05-client-management.md §3*

> [!trace-covered]
> ✅ `CS-9-039` Client scope: production tracking — *05-client-management.md §3*

> [!trace-partial]
> ⚠️ `CS-9-040` Client scope: delivery — *05-client-management.md §3* — spec uses "shipping", does not differentiate delivery vs. pickup

> [!trace-missing]
> ⬜ `CS-9-041` Client scope: partner relationship management — Not verified
