"""Grader v3: an oracle_map entry's operation, stated in plain words, as a fixed plan over one mart.

The spec asks for "the table and column (or SQL view) that answers it" (P1/P2 prompt.md:41). An entry that
names a table and its columns and says in words how they answer the check (`how: sum net_obligations by
agency_code`, `note: Count the rows with net_obligations below zero.`) is such an answer (owner, 2026-10-24:
"opinion mismatches, not failures"). This module reads those words with a fixed grammar and no model, and
the plan it builds is applied to the mart's rows before the check reads them (grade.py). The same grammar
applies to every arm.

What the grammar knows (every column it names must be a column of the entry's mart, matched without case):

- filter: `where C <op> V`, `filter C to V`, `filter C = V`, `keep the rows whose/where ...`, `rows where ...`,
  `C is true|false`, a bare boolean `C`, `C below zero`, `C is negative`, `C is V`; several joined by `and`.
  `<op>` is one of = == != <> < <= > >=. `C is in the replayed hour` keeps every row: the replay is the hour
  the prompt asks about (check 5: "for the replayed hour").
- aggregate: `sum C`, `sum(C)`, `total C`, `count rows`, `count(*)`, `count the rows`, with `where ...` after a
  count; several joined by `and`.
- group: `by C [and C]`, `grouped by ...`, `group by ...`, `per C`, `for each C`, or a `group_by:` key.
- divide: `divide by C`: the one summed measure of each group divided by C, which must hold one value per
  group. Exact decimal arithmetic, as the answer key's.
- count of groups: `count the <things> whose sum is below zero` (or `< 0`, `negative`) after a group and a sum.
- recognised, not applied: `order by ...`, `sort by ...`, `asc`, `desc`, `nulls last`, `take ten`, `top 10`,
  `first ten rows`, `limit 10`: ranking and cutting are the check's own (checks 2 and 6 rank the whole result
  themselves, as they always have); `over all ...` and `over the ... months` (the sum's extent, which the
  grouping already says); `read the rows directly`, `one row per ...`, `... are excluded` (a description of
  the mart, not an operation).

A clause that names a column of the mart, a marts table, a dotted name (`dim_wiki.dbname`) or an operation word
(sum, count, divide, filter, where, join, union, group, having) and that the grammar cannot read makes the
entry UNRESOLVED: the check fails with the clause quoted in its log, the same way for every arm (owner,
2026-10-24: "I'm not going to review these."). A clause with none of those is commentary and is skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, DivisionByZero, InvalidOperation

# The keys an entry states its operation in (the spec fixes no format). A query key is read before these.
PROSE_KEYS = ("how", "aggregation", "aggregate", "operation", "op", "rows", "filter", "where", "note",
              "notes", "group_by", "groupby")
OP_WORDS = ("sum", "count", "divide", "filter", "where", "join", "joins", "union", "group", "having", "average",
            "avg", "mean", "max", "min", "distinct")
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
           "ten": 10, "twenty": 20}


class Unresolved(Exception):
    """The entry states an operation the grammar cannot read."""


@dataclass
class Plan:
    filters: list[tuple[str, str, object]] = field(default_factory=list)   # (column, op, value)
    aggregates: list[tuple[str, str | None]] = field(default_factory=list)  # ("sum", col) or ("count", None)
    group: list[str] = field(default_factory=list)
    divide: str | None = None
    count_groups_below_zero: bool = False
    noted: list[str] = field(default_factory=list)  # clauses recognised and not applied (order, limit, ...)

    def empty(self) -> bool:
        return not (self.filters or self.aggregates or self.group or self.divide or self.count_groups_below_zero)

    def describe(self) -> str:
        parts = []
        if self.filters:
            parts.append("filter " + " and ".join(f"{c} {o} {_literal(v)}" for c, o, v in self.filters))
        if self.aggregates:
            parts.append(", ".join(f"{f}({c or ('*' if f == 'count' else 'the named measure')})"
                                   for f, c in self.aggregates))
        if self.group:
            parts.append("by " + ", ".join(self.group))
        if self.divide:
            parts.append(f"divided by {self.divide}")
        if self.count_groups_below_zero:
            parts.append("count of groups whose sum < 0")
        return "; ".join(parts) or "rows as published"


def prose(entry: dict) -> list[tuple[str, str]]:
    """(key, text) for each operation statement in the entry, in PROSE_KEYS order."""
    lower = {str(k).lower(): v for k, v in entry.items()}
    out = []
    for key in PROSE_KEYS:
        value = lower.get(key)
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value)
        if isinstance(value, (str, int, float)) and str(value).strip():
            text = str(value).strip()
            if key in ("group_by", "groupby"):
                text = "" if text.lower() in ("none", "-", "") else "by " + text
            elif key in ("filter", "where", "rows"):
                text = text if re.match(r"\s*(where|filter|keep|rows)\b", text, re.I) else "where " + text
            if text:
                out.append((key, text))
    return out


_PAREN = re.compile(r"\([^()]*\)")
_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"


def _normalize(text: str) -> str:
    text = re.sub(r"\bcount\s*\(\s*(\*|[A-Za-z_][\w.]*)\s*\)", "count rows", text, flags=re.I)
    text = re.sub(r"\b(sum|total)\s*\(\s*([A-Za-z_]\w*)\s*\)", r"\1 \2", text, flags=re.I)
    while _PAREN.search(text):
        text = _PAREN.sub(" ", text)  # a parenthesis is commentary: "(the county rows)", "(July 1, 2024 basis)"
    return re.sub(r"\s+", " ", text).strip()


def _clauses(text: str) -> list[str]:
    text = _normalize(text)
    parts = re.split(r";|\.(?=\s|$)|\bthen\b|,|\s+and\s+(?=(?:sort|order|take|divide|filter|keep|limit|return|"
                     r"count|sum|total|where|compare)\b)", text, flags=re.I)
    return [p.strip(" .:-") for p in parts if p and p.strip(" .:-")]


class Grammar:
    def __init__(self, columns: list[str], marts: list[str]):
        self.columns = {c.lower(): c for c in columns}
        self.marts = {m.lower() for m in marts}

    # ------------------------------------------------------------------ pieces

    def col(self, word: str) -> str | None:
        return self.columns.get(word.strip("`\"'").lower())

    def cols(self, text: str) -> list[str] | None:
        """`a and b`, `a, b`, `a`: every word a column, else None."""
        words = [w for w in re.split(r"\s*(?:,|\band\b)\s*", text.strip()) if w]
        found = [self.col(w) for w in words]
        return found if words and all(found) else None

    @staticmethod
    def value(text: str):
        t = text.strip()
        m = re.fullmatch(r"(?:date\s+)?'([^']*)'|\"([^\"]*)\"", t, re.I)
        if m:
            return m.group(1) if m.group(1) is not None else m.group(2)
        if re.fullmatch(r"-?\d+(?:\.\d+)?", t):
            return Decimal(t)
        if t.lower() in ("true", "false"):
            return t.lower() == "true"
        if t.lower() in ("zero",):
            return Decimal(0)
        if re.fullmatch(r"[\w.:/-]+", t):
            return t  # en.wikipedia.org, enwiki, 2024-07-01
        return None

    def cond(self, text: str, bare: bool = True) -> list[tuple[str, str, object]] | None:
        """One condition or several joined by `and`; [] for `C is in the replayed hour`; None if unreadable."""
        out = []
        for part in re.split(r"\s+and\s+", text.strip()):
            part = part.strip()
            m = re.fullmatch(rf"({_IDENT})\s*(==|=|!=|<>|<=|>=|<|>)\s*(.+)", part)
            if m and self.col(m.group(1)) and self.value(m.group(3)) is not None:
                op = {"==": "=", "<>": "!="}.get(m.group(2), m.group(2))
                out.append((self.col(m.group(1)), op, self.value(m.group(3))))
                continue
            m = re.fullmatch(rf"({_IDENT})\s+(?:is\s+)?(?:in|within)\s+the\s+replayed\s+hour", part, re.I)
            if m and self.col(m.group(1)):
                continue  # the replay is the hour (prompt check 5)
            m = re.fullmatch(rf"({_IDENT})\s+(?:is\s+)?(?:below|under|less\s+than)\s+(?:zero|0)", part, re.I) or \
                re.fullmatch(rf"({_IDENT})\s+is\s+negative", part, re.I)
            if m and self.col(m.group(1)):
                out.append((self.col(m.group(1)), "<", Decimal(0)))
                continue
            m = re.fullmatch(rf"({_IDENT})\s+is\s+(true|false)", part, re.I)
            if m and self.col(m.group(1)):
                out.append((self.col(m.group(1)), "=", m.group(2).lower() == "true"))
                continue
            m = re.fullmatch(rf"({_IDENT})\s+(?:is|to)\s+(.+)", part, re.I)
            if m and self.col(m.group(1)) and self.value(m.group(2)) is not None:
                out.append((self.col(m.group(1)), "=", self.value(m.group(2))))
                continue
            if bare and self.col(part):
                out.append((self.col(part), "=", True))  # a bare boolean column: "where is_net_negative"
                continue
            return None
        return out

    # ------------------------------------------------------------------ clauses

    def clause(self, c: str, plan: Plan) -> bool:
        """Apply one clause to `plan`; False when the grammar does not read it."""
        s = c.strip()
        low = s.lower()
        # recognised, not applied
        if re.fullmatch(r"(?:and\s+)?(?:order|sort|rank)(?:ed)?\s+(?:by\s+)?.+", low) or \
                re.fullmatch(rf"{_IDENT}\s+(?:asc|desc|ascending|descending)", low) or \
                re.fullmatch(r"(?:asc|desc|ascending|descending|nulls\s+(?:last|first))", low) or \
                re.fullmatch(r"(?:and\s+)?(?:take|keep|return|show|limit|select)?\s*(?:the\s+)?(?:first|top)?\s*"
                             r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twenty)(?:\s+rows)?", low) or \
                re.fullmatch(r"(?:take|keep|return|show)\s+(?:the\s+)?(?:first|top)\s+.*", low) or \
                re.fullmatch(r"read\s+the\s+rows(?:\s+directly)?", low) or \
                re.fullmatch(r"(?:.+\s+)?one\s+row\s+per\s+.+", low) or \
                re.fullmatch(r".+\s+(?:are|is)\s+excluded", low) or \
                re.fullmatch(r"(?:and\s+)?(?:compare|equals?|add\s+up|rolled\s+up)\b.*", low) or \
                re.fullmatch(r"(?:then\s+)?sum\s+(?:over\s+)?(?:the\s+|all\s+)?(?:states?|count(?:y|ies))"
                             r"(?:\s+totals?)?(?:\s+.*)?", low):
            if self._names_foreign(s, allow_columns=True):
                return False
            plan.noted.append(s)
            return True
        m = re.fullmatch(r"(.*?)\s*\bover\s+(.+)", s, re.I)
        if m:
            if self._names_foreign(m.group(2), allow_columns=True):
                return False
            plan.noted.append("over " + m.group(2))
            s, low = m.group(1).strip(), m.group(1).strip().lower()
            if not s:
                return True
        m = re.fullmatch(r"divide(?:\s+(?:it|that|this|the\s+result|the\s+sum))?\s+by\s+(\S+)", s, re.I)
        if m and self.col(m.group(1)):
            plan.divide = self.col(m.group(1))
            return True
        m = re.fullmatch(r"(?:count|counts)\s+the\s+\w+\s+whose\s+(?:sum|total)\s+is\s+(?:below\s+zero|negative|<\s*0)",
                         s, re.I)
        if m:
            plan.count_groups_below_zero = True
            return True
        m = re.fullmatch(r"(?:where|filter|only|keep\s+(?:the\s+)?rows\s+(?:where|whose|with)|rows\s+(?:where|whose|with))"
                         r"\s+(.+)", s, re.I)
        if m:
            got = self.cond(m.group(1))
            if got is None:
                return False
            plan.filters += got
            return True
        m = re.fullmatch(rf"(?:grouped\s+by|group\s+by|by|per|for\s+each)\s+(.+)", s, re.I)
        if m and self.cols(m.group(1)):
            return self._group(self.cols(m.group(1)), plan)
        m = re.fullmatch(rf"for\s+({_IDENT})\s+(\S+)", s, re.I)  # "for month_start 2024-09-01"
        if m and self.col(m.group(1)) and self.value(m.group(2)) is not None:
            plan.filters.append((self.col(m.group(1)), "=", self.value(m.group(2))))
            return True
        if self._aggregate(s, plan):
            return True
        got = self.cond(s, bare=False)  # a bare condition: "month_start = 2024-07-01", "grain = 'agency'"
        if got:
            plan.filters += got
            return True
        return False

    def _group(self, cols: list[str], plan: Plan) -> bool:
        if plan.group and plan.group != cols:
            return False  # two different groupings in one entry
        plan.group = cols
        return True

    def _aggregate(self, s: str, plan: Plan) -> bool:
        """`sum C [and count rows] [by G] [where COND]`, `count rows [where COND]`, `sum per G`."""
        m = re.fullmatch(r"(.+?)\s+(?:where|with|whose)\s+(.+)", s, re.I)
        rest, cond = (m.group(1), m.group(2)) if m else (s, None)
        m = re.fullmatch(r"(.+?)\s+(?:grouped\s+by|group\s+by|by|per|for\s+each)\s+(.+)", rest, re.I)
        head, group = (m.group(1), m.group(2)) if m else (rest, None)
        aggs = []
        for part in re.split(r"\s+and\s+", head.strip()):
            p = part.strip().lower()
            mm = re.fullmatch(r"(?:sum|total)(?:\s+of)?\s+(\S+)", p)
            if mm and self.col(mm.group(1)):
                aggs.append(("sum", self.col(mm.group(1))))
            elif re.fullmatch(r"(?:sum|total)", p) and group:
                aggs.append(("sum", None))  # "sum per award_key": the measure named in the entry's columns
            elif re.fullmatch(r"count(?:\s+(?:the|all))?(?:\s+(?:rows|records|\*))?", p):
                aggs.append(("count", None))
            else:
                return False
        if group is not None:
            cols = self.cols(group)
            if not cols or not self._group(cols, plan):
                return False
        if cond is not None:
            got = self.cond(cond)
            if got is None:
                return False
            plan.filters += got
        plan.aggregates += aggs
        return True

    def _names_foreign(self, text: str, allow_columns: bool = False) -> bool:
        """Whether text names another mart or a dotted name (a join the grammar does not do)."""
        for w in re.findall(r"[A-Za-z_][\w.]*", text):
            if "." in w.strip(".") and not re.fullmatch(r"[a-z]+\.(?:wikipedia|wiktionary|wikidata)\.org", w.lower()):
                return True
            if w.lower() in self.marts:
                return True
            if not allow_columns and self.col(w):
                return True
        return False

    def significant(self, clause: str) -> bool:
        """A clause the grammar must read: it names a column, a mart, a dotted name or an operation word."""
        for w in re.findall(r"[A-Za-z_][\w.]*", clause):
            lw = w.lower()
            if self.col(w) or lw in self.marts or lw in OP_WORDS:
                return True
            if "." in w.strip(".") and not re.fullmatch(r"[a-z]+\.(?:wikipedia|wiktionary|wikidata)\.org", lw):
                return True
        return False


def parse(entry: dict, columns: list[str], marts: list[str], named: list[str]) -> Plan | None:
    """The plan an entry's words state, or None when it states none. Raises Unresolved.

    `named`: the entry's own column list; a bare `sum` (`sum per award_key`) sums the one numeric column it
    names besides the group (resolved by grade.py from the values, see apply())."""
    texts = prose(entry)
    if not texts:
        return None
    g = Grammar(columns, marts)
    plan = Plan()
    for key, text in texts:
        for c in _clauses(text):
            if g.clause(c, plan):
                continue
            if g.significant(c):
                raise Unresolved(f"{key}: cannot read {c!r}")
            plan.noted.append(f"commentary: {c}")
    if plan.divide and len([a for a in plan.aggregates if a[0] == "sum"]) != 1:
        raise Unresolved(f"divide by {plan.divide} needs exactly one summed measure")
    if plan.count_groups_below_zero and not (plan.group and plan.aggregates):
        raise Unresolved("a count of groups whose sum is below zero needs a grouping and a sum")
    if plan.divide and not plan.group:
        raise Unresolved(f"divide by {plan.divide} needs a grouping")
    return plan


# ---------------------------------------------------------------------------------- applying a plan


def _literal(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, Decimal):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sql(plan: Plan, view: str, measure: str | None) -> tuple[str, list[str]]:
    """The DuckDB query for a plan over the mart `view`, and the names of its output columns.
    `measure`: the column a bare `sum` sums (grade.py picks it from the entry's named columns)."""
    where = " and ".join(f"{_q(c)} {o} {_literal(v)}" for c, o, v in plan.filters)
    base = f"select * from {_q(view)}" + (f" where {where}" if where else "")
    if not plan.aggregates and not plan.group:
        return base, []
    outs, names = [], []
    for g in plan.group:
        outs.append(_q(g)); names.append(g)
    for func, col in plan.aggregates:
        col = col or measure
        if func == "sum":
            if col is None:
                raise Unresolved("a bare sum with no measure column named")
            outs.append(f"sum({_q(col)}) as {_q('sum_' + col)}"); names.append("sum_" + col)
        else:
            outs.append("count(*) as row_count"); names.append("row_count")
    if plan.divide:
        outs.append(f"min({_q(plan.divide)}) as __den_min, max({_q(plan.divide)}) as __den_max")
        names += ["__den_min", "__den_max"]
    group = (" group by " + ", ".join(_q(g) for g in plan.group)) if plan.group else ""
    query = f"select {', '.join(outs)} from ({base}) t{group}"
    if plan.count_groups_below_zero:
        total = next(n for n in names if n.startswith("sum_"))
        return f"select count(*) as groups_below_zero from ({query}) g where {_q(total)} < 0", ["groups_below_zero"]
    return query, names


def divide_rows(plan: Plan, names: list[str], rows: list[tuple]) -> tuple[list[str], list[tuple]]:
    """Replace the summed measure by measure / divisor, exactly, per group. The divisor must hold one value per
    group (min = max); a null or zero divisor gives a null quotient, which the check skips."""
    if not plan.divide:
        return names, rows
    i_sum = next(i for i, n in enumerate(names) if n.startswith("sum_"))
    i_lo, i_hi = names.index("__den_min"), names.index("__den_max")
    keep = [i for i in range(len(names)) if i not in (i_sum, i_lo, i_hi)]
    out = []
    for r in rows:
        if r[i_lo] != r[i_hi]:
            raise Unresolved(f"divide by {plan.divide}: it holds more than one value in group "
                             f"{[r[i] for i in keep]!r}")
        try:
            q = None if r[i_sum] is None or r[i_lo] is None else Decimal(str(r[i_sum])) / Decimal(str(r[i_lo]))
        except (DivisionByZero, InvalidOperation):
            q = None
        out.append(tuple(r[i] for i in keep) + (q,))
    return [names[i] for i in keep] + [f"{names[i_sum]}_per_{plan.divide}"], out
