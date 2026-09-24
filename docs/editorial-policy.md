# Editorial matching policy

The matcher should produce an editor-usable, continuously covered intro rather
than a collection of isolated search results.

## Evidence priority

For each narration beat, prefer candidates in this order:

1. **Literal visible action.** Show the event occurring on screen: the player
   being hit and falling, a purchase interface, a revive, a vehicle full of
   teammates, or a clearly visible HUD value.
2. **Contextual source audio.** When the literal event happens off-screen, use
   an immediate spoken reaction such as “a helicopter just crashed” or “where
   did that shot come from?” together with the closest honest visual context.
3. **Specific contextual imagery.** Use the nearest truthful situation even if
   it is not a perfect literal match, such as teammates riding in a helicopter
   for narration about crashing with the team.
4. **Clean generic gameplay.** If no specific support exists, fill the beat with
   distinct, readable gameplay. Never leave a black gap merely because the
   match is imperfect.

## Assembly rules

- Extend each selected clip to the next narration beat so normal playback has
  continuous video coverage.
- Never reuse or overlap a source range across separate narration beats.
- Spread selections across the raw recording when equally relevant moments
  exist, so the intro does not feel assembled from one short source cluster.
- Treat later negative-balance HUD moments as stronger evidence for losing
  money than generic reactions or visually unrelated gestures.
- For teammate-specific narration, prefer footage that visibly follows,
  supports, rides with, or engages a teammate over generic solo combat.
- When generic gameplay is necessary, rotate locations and visual situations;
  do not repeat scenery already used by a nearby narration beat.
- Split compound narration into short sub-beats when the nouns/actions change
  (death, helicopter crash, sniper shot, money loss, vehicle, gun, medkit,
  revive).
- Source dialogue is valid evidence and may be placed on a contextual-audio
  track when it materially clarifies the event.
- Do not claim that a clip shows an event it does not show. Describe contextual
  fallbacks accurately in markers and reports.
