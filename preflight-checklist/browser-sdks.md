+++
title = "Browser SDKs"
weight = 4
+++

The following items apply only to the following SDKs:
- Javascript Client SDK 
- React SDK
- Vue SDK

## Send events only for variation

Avoid sending spurious events when allFlags is called. Sending evaluation events for allFlags will cause flags to never report as stale and may cause innacuracies in guarded rollouts and experiments with false impressions.

### Implementation

- **MUST** Set `sendEventsOnlyForVariation: true` in the SDK options

### Validation

- **Pass** calls to allFlags do not generate evaluation/summary events

## Bootstrapping strategy defined and implemented
Prevent UI flicker by rendering with known values before the initial handshake. For more information, read [Bootstrapping](https://launchdarkly.com/docs/sdk/features/bootstrapping).

### Implementation

- **SHOULD** Enable `bootstrap: 'localStorage'` or bootstrap from a server-side-SDK

### Validation

- **Pass** if under offline/slow network the first paint uses bootstrapped values (no visible "flash of wrong content").