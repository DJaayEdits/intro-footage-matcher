# Dialogue-led visual timing and pacing

These reusable rules capture the October 4, 2026 second-pass brief. They apply
when refining an already assembled documentary rough cut. This document records
requirements, not a claim that an existing timeline has passed the review.

## Scope and foundation

Inspect the current timeline and listen to its dialogue before editing. Treat
existing visual selections as editorial intent, with adjustable timing and source
ranges. Reuse cached transcripts, word timestamps, source indexes and embeddings.
Do not rebuild the cut or search for new footage for every line. Preserve the
spoken edit and all audio tracks; adapt video around them. Preserve source media.

## Meaning and timing

Explicit user-marked hit frames take precedence over the audible-onset heuristic
below. Follow [marker-guided timing](fitmc-marker-timing-policy.md) when manual
markers demonstrate the user's intended timing. Preserve those markers and keep
explicit instructions separate from inferred editorial choices.

- Review at sentence, phrase and trigger-word levels. Each visual must reasonably
  represent the narration, including the correct subject and actor/victim roles.
- When a word introduces the depicted subject, place the cut on the first timeline
  frame of its audible onset. Use cached timestamps as a lead, confirm against
  the actual edited dialogue, and record the chosen timeline frame. Do not add
  a habitual several-frame offset. Document any strong editorial exception.
- For example, hold a creator visual through “was the creator ... and,” then cut
  to the community on the first frame of “everyone.” Cover the earlier gap with
  the previous relevant visual if the community shot currently starts too soon.
- Motivate cuts with new subjects, locations, actions, concepts, important nouns,
  emphasis, reveals, contrasts, jokes, escalation, emotion or story changes.
  Elapsed shot duration alone is not a reason to cut.
- A coherent visual may span several phrases. Conversely, a single sentence may
  need several visuals. Give viewers enough time to recognize the information.
- Selectively hold the previous visual into a genuinely new sentence or idea
  when it still supports the narration. Within the same sentence/idea, prefer
  precise trigger timing. This visual hold does not authorize moving audio.

## Clean source ranges

Review the entire displayed source range, including its in/out boundaries.
Source documentaries contain their own edits: cuts, dissolves, wipes, zoom
transitions, title cards and unrelated scene changes. Do not let these play
inside a selected B-roll shot. Any final transition must be an intentional edit
on the destination timeline. Detection scores and sampled frames are review
leads, not proof of cleanliness; visually inspect suspected boundaries.

When a range reaches an unwanted edit, trim before it or slide to a clean portion
of the same source. Source in/out points and existing timeline order are
adjustable. Replace the source only when the current material cannot work.

For extra duration, use this order:

1. Extend into additional relevant, clean, continuous footage from that source.
2. Apply a mild slowdown only if the motion remains natural.
3. Hold a strong, readable freeze frame when motion is unnecessary.
4. Extend an adjacent relevant visual over the interval.
5. Remove the fragment if none of these communicates the idea cleanly.

Do not stretch a tiny moving clip into conspicuous extreme slow motion.

## Short inserts and freezes

Keep a short insert when its information matters. If its usable moving portion
is too brief to understand, hold its strongest clean frame like a photograph.
Choose a sharp, readable, recognizable frame away from source transitions;
avoid blur, motion smear, partially changed shots and transition frames.

An intentional freeze within one continuous shot is allowed. It does not permit
reusing that source frame in another shot. Record the original source path and
frame for any generated still/retimed derivative, and reserve that provenance
against reuse; a new filename does not make reused imagery unique.

Remove an insert that adds no useful information, confuses the narration,
interrupts pacing or cannot be made clean. Fill its interval with a relevant
neighbor. Do not preserve every clip merely to retain the original structure.

An exceptionally relevant high-resolution online image is acceptable only when
clearly better than the available footage. Verify its subject and provenance;
prefer clean, recognizable imagery without distracting watermarks or graphics.
Do not replace good footage merely because another image exists.

## Safe application and evidence

Follow the existing live-audit, backup, stale-state refusal, non-ripple video-only
and audio-preservation guards. Group adjacent clips into bounded patches when
moving a shared boundary; cover the whole interval without accidental gaps or
changes outside the patch. Keep unrelated edits, properties and user annotations.

For each changed shot, record the dialogue trigger/idea, actual record frames,
source frames, reason, clean-range review and any retime/freeze provenance.
Revalidate source-frame uniqueness after every slip, extension, merge, replacement
or retime using the actual source frames consumed. Review repeated embedded
inserts across files as well as overlapping source ranges. Do not equate a
sampled duplicate check with exhaustive visual verification.

Use documented Resolve APIs or verified UI operations. If scripting cannot
perform a needed operation, prepare an exact manual instruction; do not invent
API methods or report an unapplied plan as completed.

Before completion, listen and watch the revised sequence against the unchanged
VO. Check motivated first-frame cuts, readable screen time, continuity, clean
source ranges, natural motion and absence of misleading/early visuals. Verify
actual saved video ranges, audio, other tracks and annotations against the fresh
audit. Keep the backup and receipt locally; keep source media and caches out of Git.

## Decision order

Meaning → strongest dialogue beat → comprehension time → clean source footage
→ no inherited source edit → natural extension/retime → freeze → relevant
neighbor → removal. Record unresolved passages rather than silently filling
with repeated or unrelated material.
