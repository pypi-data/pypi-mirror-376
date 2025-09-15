# AICA Challenge 1 heuristic agent

The purpose of this agent is to serve as an inspiration for the authors of agents used in the AICA challenge. It also serves as a benchmark for evaluating the capabilities of AI agents.

A new version of the agent will be released with each new scenario. The agent will be able to solve all scenarios up to this point, so don't forget to update it whenever there is a new scenario published.

The agent is relatively straightforward:

- It scouts around itself, looking for potential targets.
- If it finds some, it checks whether there is something that can be remotely exploited.
- If it manages to get local access to a target, it analyzes what runs there.
- And if possible, it tries to exfiltrate some interesting data.

The code is relatively densely commented, so feel free to study the source if you get stuck or if some challenge-related code or idioms are not clear.

As usual, if you have any questions, feel free to contact us at aica-challenge@csirt.muni.cz.

Good luck! 