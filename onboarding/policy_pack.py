"""Bounded policy detector. Patterns are the SAD table, not arbitrary paraphrases."""

import unicodedata


PASSAGES = {
    "P1": (
        "The new hire acknowledges the written policies at least two business days "
        "before the start date. Late acknowledgment is recorded as late; completion "
        "remains valid after a start-date change."
    ),
    "P2": (
        "IT provides an assigned laptop or approved loaner by the start date. "
        "IT must explicitly confirm availability and a ready date; a same-day ready "
        "date means ready for the start of work. Confirmation reserves the device "
        "from that date until onboarding completes unless revoked. A possibility or "
        "delivery estimate is not confirmation. Other tasks continue while equipment "
        "is unresolved."
    ),
    "P3": (
        "The manager confirms a first-day meeting for the current start date. "
        "A changed date requires reconfirmation unless the meeting has already been held."
    ),
    "P4": (
        "A Customer Support Representative at the Austin office completes "
        "customer-support tools orientation within five business days after starting. "
        "The manager owns scheduling and completion. This demonstration does not make "
        "equipment a prerequisite for assigning or scheduling training."
    ),
}

RETRIEVAL = {
    "P1": ("acknowledgment", "acknowledge", "acknowledges"),
    "P2": ("laptop", "loaner", "equipment"),
    "P3": ("meeting",),
    "P4": ("orientation", "training", "prerequisite"),
}

_REWRITES = {
    "dont": "do",
    "doesnt": "does",
    "isnt": "is",
    "arent": "are",
    "cant": "can",
    "wont": "will",
}
_DELETE = {"no", "not", "never"}
_APOSTROPHES = ("\u0027", "\u2018", "\u2019", "\u0060")
_OPENERS = {
    "does",
    "do",
    "is",
    "are",
    "can",
    "could",
    "should",
    "what",
    "when",
    "whether",
    "will",
    "who",
    "which",
    "how",
    "if",
    "must",
    "why",
}


def _phrase(text: str) -> tuple[str, ...]:
    return tuple(text.split())


def _pattern(*parts: str) -> tuple[tuple[str, ...], ...]:
    return tuple(_phrase(part) for part in parts)


_PACK = (
    {
        "id": "P1-due",
        "passage": "P1",
        "patterns": (
            _pattern("how many business days", "acknowledge"),
            _pattern("how many business days", "acknowledges"),
            _pattern("acknowledge", "before the start"),
            _pattern("acknowledges", "before the start"),
            _pattern("acknowledgment", "two business days"),
            _pattern("acknowledgment due"),
        ),
        "must_not": (_phrase("late"),),
    },
    {
        "id": "P1-late",
        "passage": "P1",
        "patterns": (
            _pattern("late acknowledgment"),
            _pattern("acknowledged late"),
            _pattern("acknowledgment", "remains valid"),
            _pattern("acknowledgment", "still valid"),
            _pattern("acknowledgment", "start date change"),
            _pattern("acknowledgment", "start date changes"),
        ),
        "must_not": (
            _phrase("first day meeting"),
            _phrase("orientation"),
            _phrase("loaner"),
        ),
    },
    {
        "id": "P2-provide",
        "passage": "P2",
        "patterns": (
            _pattern("approved loaner"),
            _pattern("provide", "loaner"),
            _pattern("provides", "loaner"),
            _pattern("assigned laptop", "loaner"),
            _pattern("provide", "laptop"),
            _pattern("provides", "laptop"),
        ),
        "must_not": (
            _phrase("confirm the laptop"),
            _phrase("reserve a loaner"),
            _phrase("reserve the laptop"),
            _phrase("prerequisite"),
        ),
    },
    {
        "id": "P2-confirm",
        "passage": "P2",
        "patterns": (
            _pattern("possibility", "confirm"),
            _pattern("estimate", "confirm"),
            _pattern("estimate", "confirmation"),
            _pattern("delivery estimate", "confirm"),
            _pattern("delivery estimate", "confirmation"),
            _pattern("explicit ready date"),
            _pattern("what confirmation requires"),
            _pattern("what does confirmation require"),
            _pattern("same day ready date"),
            _pattern("ready date", "confirm"),
            _pattern("ready date", "confirmation"),
        ),
        "must_not": (
            _phrase("for this hire"),
            _phrase("for this case"),
            _phrase("for riley"),
            _phrase("for jordan"),
        ),
    },
    {
        "id": "P2-continue",
        "passage": "P2",
        "patterns": (
            _pattern("other tasks", "continue", "equipment"),
            _pattern("tasks continue", "equipment"),
            _pattern("while equipment is unresolved"),
            _pattern("equipment is unresolved"),
        ),
        "must_not": (_phrase("prerequisite"),),
    },
    {
        "id": "P3-meeting",
        "passage": "P3",
        "patterns": (
            _pattern("first day meeting"),
            _pattern("manager", "confirm", "meeting"),
            _pattern("manager", "confirms", "meeting"),
        ),
        "must_not": (
            _phrase("reconfirm"),
            _phrase("reconfirmation"),
            _phrase("confirmed again"),
            _phrase("changed start"),
            _phrase("start date change"),
            _phrase("start date changes"),
            _phrase("new start date"),
        ),
    },
    {
        "id": "P3-reconfirm",
        "passage": "P3",
        "patterns": (
            _pattern("reconfirm"),
            _pattern("reconfirmation"),
            _pattern("confirmed again"),
            _pattern("changed start date", "meeting"),
            _pattern("start date change", "meeting"),
            _pattern("start date changes", "meeting"),
            _pattern("new start date", "meeting"),
            _pattern("changed date", "meeting"),
        ),
        "must_not": (_phrase("late acknowledgment"),),
    },
    {
        "id": "P4-due",
        "passage": "P4",
        "patterns": (
            _pattern("orientation", "five business days"),
            _pattern("when", "orientation", "due"),
            _pattern("orientation", "after starting"),
            _pattern("orientation", "after the start"),
            _pattern("orientation due"),
        ),
        "must_not": (
            _phrase("who owns"),
            _phrase("who schedules"),
            _phrase("who is responsible"),
            _phrase("prerequisite"),
        ),
    },
    {
        "id": "P4-owner",
        "passage": "P4",
        "patterns": (
            _pattern("who owns", "orientation"),
            _pattern("who schedules", "orientation"),
            _pattern("manager owns", "orientation"),
            _pattern("who is responsible", "orientation"),
            _pattern("orientation", "scheduling", "who"),
        ),
        "must_not": (
            _phrase("five business days"),
            _phrase("prerequisite"),
            _phrase("orientation due"),
        ),
    },
    {
        "id": "P4-not-prereq",
        "passage": "P4",
        "patterns": (
            _pattern("equipment", "prerequisite"),
            _pattern("prerequisite", "training"),
            _pattern("prerequisite", "orientation"),
            _pattern("assigning or scheduling training"),
            _pattern("equipment", "required before", "training"),
        ),
        "must_not": (
            _phrase("confirm the laptop"),
            _phrase("reserve a loaner"),
        ),
    },
)

_OUT_OF_PACK = (
    _phrase("pay"),
    _phrase("salary"),
    _phrase("wage"),
    _phrase("wages"),
    _phrase("compensation"),
    _phrase("paycheck"),
    _phrase("overtime"),
    _phrase("time and a half"),
    _phrase("extra hours"),
    _phrase("remote"),
    _phrase("remotely"),
    _phrase("work from home"),
    _phrase("wfh"),
    _phrase("telework"),
    _phrase("telecommute"),
    _phrase("eligible to work"),
    _phrase("work authorization"),
    _phrase("visa"),
    _phrase("i 9"),
    _phrase("i9"),
    _phrase("legal eligibility"),
    _phrase("right to work"),
)

_INSTRUCTIONS = (
    _phrase("confirm the laptop"),
    _phrase("confirm the loaner"),
    _phrase("confirm a loaner for"),
    _phrase("please confirm"),
    _phrase("reserve the laptop"),
    _phrase("reserve a loaner"),
    _phrase("reserve the device for"),
    _phrase("reserve a device for"),
    _phrase("set equipment readiness"),
    _phrase("mark equipment ready"),
    _phrase("mark the laptop ready"),
    _phrase("mark the loaner ready"),
    _phrase("book the laptop"),
    _phrase("book a loaner"),
    _phrase("change equipment evidence"),
    _phrase("update equipment readiness"),
)

_HIRE_PHRASES = (
    _phrase("for this hire"),
    _phrase("for this case"),
    _phrase("for riley"),
    _phrase("for jordan"),
)

OBLIGATION_PASSAGE = {row["id"]: row["passage"] for row in _PACK}


def detect(question: str) -> dict:
    """Classify one question. Retrieval terms do not mark an obligation."""
    clauses = [_classify_clause(tokenize(piece)) for piece in _clauses(question)]
    obligations: list[str] = []
    seen = set()
    for clause in clauses:
        for obligation in clause["obligations"]:
            if obligation not in seen:
                seen.add(obligation)
                obligations.append(obligation)
    out_of_pack = any(clause["out_of_pack"] for clause in clauses)
    instruction = any(clause["instruction"] for clause in clauses)
    unmatched_clause = any(clause["unmatched"] for clause in clauses)
    pack_clause = any(clause["obligations"] for clause in clauses)
    if out_of_pack:
        route = "out_of_pack"
    elif instruction:
        route = "equipment_instruction"
    elif pack_clause and unmatched_clause:
        route = "ambiguous"
    elif pack_clause and clauses and all(clause["obligations"] for clause in clauses):
        route = "pack"
    else:
        route = "unmatched"
    candidates = _candidates(question) if route in {"pack", "unmatched"} else []
    return {
        "route": route,
        "obligations": obligations if route == "pack" else [],
        "candidates": candidates,
        "call_model": bool(candidates) and route in {"pack", "unmatched"},
    }


def _candidates(question: str) -> list[str]:
    tokens = set(tokenize(normalize(question)))
    found = []
    for passage, terms in RETRIEVAL.items():
        if any(term in tokens for term in terms):
            found.append(passage)
    return found


def _classify_clause(tokens: list[str]) -> dict:
    out_of_pack = any(_contains(tokens, phrase) for phrase in _OUT_OF_PACK)
    instruction = _instruction(tokens)
    obligations = []
    if not instruction:
        for row in _PACK:
            if _row_matches(tokens, row):
                obligations.append(row["id"])
    return {
        "out_of_pack": out_of_pack,
        "instruction": instruction,
        "obligations": obligations,
        "unmatched": not out_of_pack and not instruction and not obligations,
    }


def _instruction(tokens: list[str]) -> bool:
    if not tokens:
        return False
    suppressed = tokens[0] in _OPENERS and not any(_contains(tokens, phrase) for phrase in _HIRE_PHRASES)
    if suppressed:
        return False
    return any(_contains(tokens, phrase) for phrase in _INSTRUCTIONS)


def _row_matches(tokens: list[str], row: dict) -> bool:
    if any(_contains(tokens, phrase) for phrase in row["must_not"]):
        return False
    return any(all(_contains(tokens, phrase) for phrase in pattern) for pattern in row["patterns"])


def _contains(tokens: list[str], phrase: tuple[str, ...]) -> bool:
    width = len(phrase)
    if width == 0 or width > len(tokens):
        return False
    return any(tokens[index : index + width] == list(phrase) for index in range(len(tokens) - width + 1))


def normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKC", text).casefold()
    for mark in _APOSTROPHES:
        folded = folded.replace(mark, "")
    return folded


def tokenize(text: str) -> list[str]:
    tokens = []
    current: list[str] = []
    for char in text:
        if unicodedata.category(char).startswith(("L", "N")):
            current.append(char)
        elif current:
            tokens.append(_rewrite("".join(current)))
            current = []
    if current:
        tokens.append(_rewrite("".join(current)))
    return [token for token in tokens if token]


def _rewrite(token: str) -> str:
    if token in _DELETE:
        return ""
    return _REWRITES.get(token, token)


def _clauses(question: str) -> list[str]:
    pieces = []
    for piece in _split_punctuation(normalize(question)):
        pieces.extend(_split_connectors(piece))
    return [piece for piece in pieces if piece.strip()]


def _split_punctuation(text: str) -> list[str]:
    pieces = []
    current: list[str] = []
    for char in text:
        if char in "?!.;":
            piece = "".join(current).strip()
            if piece:
                pieces.append(piece)
            current = []
        else:
            current.append(char)
    tail = "".join(current).strip()
    if tail:
        pieces.append(tail)
    return pieces


def _split_connectors(piece: str) -> list[str]:
    piece = piece.strip()
    if not piece:
        return []
    for separator in (" and ", " but "):
        start = 0
        while True:
            index = piece.find(separator, start)
            if index < 0:
                break
            left = piece[:index].strip()
            right = piece[index + len(separator) :].strip()
            if len(left.split()) >= 2 and len(right.split()) >= 2:
                return _split_connectors(left) + _split_connectors(right)
            start = index + len(separator)
    return [piece]
