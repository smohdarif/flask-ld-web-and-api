+++
title = "Using Flags"
weight = 6
+++

## Define context kinds and attributes

Choose context kinds/attributes that enable safe targeting, deterministic rollouts, and cross-service alignment.

### Implementation

- **MUST** Define context kinds (e.g., `user`, `organization`, `device`); use **multi-contexts** when both person and account matter.
- **MUST NOT** Derive context keys from PII, secrets or other sensitive data.
- **MUST** Mark sensitive attributes as private. _Context Keys_ can not be private
- **SHOULD** Use keys that are unique, opaque, and high-entropy
- **SHOULD** Document the source/type for all attributes; normalize formats (e.g., ISO country codes).
- **SHOULD** Provide shared mapping utilities to transform domain objects → LaunchDarkly contexts consistently across services.
- **SHOULD** Avoid targeting on sensitive information or secrets.


### Validation

- **Pass** if a 50/50 rollout yields **consistent allocations** across services for the same context.
- **Pass** if sample contexts evaluated in a harness match expected targets/segments.
- **Pass** if a PII audit finds no PII in keys and private attributes are redacted in events.
- **Pass** if applications create/define contexts consistently across services

---

## Define and document fallback strategy

Every flag must specify a safe fallback value that is used when the flag is unavailable.

### Implementation

- **MUST** Pass the fallback value as the last argument to `variation()`/`variationDetail()` with correct types.
- **MUST** Define a strategy for determining when fallback values should be audited and updated.
- **MUST** Implement automated tests to validate the application is able to function in an at most degraded state when flags are unavailable.

### Validation

- **Pass** if blocking SDK network causes the application to use the fallback path safely with **no errors**.

---

## Use `variation`/`variationDetail`, not `allFlags`/`allFlagsState` for evaluation

Direct evaluation emits accurate usage events required for flag statuses, experiments, and rollout tracking.

### Implementation

- **MUST** Call `variation()`/`variationDetail()` at the decision point
- **MUST NOT** Implement an additional layer of caching for calls to variation that would prevent accurate flag evaluation telemetry from being generated

### Validation

- **Pass** accurate flag evaluation data is shown in the Flag Monitoring dashboard

---

## Flags are evaluated only where a change of behavior is exposed

Evaluation events should only be generated when a change in behavior is exposed to the end user. This ensures that features such as experimentation and guarded rollouts function correctly.

### Implementation
- **MUST** Evaluate flags only when the value will be used
- **SHOULD** Evaluate flags as close to the decision point as possible
---

## The behavior changes are encapsulated and well-scoped

New vs. old logic should be isolated to ease future cleanup. A rule of thumb is never store the result of a boolean flags in a variable. This ensures that the behavior impacted by the flag is fully contained within the branches of the if statement.

### Implementation

- **SHOULD** Place new/old logic in separate functions/components; avoid mixed branches.
- **SHOULD** Evaluate the flag **inside** the decision point (`if`) to simplify later removal.

```tsx
// Example: evaluation scoped to the component
export function CheckoutPage() {
  if (ldClient.variation('enable-new-checkout', false)) {
    return <NewCheckoutComponent />;
  }
  return <LegacyCheckoutComponent />;
}
```

## Subscribe to flag changes

In applications with a UI or server-side use-cases where you need to respond to a flag change, you should use the update/change events in order to update the state of the application.

### Implementation

- **SHOULD** Use the subscription mechanism provided by the SDK to respond to updates. For more information, read [Subscribing to flag changes](https://launchdarkly.com/docs/sdk/features/flags#subscribing-to-flag-changes).
- **SHOULD** Unregister temporary handlers to avoid memory leaks.

### Validation

- **Pass** if the application responds to flag changes

---