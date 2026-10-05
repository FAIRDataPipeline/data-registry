"""
The registry's own vocabulary: the terms its provenance reports and RO Crates use
where no standard vocabulary has one.

Each term is identified by the central registry's `vocab/#<term>` address, where the
`vocab` view serves this list. A `Term` is its `name`, whether it is a `CLASS` or a
`PROPERTY`, and a `definition` saying what it means and where it is used.
"""

from collections import namedtuple

Term = namedtuple("Term", "name kind definition")

CLASS = "class"
PROPERTY = "property"

TERMS = (
    Term(
        "Namespace",
        CLASS,
        "A namespace: the grouping within which data products are named, so that a "
        "data product's full name is its namespace, name and version. An RO Crate's "
        "Namespace entity carries the namespace's name, and its full name and website "
        "where the registry has them.",
    ),
    Term(
        "Run",
        CLASS,
        "A code run: one execution of a model or script through the pipeline, which "
        "read inputs and wrote outputs. The type of a provenance report's activities.",
    ),
    Term(
        "alternate_identifier",
        PROPERTY,
        "An identifier of an external source that is not a URL: a name for it within "
        "some domain, such as a project's own name for a dataset.",
    ),
    Term(
        "alternate_identifier_type",
        PROPERTY,
        "What kind of name an alternate identifier is: the domain within which it is "
        "unique.",
    ),
    Term(
        "code_runner",
        PROPERTY,
        "The role of the agent that started a code run, in a provenance report's "
        "wasStartedBy relation.",
    ),
    Term(
        "commit",
        PROPERTY,
        "The commit of a code repository that a code run was run from: the hash the "
        "registry records for the repository's location.",
    ),
    Term(
        "hash",
        PROPERTY,
        "The SHA-1 of a file's bytes, as the registry recorded it, in a provenance "
        "report. An RO Crate gives the same value as sha1.",
    ),
    Term(
        "identifier",
        PROPERTY,
        "The identifier of the user who started a code run, in a provenance report. "
        "An author's identifier is dcterms:identifier.",
    ),
    Term(
        "input_data",
        PROPERTY,
        "The role of a data product that a code run read, in a provenance report's "
        "used relation.",
    ),
    Term(
        "issue",
        PROPERTY,
        "An issue raised against a file or one of its components, as one line of "
        "text. A provenance report writes the description, then the severity, then "
        "the issue's row in that registry; an RO Crate writes the issue's uuid, then "
        "its severity, then its description, in that order so that a reader can "
        "parse it.",
    ),
    Term(
        "model_configuration",
        PROPERTY,
        "A code run's working configuration: the config.yaml the pipeline wrote for "
        "the run, which maps the names the code uses to data products. The role of "
        "the file in a provenance report's used relation; a link from the run to the "
        "file in an RO Crate.",
    ),
    Term(
        "namespace",
        PROPERTY,
        "The namespace a data product is named in: its name in a provenance report, "
        "a link to a Namespace entity in an RO Crate.",
    ),
    Term(
        "software",
        PROPERTY,
        "The role of the code repository a code run was run from, in a provenance "
        "report's used relation.",
    ),
    Term(
        "submission_script",
        PROPERTY,
        "A code run's submission script: the script the pipeline ran. The role of the "
        "file in a provenance report's used relation; a link from the run to the file "
        "in an RO Crate.",
    ),
    Term(
        "website",
        PROPERTY,
        "The website of a code repository release, in a provenance report.",
    ),
)
