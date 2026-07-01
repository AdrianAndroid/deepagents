---
name: save-question-doc
description: Use this skill for every user question in this project. Save each user prompt and the AI response to a Markdown file under the project root `doc/` directory with a timestamp and summary title.
---

# Save User Conversations to Project Docs

When working in this project, every time the user asks a question or gives a task, save the user's latest prompt and the AI response to the project root `doc/` directory.

## Required behavior

1. Ensure `doc/` exists at the project root.
2. Create a new Markdown file for each user prompt and response pair.
3. Use a timestamped filename with a concise kebab-case summary title:
   - `doc/YYYY-MM-DD-HHMMSS-summary-title.md`
4. The summary title must describe the user request, not just use `question`.
5. Write the original user prompt exactly as provided, plus the final AI response content.
6. If the response requires tool work, create or update the record after the final response is known.
7. Do this for every user prompt, unless the current task is only about fixing this skill itself.

## File template

```markdown
# <Summary Title>

- Time: YYYY-MM-DDTHH:MM:SS±HH:MM
- Project: deepagents

## Prompt

<original user prompt>

## AI Response

<final AI response>
```

## Notes

- Do not modify unrelated conversation records.
- It is acceptable to update the current prompt's record once to add the final AI response.
- Do not store secrets if the user explicitly asks not to save a prompt.
- Keep records local to the repository.
