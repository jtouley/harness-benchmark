---
name: review-loop
description: Do the task, then get an independent review from the reviewer agent and fix what it finds, until it approves. Use for every code change in this session.
---

# Review loop

1. Record the base commit: `git rev-parse HEAD`.
2. Do the task. Commit your change.
3. Call the Agent tool with `subagent_type: "reviewloop:reviewer"`. In the prompt, give the original request word for word, the base commit, and the repository path. Add nothing else: the reviewer must form its own view.
4. If the reviewer ends with `VERDICT: CHANGES`, fix each defect it reports, commit, and call the reviewer again with the same kind of prompt.
5. Stop when the reviewer says `VERDICT: APPROVE`, or after 3 reviews. Write in your summary how many reviews ran and what each found.
