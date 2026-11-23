"""Ten invented user fact sets for resume generation tests."""

from __future__ import annotations

from medici.resume.schema.facts import EmployerFact, ProjectFact, SchoolFact, UserFacts

# All names and domains are invented — no real people or companies.

SAMPLE_FACT_SETS: tuple[UserFacts, ...] = (
    UserFacts(
        employers=(
            EmployerFact(
                name="Loominary Labs",
                title="Platform Engineer",
                start="Jun 2019",
                end="Present",
            ),
        ),
        schools=(
            SchoolFact(
                name="North Example Institute",
                degree="B.S. CS",
                start="2015",
                end="2019",
            ),
        ),
        tools=("Python", "PostgreSQL"),
    ),
    UserFacts(
        employers=(
            EmployerFact(
                name="Paperbyte Systems",
                title="Intern",
                location="Sampleville, EX",
                start="May 2017",
                end="Aug 2017",
            ),
        ),
        schools=(
            SchoolFact(
                name="East Ficton College",
                degree="A.A. Programming",
                start="2015",
                end="2017",
            ),
        ),
        tools=("Java",),
    ),
    UserFacts(
        employers=(
            EmployerFact(name="Widgetry Co", title="SRE", start="2020", end="2022"),
            EmployerFact(name="Cratestack Ltd", title="Junior Dev", start="2018", end="2020"),
        ),
        schools=(
            SchoolFact(
                name="South Sample University",
                degree="B.Eng",
                start="2014",
                end="2018",
            ),
        ),
        tools=("Go", "Terraform", "Linux"),
    ),
    UserFacts(
        employers=(
            EmployerFact(
                name="Hexabyte Analytics",
                title="Data Engineer",
                start="2021",
                end="Present",
            ),
        ),
        schools=(
            SchoolFact(
                name="Institute of Example Studies",
                degree="M.S. Data",
                start="2019",
                end="2021",
            ),
        ),
        tools=("Python", "Spark", "SQL"),
        projects=(
            ProjectFact(
                name="batch-merger",
                start="Jan 2020",
                end="Jun 2020",
                tools=("Python", "Spark"),
                bullets=("Merged fixture streams.",),
            ),
        ),
    ),
    UserFacts(
        employers=(
            EmployerFact(
                name="Cloudfable Inc",
                title="Backend Lead",
                start="2017",
                end="2019",
            ),
        ),
        schools=(
            SchoolFact(
                name="West Imaginary Tech",
                degree="B.S.",
                start="2013",
                end="2017",
            ),
        ),
        tools=("Rust", "Docker"),
        projects=(
            ProjectFact(
                name="api-shard",
                start="2016",
                end="2017",
                tools=("Rust",),
            ),
        ),
    ),
    UserFacts(
        employers=(
            EmployerFact(
                name="Nimbus Nine",
                title="Consultant",
                start="Mar 2022",
                end="Dec 2023",
                bullets=("Advised on example.test migrations.",),
            ),
        ),
        schools=(),
        tools=("Python", "AWS"),
    ),
    UserFacts(
        employers=(
            EmployerFact(
                name="Riverglass LLC",
                title="Engineer",
                start="2016",
                end="2018",
            ),
        ),
        schools=(
            SchoolFact(
                name="Central Fake Polytechnic",
                degree="Diploma",
                location="Ficton",
                start="2012",
                end="2016",
            ),
        ),
        tools=("C#", ".NET", "Azure"),
    ),
    UserFacts(
        employers=(
            EmployerFact(name="Tessera Works", title="ML Engineer", start="2019", end="2021"),
            EmployerFact(name="Tessera Works", title="Staff ML", start="2021", end="Present"),
        ),
        schools=(
            SchoolFact(
                name="Alphabet City University",
                degree="Ph.D.",
                start="2013",
                end="2018",
            ),
        ),
        tools=("PyTorch", "Python", "CUDA"),
    ),
    UserFacts(
        employers=(),
        schools=(
            SchoolFact(
                name="Open Horizon Academy",
                degree="Bootcamp",
                start="2022",
                end="2022",
            ),
        ),
        tools=("JavaScript", "React", "Node"),
        projects=(
            ProjectFact(
                name="demo-board",
                start="Nov 2022",
                end="Feb 2023",
                tools=("JavaScript", "React"),
                bullets=("Built a kanban for fixtures.",),
            ),
        ),
    ),
    UserFacts(
        employers=(
            EmployerFact(
                name="Substrate Foundry",
                title="Security Analyst",
                start="2020",
                end="2023",
            ),
        ),
        schools=(
            SchoolFact(
                name="Defense of Example Academy",
                degree="B.S. Cyber",
                start="2016",
                end="2020",
            ),
        ),
        tools=("Python", "Wireshark", "Linux"),
        projects=(
            ProjectFact(
                name="honeypot-lab",
                start="2018",
                end="2019",
                tools=("Python", "Linux"),
            ),
        ),
    ),
)