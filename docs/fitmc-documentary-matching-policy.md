# FitMC documentary matching policy

## Goal

Every spoken sentence or idea should be supported by the most accurate footage
available. The editor should not hear a specific claim while seeing unrelated
generic gameplay unless all stronger sources have been exhausted.

## Source priority

1. Literal footage of the exact event, person, location, build, battle, group,
   exploit, item, or action named in the voiceover.
2. Closely related footage from the same event, person, location, era, or story.
3. Strong contextual footage that truthfully supports the sentence.
4. General 2b2t gameplay/B-roll only when the specific and contextual searches
   fail.

## Search order for the Parker Wolf FitMC project

Search recursively under:

`/Users/djaay/Editing Projects Mac/Parker Wolf/Clips`

Prefer these folders in this order when their subject is relevant:

- `fit/` for FitMC-specific history/events.
- `rusher/` for TheCampingRusher/Rusher War material.
- `General 2B2T Clips/` as contextual or generic fallback footage.

Folder priority does not override factual relevance. A General clip that
literally shows the narrated event is stronger than a named-folder clip that
does not.

## Research rule

If a sentence contains a server event, faction, player, location, historical
reference, or terminology that is not clear enough to search accurately,
research the subject before choosing footage. Use that research to generate
search terms, aliases, dates, names, and visual cues. Do not treat research as
proof that a local clip depicts the event; the clip still has to be verified.

## Match quality

For every narration segment, record:

- narration text
- timeline start/end
- chosen source file
- chosen source start
- match type: literal / contextual / generic
- short reason
- confidence
- rejected stronger candidates, if any

A generic match should only be accepted after the specific search fails.

## Resolve assembly

The existing voiceover timeline is authoritative. Do not rebuild, move, trim,
or replace the voiceover. Place selected footage on video tracks over the exact
record-time range of the narration segment.

## Mandatory frame uniqueness

No frame may be reused in another shot. The same file may supply multiple shots
only when their full displayed source-frame ranges are disjoint. Include pauses,
merged narration fragments, and source/timeline FPS rounding in the reservation.
An overlap score penalty does not satisfy this requirement: skip the candidate
or stop for editorial review when no relevant unused source remains.

Run the hard uniqueness check again after manual selections or duration edits,
before placing video in Resolve. After placement, inspect actual source-frame
ranges across the entire cut and confirm existing audio/other tracks are unchanged.

Also check for repeated stills and inserts at different timestamps or in different
files. The October 2026 FitMC revision found repeated group, farming, Wrath, and
snowy-base stills embedded in Personal Story despite disjoint source ranges.
Source interval validation cannot detect those; displayed-image review is required.
Sampled comparisons can flag repeats but are not an exhaustive frame-level proof.

Keep the before/after audit and project backup locally in ignored reports; commit
rules, reusable guards, repair tools, and regression tests, not cached media.


## Clause-level review and pacing

Apply the user-reviewed rules in [FitMC red-marker review](fitmc-red-marker-review.md).
A source filename or transcript score cannot replace visual verification of the
actual selected range. Support each visible noun/action at its spoken timestamp,
including who performs the action and who is affected. Split a beat when it names
different subjects, and merge adjacent fragments when one continuous relevant
sequence gives the passage a steadier pace. Reserve literal footage for its named
passage, relocating earlier contextual use rather than repeating the footage.

Red review notes remain attached to their original timeline positions. Apply
bounded video-only patches against a fresh live audit, preserve unrelated manual
edits, and confirm the saved post-placement receipt before claiming completion.
