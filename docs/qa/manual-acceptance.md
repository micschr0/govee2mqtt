# Manual acceptance handoff

Use this handoff for checks requiring real Home Assistant, MQTT or device
observations. Copy the template into the ticket's acceptance report and link it
from the ticket and PR. Keep automated evidence and physical acceptance separate.
An acknowledgment, mock response, MQTT publication or last-sent value cannot
stand in for the owner's physical observation.

## Prepare before requesting owner action

Workers finish all independent implementation, automated checks, redacted evidence
capture and report preparation first. Supply numbered actions, expected results,
safe restoration steps and the exact remaining observations. Name the repository
owner as the physical operator and agree a hardware/test window before any live
device or network operation. This document grants no release or production access.

Use disposable fixtures for automated checks. Keep credentials, tokens, connection
details, device identifiers and runner artifacts out of the public repository.
Use stable redacted evidence IDs; record their authorized private location outside
public Git. Inspect logs and captures before sharing sanitized excerpts. A private
reference must describe the evidence and who can review it without exposing access
details. Unavailable evidence is a limitation, not proof.

## Decisions

Apply these statuses per requirement and per evidence type:

| Status | Meaning | Consequence |
| --- | --- | --- |
| pending | Action or required evidence has not been supplied | Name the owner and remaining action; a pending mandatory observation prevents overall acceptance. |
| pass | The expected result was observed on the identified build | Cite evidence for that specific result and its scope. |
| fail | Execution produced a result contrary to the expectation | Retain the failure and report the affected requirement; do not imply support. |
| inconclusive | Execution occurred but cannot settle the expectation | Explain uncertainty, missing evidence and the next discriminating check. |

Technical completion means the independent work and handoff are ready; it does
not mean physical acceptance passed. For support acceptance, all mandatory checks
must pass. Optional checks may be omitted only with a written applicability
rationale; do not silently relabel a mandatory check optional to close a ticket.
Leave hardware acceptance open while mandatory observations are pending.

An investigation may finish with an owner-observed unsupported or inconclusive
capability when its required investigative actions have been executed and
documented. Record investigation completion separately from support acceptance.
An observed failure can establish an unsupported capability; an ambiguous response
cannot. Neither outcome establishes support or authorizes speculative controls.

## Evidence applicability after changes

Keep original results, failures, dates and evidence immutable; append a new run
or applicability assessment rather than rewriting historical outcomes. A historical
pass does not automatically apply to the current build.

For every new candidate SHA, write which changes could affect each tested behavior.
Changes to command encoding, state handling, startup, dependencies, configuration
or packaging may invalidate the corresponding checks. Mark affected results pending
and perform targeted revalidation against the new SHA/artifact before accepting
them. Include relevant device, firmware and environment changes in the assessment.
Keep unaffected results only with a written rationale identifying both SHAs, the
reviewed change scope, retained evidence IDs and why the behavior is unchanged.
Unrelated changes do not automatically require every physical test to repeat.
If applicability is uncertain, record it as inconclusive and request targeted
revalidation. Never silently carry forward an old result as a fresh execution.

## Copyable report

All placeholders start pending. Add one action and evidence record per check;
do not prefill observations from expected results.

```markdown
# Acceptance report: <issue / requirement IDs>

## Identity and prerequisites

- Report ID / revision: <ID>
- Tested full commit SHA / source tree: <SHA; clean or dirty; patch identity if dirty>
- Artifact: <binary/image/package version and digest; build ID; source SHA>
- Model / firmware: <exact model, hardware variant and firmware>
- Environment: <controller OS/architecture; bridge version; HA Core/Supervisor;
  MQTT broker daemon and add-on versions; container/runtime versions if relevant>
- Relevant settings: <LAN enabled; credential presence/absence, never values;
  HTTP opt-in state; isolation scope; redacted device alias>
- Operator / repository owner confirmation: <name; confirmation reference or pending>
- Date / timezone / test window: <ISO date/time and timezone or pending>
- Prerequisites / dependencies: <issue IDs; hardware availability; safe test window>
- Original evidence: <historical report IDs/commits; retain their original scope>

## Numbered actions

| Step / requirement | Mandatory? / applicability rationale | Exact action and inputs | Expected result | Observed result | Status | Evidence IDs |
| --- | --- | --- | --- | --- | --- | --- |
| 1 / <req> | yes | <bounded action> | <observable expectation> | pending | pending | pending |
| 2 / <req> | yes | <next action> | <observable expectation> | pending | pending | pending |

## Separate evidence records (repeat for each step)

- Step / requirement: <ID>
- Automated protocol result: <pending/pass/fail/inconclusive; exact command;
  fixture/simulation or real endpoint; replies/acknowledgments; evidence IDs>
- Actual device readback: <pending/pass/fail/inconclusive; query, transport,
  timestamp, returned value and evidence IDs; say unavailable if unsupported>
- Last-sent values: <command, value, target zone and timestamp; evidence IDs;
  explicitly identify cached/optimistic state; never label it actual readback>
- Physical owner observation: <pending/pass/fail/inconclusive; operator, time,
  actual physical effect on each relevant zone and owner confirmation reference>
- Expected versus observed / limitations: <differences; what this cannot prove>
- Redacted evidence index: <ID, description, tested SHA/artifact, timestamp,
  sanitized excerpt or access-controlled reference and authorized reviewer>

## Isolation and restoration

1. Preconditions and original settings: <record without secrets>
2. Isolation: <owner-approved steps for controller AND device; verification method>
3. Bounded failure/test action: <duration, retry limit and stop condition>
4. Restoration: <restore original network/settings; verify connectivity and control>

- Actual restoration result / evidence / operator: pending

## Applicability to candidate build

- Previous tested SHA/artifact and new candidate SHA/artifact: <identities>
- Reviewed changes and affected requirements: <scope and reasoning>
- Retained evidence IDs and written rationale for each: <why still applicable>
- Invalidated evidence IDs / required targeted revalidation: <checks; new SHA>
- Revalidation results / evidence: pending

## Decision and remaining work

- Technical completion: pending <independent checks and handoff readiness>
- Physical acceptance: pending <per mandatory requirement; owner confirmation>
- Capability matrix: <function/zone; verified/unsupported/inconclusive;
  pending until observed; supporting evidence IDs>
- Investigation completion (if applicable): pending <actions executed and conclusion>
- Overall support acceptance: pending <rationale covering every mandatory check>
- Pending/failed/inconclusive requirements: <IDs; reason; owner; exact next action>
- Owner request: <only the observations still requiring hardware; agreed window>
```

Actual device readback is a device-originated value with provenance, not an echo
of a send or an optimistic cache. It still does not prove the visible physical
effect. When readback is unavailable, say so and retain the physical check.

## Apply to current hardware tickets

These are handoff instructions, not executed tests or additional dependencies.
Keep each ticket's existing ACs, dependencies and historical original evidence.

| Ticket | Required handoff scope | Initial physical status |
| --- | --- | --- |
| [#5: LAN without cloud](https://github.com/micschr0/govee2mqtt/issues/5) | LAN protocol fixtures; owner on/off, brightness and supported color/temperature; verified controller and lamp internet isolation; offline bridge restart; safe restoration. Preserve dependency #1. | pending |
| [#6: cloud recovery](https://github.com/micschr0/govee2mqtt/issues/6) | DNS/connectivity and HTTP 503 fixtures; three bounded outage/recovery cycles and retry/redaction results; owner LAN response during failure and after recovery; restoration. Preserve dependency #1. | pending |
| [#10: H60C1 zones](https://github.com/micschr0/govee2mqtt/issues/10) | Protocol supplied by #3; H60C1 firmware 1.01.27 (record actual firmware); independent dedicated bottom white and side RGB; physical effects on both zones; offline lamp/controller restarts, initialization/persistence and capability matrix linked to #3. Unresolved dedicated LED identity stays inconclusive. Preserve dependency #3. | pending |

For #5 and #6, pending physical checks prevent acceptance. For #10, executed
unsupported/inconclusive findings can complete the investigation under its ACs,
but unexecuted mandatory steps cannot. RGB-mixed white and other-model commands
do not establish H60C1 dedicated-white support.

The [historical test matrix](../security/TEST-MATRIX.md) remains a record of its
original builds and observations. Link new reports alongside it; do not convert
its local or simulated results into current hardware acceptance.
