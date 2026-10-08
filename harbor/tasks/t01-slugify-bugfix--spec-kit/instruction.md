Use Spec Kit for this change. Run /speckit-specify with the issue below, then /speckit-plan, /speckit-tasks, /speckit-implement and /speckit-converge, in that order.

Issue:
`textkit.slugify` produces broken slugs.

- `slugify("Hello,  World!!")` returns `"hello---world--"`. It should return `"hello-world"`:
  words are runs of ASCII letters and digits, joined by exactly one hyphen, with no
  leading or trailing hyphen. Accented letters are transliterated (`"Crème brûlée"` → `"creme-brulee"`).
  Input with no letters or digits returns `""`.
- `max_length` currently cuts in the middle of a word and can leave a trailing hyphen.
  When the slug is longer than `max_length`, keep as many whole words as fit
  (`slugify("alpha beta gamma", max_length=12)` → `"alpha-beta"`). If even the first
  word is longer than `max_length`, cut that word to `max_length` characters
  (`slugify("supercalifragilistic", max_length=5)` → `"super"`).

Keep the public signature `slugify(text: str, max_length: int = 50) -> str`.
