# Security policy

## Scope

This repository contains a skill (instructions for AI agents) and its
tooling. It does not itself execute printer actions; the actions are
executed by the companion MCP servers (`mcp-cura`, `mcp-moonraker`) under
their own policy engines. A vulnerability here is **any content that lets an
agent bypass or weaken those gates**, including:

- skill text that instructs the agent to skip verification or self-approve,
- approval-flow flaws in documentation or examples (e.g. wrong wording that
  leads a client to treat a phrase as reusable),
- tooling (`scripts/`) that leaks approval state or writes outside the
  skill,
- examples/config snippets that disable safety defaults silently.

## Reporting

**Do not open a public issue for a safety or security fault.** Use GitHub's
private vulnerability reporting for this repository (Security → Advisories →
Report a vulnerability). If that is unavailable, contact the maintainer
listed in the repository profile.

Include: what an agent was able to do, with which skill/server versions,
the exact prompt if known, and the gate you expected to hold.

You will get an acknowledgement within 72 hours. Confirmed faults get a
CVE-style advisory in the affected server repo where applicable, plus a
patch and a `CHANGELOG.md` entry here.

## Hard truths

- The servers' policy engine is the enforcement layer. Filing a report
  here about a server bug is fine — it will be routed to `mcp-cura` /
  `mcp-moonraker`, which have their own security policies.
- "The agent disobeyed a gate because I told it it was my printer" is not a
  vulnerability. "The skill told the agent to disobey the gate" is.
- Printer hardware faults (fires, jammed axes) are emergencies for physical
  response first; report afterwards.

## Supported versions

| Version | Supported |
| --- | --- |
| latest `main` | yes |
| older tags | best effort, no backports promised |
