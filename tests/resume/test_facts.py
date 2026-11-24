"""User facts schema parsing and allowlists."""

from __future__ import annotations

from medici.resume.schema.facts import (
    EmployerFact,
    SchoolFact,
    UserFacts,
    allowed_dates,
    allowed_employers,
    allowed_schools,
    allowed_tools,
)


def test_allowlists_aggregate_user_facts():
    facts = UserFacts(
        employers=(
            EmployerFact(name="A", start="Jan 2020", end="Dec 2020"),
            EmployerFact(name="B", start="Feb 2021", end="Present"),
        ),
        schools=(SchoolFact(name="C", start="2016", end="2020"),),
        tools=("Python", "Go"),
        projects=(),
    )
    assert allowed_employers(facts) == frozenset({"A", "B"})
    assert allowed_schools(facts) == frozenset({"C"})
    assert allowed_tools(facts) == frozenset({"python", "go"})
    assert "Jan 2020" in allowed_dates(facts)
    assert "Present" in allowed_dates(facts)


def test_user_facts_from_dict_requires_employers_schools_tools():
    data = {
        "employers": [{"name": "Loominary Labs", "title": "Engineer"}],
        "schools": [{"name": "North Example Institute"}],
        "tools": ["Python"],
    }
    facts = UserFacts.from_dict(data)
    assert facts.employers[0].name == "Loominary Labs"
    assert facts.tools == ("Python",)