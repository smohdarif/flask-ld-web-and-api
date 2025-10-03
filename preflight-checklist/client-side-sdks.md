+++
title = "Client-side and Mobile SDKs"
weight = 3
+++

The following items apply to all client-side and mobile SDKs.

## Application does not block on identify

Calls to identify return a promise that resolves when flags for the new context have been retrieved. In many applications, using the existing flags is acceptable and preferable to blocking in a situation where flags can not be retrieved.

### Implementation

- **MAY** Continue without waiting for the promise to resolve
- **SHOULD** Implement a timeout when identify is called

### Validation

- **Pass** The application is able to function after calling identify while the SDK domains are blocked (clientsdk.launchdarkly/app.launchdarkly.com)


## Application does not rapidly call identify

In mobile and client-side SDKs, identify results in a network call to the evaluation endpoint. Calls to identify should be made sparingly. For example:

**Good times to call identify:**
- During a state transition (from unauthenticated to authenticated)
- When a attribute of a context changes 
- When switching users

**Bad times to call identify:**
- To implement a `currentTime` attribute in your context that updates every second
- Implementing contexts that appear multiple times in a page such as per-product

