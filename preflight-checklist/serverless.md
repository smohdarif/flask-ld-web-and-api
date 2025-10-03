+++
title = "Serverless functions"
weight = 5
+++

The following applies to SDKs running in serverless environments such as AWS Lambda, Azure Functions, and Google Cloud Functions. 

## Initialize the SDK outside of the handler

Many serverless environments will re-use execution environments for many invocations of the same function. This means that the SDK will need to be initialized outside of the handler to avoid duplicate connections and resource usage.

### Implementation

- **MUST** Initialize the SDK outside of the funciton handler
- **MUST NOT** Close the SDK in the handler

## Leverage LD Relay to reduce initialization latency

Serverless functions spawn many instances in order to handle concurrent requests. LD Relay can be deployed in order to reduce outgoing network connections, reduce outbound traffic and reduce initialization latency.

### Implementation

- **SHOULD** Deploy LD Relay in the same region as the serverless function
- **SHOULD** Configure LD Relay as an event forwarder and configure the SDK's event URI to point to LD Relay
- **SHOULD** Configure the SDK in proxy mode or daemon mode instead of connecting directly to LaunchDarkly
- **MAY** Call flush at the end of invocation to ensure all events are sent
- **MAY** Call flush/close when the runtime is being permanently terminated in environments that support this signal (Lamdba does provide this signal to functions themselves, only extensions)

Consider daemon mode if you have a particularly large initialization payload and only need a couple of flags for the function.

