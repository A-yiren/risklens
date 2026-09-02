# RiskLens DESIGN.md

> Visual source of truth for RiskLens product UI. This is an original project design system informed by general patterns studied from the MIT-licensed `VoltAgent/awesome-design-md` collection. It must not be used to imitate any referenced brand one-to-one.

## 1. Product character

RiskLens should feel calm, trustworthy and understandable to an ordinary person facing a legal or contractual problem for the first time.

The primary user is an individual, not a lawyer. Lead with real-life goals such as “我要租房” and “我想检查合同”. Legal and technical depth remains available as a secondary expandable layer for lawyers and legal teams.

The interface must communicate four promises:

1. We ask before we assume.
2. “不确定” is a valid answer.
3. Important conclusions show their source and coverage boundary.
4. Generated documents are drafts, not declarations that legal review has passed.

## 2. Color roles

```text
brand-950       #102823  deep navigation background
brand-900       #15362f  primary dark surface
brand-800       #1e4b41  primary action
brand-700       #286253  primary hover
brand-100       #dcebe5  selected/soft brand surface
brand-50        #eef6f2  quiet brand surface
canvas          #f7f4ed  warm page background
surface         #ffffff  primary cards
surface-soft    #fbfaf6  secondary cards
ink             #1d2824  primary text
body            #4e5b56  body text
muted           #7c8581  explanatory text
hairline        #e2dfd6  card and section borders
accent          #c47a2c  restrained gold/amber for guidance
accent-soft     #fff1dc  questions and pending state
success         #2f7d61  confirmed state
success-soft    #e7f4ed  confirmed state background
danger          #b24b45  errors only
```

Rules:

- Deep green and warm cream are the identity. Do not replace them with generic technology blue.
- Gold is used for guidance and pending items, never as decoration everywhere.
- Red means a real error or destructive action, not an ordinary unconfirmed field.
- Use surface contrast and thin borders instead of heavy shadows.

## 3. Typography

- Product UI: system sans-serif, `PingFang SC`, `Microsoft YaHei`, sans-serif.
- Contract document preview: `Source Han Serif SC`, `Songti SC`, `SimSun`, serif.
- Page title: 30–36px desktop, weight 650, compact line height.
- Section title: 16–18px, weight 650.
- Body: 14–16px, line height 1.6.
- Helper text: no smaller than 12px on desktop.
- Avoid excessive English and uppercase labels in the ordinary-user flow.

## 4. Spacing and shape

- Base spacing unit: 4px.
- Common spacing: 8, 12, 16, 20, 24, 32, 40px.
- Inputs and primary buttons: at least 44px high.
- Button radius: 10–12px.
- Card radius: 16–20px.
- Status pills may use full radius.
- Desktop content maximum width: 1380px.

## 5. Core components

### Scenario card

Use plain-language goals: “我要租房”, “我要出租”, “我要检查已有合同”. Include a one-line explanation. Do not expose contract taxonomy as the first decision.

### Guided question card

One group of related questions at a time. Explain why the information is needed. Every extracted critical fact offers:

- 确认正确
- 修改
- 暂不确定

Never preselect “确认正确”.

### Fact checklist

Show progress as “已回答 X / N”, not as a fabricated accuracy score. Status values are:

- 已确认
- 暂不确定
- 待回答

“暂不确定” counts as answered but stays visible as a future contract placeholder.

### Trust explanation

Use ordinary language first. Terms such as RAG, embedding, reranker and agent orchestration must not appear in the main flow. Put professional details behind “查看依据与检查范围”.

## 6. Desktop contract workspace

- Persistent left navigation: 220–240px.
- Main work area: guided conversation and confirmation, flexible width.
- Right summary rail: 300–340px, sticky on desktop.
- Primary action remains close to the current question, not at the far page bottom.
- Keep only one dominant primary button per view.

## 7. Responsive behavior

- Desktop is implemented and reviewed first.
- Below 900px: remove persistent sidebar, stack summary after main content.
- Touch targets remain at least 44px.
- Never hide the “暂不确定” choice on mobile.

## 8. Do

- Start with a concrete real-life scenario.
- Use short questions and familiar words.
- Clearly label demo data and prototypes.
- Preserve the user’s original description separately from confirmed facts.
- Show why the system asks each important question.
- Let lawyers inspect sources without making ordinary users read technical details.

## 9. Do not

- Do not claim AI-extracted text is confirmed.
- Do not use “审核通过” when only automated checks ran.
- Do not show fake confidence percentages.
- Do not display dense legal forms before the user understands the task.
- Do not copy a named product’s colors, typography or brand identity one-to-one.
- Do not redesign unrelated RiskLens pages while a preview is under review.

## 10. Reference and attribution

General design-system structure and comparative study references:

- `VoltAgent/awesome-design-md`, locally cloned outside the RiskLens repository at `references/awesome-design-md`.
- Studied references: Notion (reading hierarchy), Intercom (conversational guidance), Wise (consumer clarity).
- RiskLens tokens, components, product rules and visual composition in this file are project-specific adaptations.
