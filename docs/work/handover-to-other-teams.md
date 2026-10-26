# Handing the system to teams that are not mine

**Three more product divisions (lash, cosmetics and appliances) run the forecasting engine now. With nails, 15+ people in the purchasing and supply chain teams of all four run it weekly on their own accounts.** They configure it by editing a plain-language rule file, not by rebuilding it, and none of it depends on me being there.

[Why this is the result that matters](#why-this-is-the-result-that-matters) · [What made it portable](#what-made-it-portable) · [How each team was brought on](#how-each-team-was-brought-on) · [What I cannot show](#what-i-cannot-show)

## Why this is the result that matters

A tool built inside a company is easy to judge by what it can do and hard to judge by what it is doing. Most of them are working the day they are demonstrated and unused six months later.

So the result I would put ahead of the accuracy number is that teams I do not sit with open this every week, on data that is not mine, and that the people who built it stepped back without the thing stopping.

Four things describe that, and all four are plain facts rather than estimates: **which teams**, **how many people**, **how often**, and **whether the builder still runs it**. The last one is the one I would ask about first if someone showed me their own internal tool.

## What made it portable

The engine was not written as one program with our accounts inside it. Three layers are separate, and only the top one is ours:

- **Rules in a plain-language file.** Thresholds, category knowledge, the conditions for raising or cutting. A planner edits this. There is no code in it.
- **Agent definitions.** Each agent does one job. A team takes the ones it needs, adjusts them for its category, or adds its own.
- **Connectors and generators.** Point these at another team's tables, point-of-sale and customers.

As a result, **a team changes what it needs without coming back to me, and without waiting for a release.** What would otherwise be a months-long rebuild is days of configuration.

It also means the thing survives me. A tool that only one person can change has an end date: the day that person moves on.

## How each team was brought on

Sharing the files was not enough on its own, so each team went through the same four steps:

1. **Environment** — the agent structure stood up inside their own workspace, so it runs where they work.
2. **Porting** — connectors, rule files and agent definitions pointed at their data rather than ours.
3. **Configuration** — access, run cadence, and the output formats they actually send on.
4. **Transition** — working sessions, then follow-through until they ran it without me in the room.

The fourth step is the one that decides whether the first three were worth doing.

## The strongest evidence is not a number

Requests come back. The people using it ask for changes, and those changes get made. Nobody asks for changes to a tool they have stopped using.

That is also the argument for writing judgment into a file rather than keeping it in a head: a rule in one file can be challenged and changed by the person it affects, and a rule in someone's head cannot.

## What I cannot show

**Whether their forecasts got better.** I do not own those accounts and I do not measure them. What I can say is what is verifiable from where I sit: which teams took it, how many people run it, how often, that they configure it themselves, and that I am not the one running it.

The system itself was co-built, and the direction came from our manager. The rollout I led: I set up each team's environment, connected it to the team's own data, and ran the training sessions until each team ran it on its own.
