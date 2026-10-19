# Semantic modeling instructions

## Purpose of Draw.io models

Use Draw.io to create a structural semantic model of domain concepts and their relationships. The diagram is the working view for proposing, reviewing, and driving structural semantic changes.

Use RDF Turtle for the formal ontology, including property definitions, attributes, datatypes, constraints, and axioms. Keep the diagram and Turtle aligned as structural decisions are accepted. Do not create Turtle merely because a diagram is being edited unless the task calls for it.

## Diagram content

- Show concepts and directed, named relationships between concepts.
- Do not put attribute/property lists, datatype fields, or property-definition tables in concept shapes or diagram notes. Capture those details in RDF Turtle. Brief illustrative instance names or values are allowed in the example notes described below.
- Relationship names on arrows are required. The exclusion of properties means attribute/detail listings, not the concept-to-concept relationships that constitute the structural model.
- Use one relationship name per connector. Do not combine distinct relationships into labels such as `payer / payee`.
- List the competency questions relevant to each diagram page in a dedicated right-side panel, using stable question identifiers and the full question text. Place the legend immediately below the questions in that same panel.
- Keep detailed explanations, source traceability, query mappings, and unresolved modeling decisions in accompanying Markdown. The canvas includes a concise title, the competency-question panel, its legend, and brief illustrative example notes.
- Beneath key concepts referenced in the competency questions, show one to three synthetic sample instance names or values. Enclose each example in square brackets and render it in bold, for example **[Atlas Growth Fund I]**. Render only the bracketed example text: no heading, prefix, explanatory prose, enclosing note box, or attachment line.
- Keep each example visually associated with its concept and outside the circle. Examples illustrate the concept; they are not additional classes, asserted production facts, or attribute inventories.
- In every page's legend, explicitly state that bold text in square brackets denotes examples of synthetic data. Reserve this notation for synthetic examples.
- Distinguish concept classes from instances and roles. Do not introduce inheritance solely because two concepts are associated or one participates in the other.

## Visual notation

- Represent concepts as circles with pale, low-saturation fills, dark readable labels, and thin outlines.
- Prefer slightly smaller circles: approximately 120 × 120 Draw.io units, compared with the previous 150 × 150 size. Wrap concept labels and retain readable type; enlarge individual circles only when necessary for legibility.
- Use color consistently to distinguish meaningful concept groups. Explain any grouping in a small legend; color must not be the sole indication of semantics.
- Represent ordinary relationships with solid directed connectors and a conventional arrowhead at the target. Read each connector as source concept → relationship name → target concept.
- Represent inheritance with a dashed connector labeled exactly `subclassOf`, directed from the subclass to the superclass.
- At the superclass end of an inheritance connector, use a small hollow UML-style triangle instead of a conventional arrowhead. In Draw.io use `dashed=1;endArrow=block;endFill=0;endSize=10;startArrow=none;` (or an equivalent small hollow triangular marker).

## Layout

- Use an actual force-directed graph layout to establish concept positions, based on the concept/relationship graph. Do not substitute a manually spaced grid or hierarchical layout and describe it as force-directed.
- Use a stable seed when the layout engine supports it, so equivalent inputs produce reproducible positions.
- Reserve the right-side panel before laying out the graph. Keep competency questions and the legend outside the force simulation; keep example notes anchored beneath their concepts and account for their bounds when spacing nodes and routing edges.
- After the force-directed pass, adjust spacing and connector routing as needed to prevent node overlap, keep relationship labels readable, and reduce unnecessary crossings while preserving the overall layout.
- Use straight relationship connectors by default. Route around another concept circle only when it obstructs the direct path; keep any necessary detour minimal. Reposition example notes and labels before bending a connector to accommodate them.
- Exception: when two concepts have relationships in both directions, use separate curved connectors on opposite sides of the direct path so each relationship label remains readable. Preserve each relationship's arrow direction and name rather than combining them into one double-headed connector. Apply the same label-separation treatment to multiple distinct relationships between the same two concepts, even when their directions match.
- Where relationship lines cross, use a small rounded semicircular line jump to distinguish crossing from connection. Use Draw.io `jumpStyle=arc;jumpSize=8;` and enable line jumps for the graph. A crossing does not imply a semantic junction.
- Split a large model into coherent views when needed. Repeated concepts across views retain the same meaning and styling.

## Overview page

- Keep a first page named `00 Model overview` that shows the whole model: the union of every concept and relationship on the detail pages, with each concept drawn once.
- Whenever a concept or relationship is added, renamed, or removed on a detail page, make the same change on the overview page. The overview introduces nothing that is absent from the detail pages.
- List all competency questions in the overview's right-side panel, with the legend below them.
- Do not place synthetic example notes on the overview page. Its legend states that examples appear on the detail pages instead of explaining the bracket notation.

## Review before delivery

- Verify that the Draw.io XML opens, all relationship endpoints exist, and concept identifiers are unique within each page.
- Render or open the diagram and inspect it visually for overlapping concepts, obscured labels, clipped content, and inheritance marker direction/style. XML validity alone is not visual verification.
- Check that inheritance points toward the superclass and that each connector has one clear relationship name.
- Check that unobstructed relationships are straight and crossing connectors have rounded line jumps enabled.
- Check that the overview page's concepts and relationships equal the union of the detail pages.
- Check that the diagram contains no attribute/property inventories and that supporting documentation reflects the final structural model.
- Verify that the competency questions are readable in the right-side panel, the legend sits directly below them, and example notes beneath key concepts are clearly illustrative and do not overlap nodes or connectors.
- Report any validation that could not be completed rather than claiming it passed.
