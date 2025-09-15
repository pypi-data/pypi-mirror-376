from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Hint:
    title: str
    why: str
    before: str
    after: str
    risk: str
    estimated_speedup_pct: int


CPP_COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)


def strip_comments(code: str) -> str:
    return re.sub(CPP_COMMENT_RE, "", code)


def detect_large_copy(code: str) -> Hint | None:
    # naive: function parameters by value for std::string or large types
    pat = re.compile(r"\b(\w+)\s*\(.*(std::string|std::vector<[^>]+>)\s+(\w+)\s*\)")
    if pat.search(code):
        return Hint(
            title="Avoid large copies in function parameters",
            why="Passing large objects by value copies them; prefer const reference or string_view",
            before="void f(std::string s);",
            after="void f(const std::string& s); // or std::string_view",
            risk="Beware of lifetime when using string_view",
            estimated_speedup_pct=5,
        )
    return None


def detect_push_back_reserve(code: str) -> Hint | None:
    if re.search(r"(std::)?vector<[^>]+>\s+\w+\s*;[\s\S]*?for\s*\(.*\)[\s\S]*?\.push_back\(", code):
        return Hint(
            title="Reserve capacity for vectors before push_back in loops",
            why="Reduces reallocations and copies during growth",
            before="vector<int> a; for(int i=0;i<n;i++) a.push_back(i);",
            after="vector<int> a; a.reserve(n); for(int i=0;i<n;i++) a.push_back(i);",
            risk="Ensure n is known or a reasonable estimate",
            estimated_speedup_pct=10,
        )
    return None


def detect_io_sync(code: str) -> Hint | None:
    if re.search(r"\bcin\b|\bcout\b", code) and not re.search(r"ios::sync_with_stdio\(false\)", code):
        return Hint(
            title="Speed up iostreams",
            why="Disable sync with stdio and untie cin/cout for faster IO",
            before="int x; cin >> x;",
            after="ios::sync_with_stdio(false); cin.tie(nullptr);",
            risk="Affects interaction with stdio/printf; avoid mixing",
            estimated_speedup_pct=15,
        )
    return None


def detect_pow_square_in_loop(code: str) -> Hint | None:
    if re.search(r"for\s*\(.*\)[\s\S]*?pow\(\s*([a-zA-Z_][\w]*)\s*,\s*2\s*\)", code):
        return Hint(
            title="Replace pow(x,2) with x*x in loops",
            why="pow is generic and slower than multiplication",
            before="for(...) y += pow(x,2);",
            after="for(...) y += x*x;",
            risk="Watch for type overflow/precision",
            estimated_speedup_pct=5,
        )
    return None


def detect_missing_O_flags(code: str) -> Hint | None:
    # cannot know compile flags from code; present generic suggestion
    return Hint(
        title="Enable -O2 and consider LTO/-march=native",
        why="Compiler optimizations often deliver significant speedups",
        before="g++ main.cpp -o a.out",
        after="g++ -O2 -pipe -std=c++17 -Wall -Wextra main.cpp -o a.out",
        risk="-Ofast and -march=native may affect portability/UB",
        estimated_speedup_pct=20,
    )


def detect_nested_loops_n2(code: str) -> Hint | None:
    if re.search(r"for\s*\(.*\)[\s\S]{0,200}?for\s*\(", code):
        if re.search(r"for[\s\S]{0,300}?\bfind\(|std::find\(|linear_search\(", code):
            return Hint(
                title="Avoid O(n^2) by using set/map or indexing",
                why="Replacing inner linear searches with hash maps reduces complexity",
                before="for(i) for(j) if(a[j]==x) ...",
                after="Use unordered_set/map or precomputed index",
                risk="Extra memory and construction overhead",
                estimated_speedup_pct=30,
            )
    return None


def detect_sort_unique(code: str) -> Hint | None:
    if re.search(r"sort\(.*\);[\s\S]{0,100}?auto\s+it\s*=\s*unique\(", code):
        return Hint(
            title="Use unordered_set if ordering is not needed",
            why="Hash-based deduplication can be faster for large datasets",
            before="sort(v.begin(), v.end()); v.erase(unique(v.begin(), v.end()), v.end());",
            after="unordered_set<T> s(v.begin(), v.end()); v.assign(s.begin(), s.end());",
            risk="Loses ordering; different iteration order",
            estimated_speedup_pct=10,
        )
    return None


def detect_loop_init(code: str) -> Hint | None:
    if re.search(r"for\s*\(.*\)[\s\S]{0,120}?(std::vector<|std::string\s+\w+\s*=)", code):
        return Hint(
            title="Hoist invariant initializations out of loops",
            why="Avoid re-creating objects on every iteration",
            before="for(...) { std::string t; /* ... */ }",
            after="std::string t; for(...) { /* ... */ }",
            risk="Ensure variable lifetime and correctness",
            estimated_speedup_pct=8,
        )
    return None


def generate_hints(source_path: Path, max_hints: int = 10) -> list[Hint]:
    code = source_path.read_text(encoding="utf-8", errors="ignore")
    code_no_comments = strip_comments(code)
    detectors = [
        detect_large_copy,
        detect_push_back_reserve,
        detect_io_sync,
        detect_pow_square_in_loop,
        detect_nested_loops_n2,
        detect_sort_unique,
        detect_loop_init,
        detect_missing_O_flags,
    ]
    hints: list[Hint] = []
    for det in detectors:
        try:
            h = det(code_no_comments)
            if h:
                hints.append(h)
            if len(hints) >= max_hints:
                break
        except Exception:
            continue
    return hints


