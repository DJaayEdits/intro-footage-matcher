# Marker-guided timing and editorial learning

These reusable rules capture the user's marker-guided refinement brief. They
are requirements for future edits, not evidence that the current markers have
been inspected or that a refinement has been applied.

## Read the complete instruction set

Before any pacing mutation, inventory every marker across the entire current
timeline, including markers outside the opening examples. Record raw marker
frame, absolute timeline frame, timecode, label, notes, duration, color and custom
metadata where available. Use the actual timeline FPS and start frame/timecode;
do not confuse timeline-relative offsets with absolute record frames or source
clip marker positions.

Associate each marker with its narration, preceding and following visuals, and
nearest existing visual boundary. Read all annotations as intentional information
that must be accounted for. Distinguish user-authored instructions from imported
chapter labels and generated matching metadata using evidence, not color alone.
A comment, range note or chapter marker does not automatically require a cut.
Record an explained disposition for every marker; never silently ignore one.

Preserve original marker positions and contents, including unnamed markers.
Do not move, rename, delete or overwrite annotations to make the edit appear
compliant. If inferred review markers are useful, identify them separately and
avoid overwriting existing markers. Do not populate the timeline with markers
merely to fill unmarked sections.

## Explicit frames outrank estimates

When the user identifies a marker as a visual-change point, its frame is the
exact requested hit. Place the relevant video boundary there even when cached
words, waveform alignment or an automatic heuristic suggest another frame.
Use narration analysis to understand the instruction, not to overrule it.

Precedence: explicit current user instruction → user-marked hit frame → timing
pattern demonstrated by those examples → actual dialogue evidence → cached or
automatic timing estimates. An inferred decision never overrides an explicit hit.
If instructions conflict or a requested hit cannot be supported safely, record
the precise conflict and required resolution; do not alter the marker or audio.

## Learn intent rather than a mechanical rhythm

Study why each demonstrated hit works: subject change, important noun, descriptive
word, action, reveal, contrast, escalation or completion of a thought. Notice the
setup words the previous image is allowed to cover. A sentence beginning is not
necessarily its strongest visual beat; an emphasized adjective such as “massive”
may be the intended reveal.

For unmarked passages, use those semantic examples with narration, sentence
structure, emphasis, existing selections and the pacing policy. Infer patterns
from multiple examples where available and record uncertainty when evidence is
thin. Do not invent a constant delay, fixed shot length, universal word rule or
cut on every emphasized word. If the same idea continues, a longer coherent shot
may best match the user's demonstrated style. A requested hit can motivate a cut;
unsupported visual movement cannot.

## Fit video around the chosen hit

Treat the current assembled timeline as the baseline. Preserve good selections
and refine shared boundaries rather than rebuilding the matcher or the cut.
Keep VO and every audio track locked. Extend a relevant neighbor, slip to a clean
source range, use mild natural retiming or a readable freeze, or remove a weak
intermediate fragment. Replace footage only when existing material cannot support
the narration cleanly. Follow the clean-source, comprehension and no-reuse rules.

Use fresh live-state checks, backups and bounded video-only patches. Moving a
boundary must preserve coverage on both sides without exposing a baked source
edit, creating a gap or overlap, reusing reserved source frames, or modifying
unrelated edits. Derived holds and retimes retain original-source provenance.

## Verify and report two kinds of decisions

After saving, read actual timeline boundaries back and compare explicit hits to
the exact requested frame, not a proximity tolerance. Verify all original markers,
audio and unrelated tracks against the pre-edit snapshot. Do not claim inspection,
listening or application from a generated plan alone.

Report separately:

- **All existing markers:** frame/timecode, label, spoken word or phrase, associated
  visual/boundary, exact alignment result, adjustment made or explained reason no
  boundary applies. Include unresolved conflicts and unchanged instructions.
- **Inferred timing changes:** spoken trigger, chosen frame/timecode, changed visual
  boundary and the specific demonstrated timing pattern that supports the choice.
  Label these as inferences, not instructions the user explicitly supplied.

If available tools cannot establish narration or apply an operation safely,
state the limitation and give exact current TC/frame and remaining operation.
Preserving an annotation is necessary; accounting for its editorial intent and
verifying the saved result are also required.
