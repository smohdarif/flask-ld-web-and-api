+++
title = "Initialization and Configuration"
weight = 2
+++

**Baseline Recommendations**

| Area                        | Recomendation    | Notes                                                                |
| --------------------------- | ---------------- | -------------------------------------------------------------------- |
| Client-side init timeout    | **100–500 ms**   | Don’t block UI; render with fallbacks or bootstrap.                  |
| Server-side init timeout    | **1–5 s**        | Keep short for startup; continue with fallback values after timeout. |
| Private attributes          | **Configured**   | Redact PII; consider `allAttributesPrivate` where appropriate.       |
| Javascript SDK Bootstrapping | **localStorage** | Reuse cached values between sessions.                               |

---

## SDK is initialized once as a singleton early in the application's lifecycle

**Applies to:** _All SDKs_

Prevent duplicate connections, conserve resources, and ensure consistent caching/telemetry.

### Implementation

- **MUST** Expose exactly one `ldClient` per process/tab via a shared module/DI container (root provider in React).
- **SHOULD** Make init idempotent: reuse the existing client if already created.
- **SHOULD** Close the client cleanly on shutdown; in serverless, create the client **outside** the handler for container reuse.
- **NICE-TO-HAVE** Emit a single startup log summarizing effective LD config (redacted).

### Validation

- **Pass** if metrics/inspector show **one** stream connection per process/tab.
- **Pass** if event volume and resource usage do not scale with repeated imports/renders.

---

## Application does not block on initialization

**Applies to:** _All SDKs_

A LaunchDarkly SDK is *initialized* when it connects to the service and is ready to evaluate flags. If `variation` is called before initialization, the SDK returns the **fallback** value you provide. **Do not block** the app while waiting for initialization. The SDK will continue connecting in the background. Calls to `variation` will always return most recent flag value.

### Implementation

- **MUST** Set an initialization timeout
  - Client-side: **100–500 ms**.
  - Server-side: **1–5 s**.
- **SHOULD** Implement a custom timeout when the SDK lacks a native parameter by racing init against a timer.
- **MAY** Subscribe to change events to proactively **respond** to flag updates.



### Validation
- **Pass** if with endpoints blocked the app renders using fallbacks (or bootstrapped values) within the configured timeout.
- **Pass** if restoring connectivity updates values without a restart.
  
**How to emulate:**
  - Point streaming/base/polling URIs to an invalid host, or
  - In browsers, block `clientstream.launchdarkly.com`, `clientsdk.launchdarkly.com`, and/or `app.launchdarkly.com` in [DevTools](/sdk/chrome-block-domain.png). 

---

## SDK configuration integrated with existing configuration/secrets management

**Applies to:** _All SDKs_

Use your existing configuration pipeline so LD settings are centrally managed and consistent across environments. Avoid requiring code changes setting common SDK options.

### Implementation

- **MUST** Load SDK credentials from existing configuration/secrets management system.
- **MUST NOT** Expose the server-side SDK Key to client applications 
- **SHOULD** Use configuration management system to set common SDK configuration options such as:
  - HTTP Proxy settings
  - Log verbosity
  - Enabling/disabling events (integration testing/load testing environments)
  - Private attribute

### Validation

- **Pass** if rotating the SDK key in the vault results in successful rollout and the old key is revoked.
- **Pass** if a repository scan finds **no** SDK keys or environment IDs committed.
- **Pass** if startup logs (redacted) show expected config per environment and egress connectivity succeeds (200/OK or open stream).

---

## Bootstrapping strategy defined and implemented
**Applies to:** _JS Client-Side SDK in browsers_, _React SDK_, _Vue SDK_

Prevent UI flicker by rendering with known values before the initial handshake.

### Implementation

- **SHOULD** Enable `bootstrap: 'localStorage'` for SPAs/PWAs to reuse cached values between sessions.
- **SHOULD** For SSR or static HTML, embed a server-generated flags JSON and pass to the client SDK at init.
- **MUST** Document which strategy each app uses and when caches expire.
- **SHOULD** Reconcile bootstrapped values with live updates and re-render when differences appear.

### Validation

- **Pass** if under offline/slow network the first paint uses bootstrapped values (no visible "flash of wrong content").
- **Pass** if clearing storage falls back to safe defaults and live updates correct the UI on reconnect.
- **Pass** if evaluations are recorded after handshake (visible in Events/exports).
