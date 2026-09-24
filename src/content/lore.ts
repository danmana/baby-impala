/**
 * Everything the journal says. Facts come from the show and fan wikis (see
 * docs/research.md); where fandom disagrees, the text says so.
 */
export interface Lore {
  title: string;
  /** a handwritten line pencilled above the title */
  kicker?: string;
  body: string[];
  /** a handwritten note in the margin */
  note?: string;
  /** episodes / sources, typed small at the bottom of the page */
  refs?: string;
}

export type HotspotView = 'exterior' | 'interior' | 'trunk';

export interface Hotspot {
  id: string;
  label: string;
  /** three.js car-space position (x forward, y up, z to the passenger side) */
  pos: [number, number, number];
  view: HotspotView;
  lore: Lore;
}

export const CAR: Lore = {
  kicker: 'Dean’s car. Don’t call it that to his face.',
  title: 'Baby',
  body: [
    'A black 1967 Chevrolet Impala four-door hardtop, the model Chevy called the Sport Sedan. Dean calls her Baby. She belonged to John Winchester first, and for most of their lives she is the only home Sam and Dean have.',
    'Motels change every night. The car doesn’t. Everything they own rides in the trunk, every hunt starts and ends on her bench seat, and every fight between the brothers happens somewhere on a two-lane road with the tape deck turned up.',
  ],
  note: 'Most important object in pretty much the whole universe. (Chuck said it, not me.)',
  refs: 'Chuck’s narration, 5.22 “Swan Song”',
};

export const HOTSPOTS: Hotspot[] = [
  {
    id: 'plates',
    label: 'KAZ 2Y5 / CNK 80Q3',
    pos: [2.62, 0.34, 0.0],
    view: 'exterior',
    lore: {
      kicker: 'Click the plate. Go on.',
      title: 'The plates',
      body: [
        'Her original Kansas plate reads KAZ 2Y5. It is an Easter egg: KAZ for Kansas, 2Y5 for 2005, the year Supernatural premiered.',
        'By season two the brothers are wanted by the FBI, so Dean swaps it for an Ohio plate, CNK 80Q3. It stays on her for most of the rest of the run. Fans usually read the Ohio choice as a nod to creator Eric Kripke, who grew up there.',
      ],
      note: 'Swapped plates > getting pulled over with a trunk full of shotguns.',
      refs: 'Ohio plate from 2.20 “What Is and What Should Never Be”',
    },
  },
  {
    id: 'engine',
    label: '327 four-barrel',
    pos: [1.9, 0.93, 0.0],
    view: 'exterior',
    lore: {
      kicker: '“A little TLC and this thing is cherry.”',
      title: '327 four-barrel, 275 horses',
      body: [
        'That is how Dean sells the car to his own father. Thrown back to 1973, he finds young John Winchester about to buy a VW van, talks him out of it, and points him at the Impala instead: a 327 cubic inch V8 with a four-barrel carburettor and 275 horsepower.',
        'So Dean is the reason John owns the car Dean grows up in. The production cars reportedly ran something bigger; the hero car is said to have had a 502 big-block crate engine for the driving shots.',
      ],
      note: 'Time travel. Don’t think about it too hard.',
      refs: '4.03 “In the Beginning”',
    },
  },
  {
    id: 'spotlights',
    label: 'A-pillar spotlights',
    pos: [0.93, 1.1, -0.965],
    view: 'exterior',
    lore: {
      kicker: 'Aim from inside. Handle by the mirror.',
      title: 'Twin spotlights',
      body: [
        'Two small round chrome spotlights sit on the A-pillars, one each side, aimed by a handle inside the cabin. On a black car at night they are one of the easiest ways to pick Baby out of a line-up.',
        'Fan wikis note they disappear for a stretch of the show, when crews needed the pillars for camera rigs, and come back later. Switch them on and sweep them across the dark.',
      ],
      refs: 'Super-wiki continuity notes',
    },
  },
  {
    id: 'wheels',
    label: '15" chrome wheels',
    pos: [1.772, 0.35, -0.97],
    view: 'exterior',
    lore: {
      title: 'Polished 15-inch wheels',
      body: [
        'Aftermarket 15-inch chrome wheels with a smooth dished face, a ring of small round holes and a chrome centre cap, on chunky black tyres.',
        'A stock ’67 Impala wore hubcaps. These wheels are the quickest way to tell Baby from any other black Chevy.',
      ],
    },
  },
  {
    id: 'mirror',
    label: 'One mirror',
    pos: [0.68, 1.07, -0.98],
    view: 'exterior',
    lore: {
      title: 'One round mirror',
      body: [
        'A single round chrome mirror on the driver’s door, with a tiny Chevy logo on the back of the head. There is no mirror on the passenger side.',
        'Inside, the rear-view mirror comes and goes depending on the season.',
      ],
      note: 'Shotgun doesn’t need a mirror. Shotgun needs to shut his cakehole.',
    },
  },
  {
    id: 'antenna',
    label: 'Radio antenna',
    pos: [0.77, 1.45, 0.79],
    view: 'exterior',
    lore: {
      title: 'The antenna',
      body: [
        'A long whip antenna on the passenger-side front fender. Mostly for show: the radio exists, but the tape deck does the real work.',
        'Dean keeps a box of cassettes in the car. Sam calls it “the greatest hits of mullet rock.” House rules: driver picks the music.',
      ],
      refs: '1.01 “Pilot”',
    },
  },
  {
    id: 'grille',
    label: 'Chevrolet script',
    pos: [2.56, 0.62, -0.36],
    view: 'exterior',
    lore: {
      title: 'Almost no badges',
      body: [
        'The only badges on Baby are the “Chevrolet” script on the horizontal-bar grille and a tiny bowtie on the chrome strip between the taillights. No flames, no stripes, no decals, no symbols on the outside.',
        'Quad round headlights, corner lamps wrapping the fender tips, a V-shaped hood and nose, and vertical chrome guards on both bumpers. From a distance she is just an immaculate, slightly menacing black sedan.',
      ],
    },
  },
  {
    id: 'hardtop',
    label: 'No B-pillar',
    pos: [0.0, 1.22, -0.92],
    view: 'exterior',
    lore: {
      title: 'Four doors, no pillar',
      body: [
        'Baby is the four-door hardtop: roll the windows down and there is no post between the front and rear doors, just one long opening under a sloping, almost fastback roof.',
        'It is a rarer, heavier car than the two-door Impala most collectors chase, and the only one that fits two brothers, a back seat full of research and a trunk full of shotguns.',
      ],
    },
  },
  {
    id: 'taillights',
    label: 'Tri-segment taillights',
    pos: [-2.66, 0.76, -0.64],
    view: 'exterior',
    lore: {
      title: 'Taillights',
      body: [
        'Three segments on each side, red, clear, red, in chrome surrounds. Between them, a chrome strip with the only other badge on the car: a tiny bowtie. The trunk lock sits dead centre on the lid above.',
        'Below: the heavy rear bumper with its own guards, and dual exhaust.',
      ],
    },
  },
  {
    id: 'trunk',
    label: 'The trunk',
    pos: [-2.1, 1.02, 0.0],
    view: 'exterior',
    lore: {
      kicker: '“You can put a body in that trunk.”',
      title: 'Why a ’67 Impala',
      body: [
        'Eric Kripke first wanted a mid-sixties Mustang. A mechanic neighbour talked him out of it: “You want a ’67 Impala because you can put a body in that trunk.”',
        'The trunk became the Winchesters’ mobile armoury, with a false floor over the weapons and a Devil’s Trap painted on the underside of the lid. Open the Trunk tab to look inside.',
      ],
      refs: 'Eric Kripke, interviews',
    },
  },
  {
    id: 'rebuilt',
    label: 'Rebuilt by hand',
    pos: [1.1, 0.8, -1.02],
    view: 'exterior',
    lore: {
      title: 'Rebuilt from the frame up',
      body: [
        'At the end of season one a demon-possessed trucker T-bones the Impala with an 18-wheeler, John, Sam and Dean inside. Bobby says she can’t be saved. Sam has her towed to the salvage yard anyway.',
        'Dean rebuilds her himself, grieving his father with a wrench in his hand. It won’t be the last time: across fifteen seasons she is crushed, flipped, shot up and put back together again.',
      ],
      refs: '1.22 “Devil’s Trap”, 2.01 “In My Time of Dying”, 2.02 “Everybody Loves a Clown”',
    },
  },
  // ------------------------------------------------------------ interior
  {
    id: 'tape_deck',
    label: 'Tape deck',
    pos: [0.87, 0.85, 0.06],
    view: 'interior',
    lore: {
      kicker: 'Driver picks the music.',
      title: 'The tape deck',
      body: [
        'An aftermarket slot-loading cassette deck under the dash: FM/AM dial window, a horizontal tape slot, chunky olive push buttons.',
        '“Black Sabbath, Motörhead, Metallica? It’s the greatest hits of mullet rock.” “House rules, Sammy. Driver picks the music, shotgun shuts his cakehole.”',
        'When Sam wires in an iPod jack while Dean is in Hell, Dean rips it out as soon as he is back.',
      ],
      refs: '1.01 “Pilot”',
    },
  },
  {
    id: 'legos',
    label: 'Legos in the vent',
    pos: [0.965, 1.06, -0.22],
    view: 'interior',
    lore: {
      kicker: 'Heat comes on, they rattle.',
      title: 'Legos in the vent',
      body: [
        'As a kid, Dean pushed Lego bricks into the defroster vent on top of the dash. They are still there. Every time the heat comes on you can hear them rattle.',
        'When he rebuilt the car, he made sure they went back in.',
      ],
      note: '“It’s the blemishes that make her beautiful.”',
      refs: '5.22 “Swan Song”',
    },
  },
  {
    id: 'army_man',
    label: 'Army man',
    pos: [-0.52, 0.76, -0.75],
    view: 'interior',
    lore: {
      title: 'The army man',
      body: [
        'Little Sam crammed a green plastic army man into the ashtray on the rear door. It is still stuck there.',
        'In “Swan Song”, with Lucifer wearing Sam and beating Dean in a cemetery, the sun catches that army man in Baby’s ashtray. Sam remembers growing up in the back seat, and fights his way back to the surface.',
      ],
      refs: '5.22 “Swan Song”',
    },
  },
  {
    id: 'initials',
    label: 'D.W. / S.W.',
    pos: [-1.17, 1.085, -0.12],
    view: 'interior',
    lore: {
      title: 'Carved initials',
      body: [
        'The boys carved their initials, D.W. and S.W., into the car as kids, under the rear package tray behind the back seat.',
        'Years later, in the Men of Letters bunker, they carve them into the library table too.',
      ],
      refs: '5.22 “Swan Song”, 11.04 “Baby”',
    },
  },
  {
    id: 'bench',
    label: 'Bench seats',
    pos: [0.2, 0.95, 0.35],
    view: 'interior',
    lore: {
      title: 'The front bench',
      body: [
        'Black vinyl bench seats with vertical pleats, front and back, against a tan padded dash, tan door panels and a tan headliner. Worn in, not showroom.',
        'Most of the show’s big conversations happen right here, one brother driving, one riding shotgun, the road going by.',
        'In “Baby” the whole episode is shot from inside or around the car. We ride along the way she does.',
      ],
      refs: '11.04 “Baby”',
    },
  },
];

export const TRAP: Lore = {
  kicker: 'Keep the lines unbroken.',
  title: 'The Devil’s Trap',
  body: [
    'A pentagram in a circle with sigils in the gaps, hand-painted in rough cream strokes on the black underside of the trunk lid. Any demon that steps inside a Devil’s Trap is stuck there: it can’t leave, can’t smoke out of its host, can’t use most of its powers.',
    'The trap only holds while its lines are unbroken. Scratch it, scuff it, drip water on it, and the demon walks.',
    'On Baby it guards the arsenal, and the lid closes the trap right over the contents of the trunk. Close it on something demonic and the Impala becomes a demon holding cell on wheels.',
  ],
  note: 'Not decoration.',
  refs: 'The symbol: 1.22 “Devil’s Trap”',
};

export interface TrunkItem {
  name: string;
  lore: Lore;
}

const item = (name: string, body: string[], refs?: string, note?: string): TrunkItem => ({
  name,
  lore: { title: name, body, refs, note },
});

export const TRUNK_ITEMS: Record<string, TrunkItem> = {
  shotgun: item('Pump shotgun', ['The workhorse of the arsenal. Loaded with rock salt it drives off ghosts; with slugs it handles anything with a body.'], 'Everywhere, from the Pilot on'),
  sawed_off: item('Sawed-off shotgun', ['Short enough to hide under a jacket. Rock salt for spirits, silver shot for shapeshifters. Dean’s favourite argument-ender.']),
  rock_salt: item('Rock-salt shells', ['Salt disperses a ghost for a while. It won’t kill one, but it buys enough time to dig up the bones.'], '1.01 “Pilot” and every salt-and-burn after'),
  silver_bullets: item('Silver bullets', ['Silver kills werewolves and shapeshifters and hurts a long list of other things. The brothers make a lot of their own rounds.']),
  colt: item('The Colt', [
    'The gun that can kill almost anything. John tells the story: made by Samuel Colt in the 1830s, with thirteen hand-made bullets. Only a handful of beings in creation are immune.',
    'It is why the Devil’s Trap is painted on the lid: a demon reaching into the trunk for the Colt gets stuck.',
  ], '1.20 “Dead Man’s Blood”, 1.22 “Devil’s Trap”', 'Non timebo mala.'),
  holy_water: item('Holy water', ['Burns demons on contact. A splash is also the quickest test for whether someone is possessed.']),
  holy_water_2: item('Holy water (flask)', ['Always carry a spare. Demons don’t like it much.']),
  salt: item('Salt', ['A line of salt across a doorway or windowsill, or a full circle, is a wall no ghost can cross. The first thing any hunter packs.']),
  crowbar: item('Iron crowbar', ['Pure iron hurts ghosts and spirits, and fairies hate it. Also opens tombs, doors and the occasional trunk.'], '6.09 “Clap Your Hands If You Believe”'),
  machete: item('Machete', ['The only sure way to kill a vampire in this world is to take its head. Hence the machete.'], '1.20 “Dead Man’s Blood”'),
  dead_mans_blood: item('Dead man’s blood', ['Poison to vampires: coat a blade with it and a vampire goes down weak and sluggish long enough for the machete.'], '1.20 “Dead Man’s Blood”'),
  lighter_fluid: item('Lighter fluid', ['Salt and burn: dig up the bones, salt them, douse them and drop a match. It is how a ghost is put down for good.'], 'The Pilot and a hundred cemeteries after'),
  flashlight: item('Flashlight', ['Every hunt happens at night, in basements, crypts and abandoned asylums.']),
  flashlight_2: item('Flashlight (spare)', ['Batteries die at the worst possible moment. Especially near ghosts.']),
  emf: item('EMF meter', ['Detects the electromagnetic field spirits give off. Dean built his out of an old Walkman.'], 'Seasons 1–3'),
  fake_ids: item('Fake IDs', ['FBI, CDC, federal marshals, priests. The aliases are usually borrowed from classic-rock musicians: Agent Page, Agent Plant.']),
  fake_ids_2: item('More fake IDs', ['A different badge for every town.']),
  journal: item('John’s journal', ['John Winchester’s notebook: decades of lore, monster notes, phone numbers and family history. For years it is the closest thing the brothers have to a father.'], 'From the Pilot on'),
  lock_picks: item('Lock picks', ['Hunting is mostly breaking and entering.']),
  hex_bag: item('Hex bag', ['Witches hide these to curse a victim. Find it and burn it, and the curse breaks.']),
  holy_oil: item('Holy oil', ['Light a ring of it and an angel can’t cross the flames.'], 'Seasons 5–6 onward'),
  cross: item('Cross', ['General warding. It helps with exorcisms, but faith matters more than the wood.']),
  sage: item('Sage bundle', ['Burned for cleansing and warding, as it was on the pegboard of the real prop trunk.']),
  dreamcatcher: item('Dreamcatcher', ['Fan-wiki inventories list one in the trunk; the show never makes much of it. A hunter takes whatever works.']),
  brass_knuckles: item('Brass knuckles', ['For when it has a body and you’re out of shells. A later set is inscribed with Enochian, which makes them work on angels.']),
  hatchet: item('Hatchet', ['Chops wood for bonfires, and heads when the machete is out of reach.']),
  arrow: item('Silver-tipped arrow', ['For the crossbow: silver tips for anything silver hurts, from a distance.']),
  bandolier: item('Bandolier of shells', ['More rock salt, ready to grab on the way out of the car.']),
  ammo_can: item('Ammo can', ['Boxes and loose rounds for every gun in the car, including the special rounds the brothers load themselves.']),
  ammo_can_2: item('Ammo can', ['Because one is never enough.']),
  duct_tape: item('Duct tape', ['Restraints, repairs, and gagging people who ask too many questions.']),
  rope: item('Rope', ['Tie up a vessel for an exorcism, climb down a well, drag a coffin. Chains when it is stronger than you.']),
  chain: item('Chain', ['Some things break rope. Iron chain holds the ones that don’t like iron.']),
  flares: item('Road flare', ['Wendigos only die by fire. So does a lot of other stuff.'], '1.02 “Wendigo”'),
  bowie: item('Bowie knife', ['A big plain steel knife for jobs that don’t need anything special.']),
  silver_knife: item('Silver knife', ['For djinn, shifters, werewolves and anything else silver hurts.']),
  sheath_knife: item('Knife in a sheath', ['Strapped to the board with the rest of the blades.']),
  ruby_knife: item('Ruby’s knife', ['A demon-killing blade taken from the demon Ruby. For years it is the only thing short of the Colt that kills a demon outright.'], 'Season 3 onward'),
  angel_blade: item('Angel blade', ['Standard issue for angels, taken from the dead ones. Kills angels, and most other things it stabs.'], 'Common from season 8'),
  holster: item('Holster', ['Handguns go on the board too.']),
  pouch: item('Pouch', ['Herbs, bones, spell ingredients: whatever this week’s ritual needs.']),
  rosary: item('Rosary', ['Blessed beads. Dunk one in water and you have a quick batch of holy water.']),
  stake: item('Wooden stake', ['Old-school vampire lore. In this world it takes a head, not a stake, but stakes still work on some other things.']),
  stake_2: item('Another stake', ['Better to have one and not need it.']),
};

export interface Track {
  title: string;
  artist: string;
  src?: string;       // local file
  spotify?: string;   // spotify track id
  seconds?: number;
}

export interface Tape {
  id: string;
  label: string;       // hand-written label on the cassette edge
  sub: string;
  color: string;
  tracks: Track[];
  kind: 'local' | 'spotify';
}

const km = (title: string, file: string, seconds: number): Track => ({
  title, artist: 'Kevin MacLeod', src: `audio/${file}.mp3`, seconds,
});

export const TAPES: Tape[] = [
  {
    id: 'mullet',
    label: 'MULLET ROCK',
    sub: 'side A',
    color: '#c9a23a',
    kind: 'local',
    tracks: [
      km('Big Rock', 'big-rock', 231), km('Twisted', 'twisted', 187), km('Gearhead', 'gearhead', 139),
      km('Hotrock', 'hotrock', 205), km('Neolith', 'neolith', 167),
    ],
  },
  {
    id: 'blues',
    label: 'ROADHOUSE',
    sub: 'blues',
    color: '#8e3b2a',
    kind: 'local',
    tracks: [
      km('Slow Burn', 'slow-burn', 229), km('Matt’s Blues', 'matts-blues', 167), km('OctoBlues', 'octoblues', 256),
      km('Hustle', 'hustle', 121), km('Nile’s Blues', 'niles-blues', 153),
    ],
  },
  {
    id: 'metal',
    label: 'HEAVY',
    sub: 'play loud',
    color: '#3d4a55',
    kind: 'local',
    tracks: [
      km('Metalmania', 'metalmania', 190), km('Cool Rock', 'cool-rock', 209), km('Noise Attack', 'noise-attack', 155),
      km('Exhilarate', 'exhilarate', 145), km('Motherlode', 'motherlode', 237),
    ],
  },
  {
    id: 'real',
    label: 'THE REAL DEAL',
    sub: 'via Spotify',
    color: '#2b2b2b',
    kind: 'spotify',
    tracks: [
      { title: 'Carry On Wayward Son', artist: 'Kansas', spotify: '50XEfDqjfO5ArryPtFCd9I' },
      { title: 'Back In Black', artist: 'AC/DC', spotify: '42h6H7zxEIP2CKRFsCZMuK' },
      { title: 'Renegade', artist: 'Styx', spotify: '0mm40yDFxN5zV6m5cUNMM7' },
      { title: 'Wanted Dead Or Alive', artist: 'Bon Jovi', spotify: '4jIcQJcRN720hPUnVPI27j' },
      { title: 'Bad Moon Rising', artist: 'Creedence Clearwater Revival', spotify: '0BG2iE6McPhmAEKIhfqy1X' },
      { title: 'Rock Of Ages', artist: 'Def Leppard', spotify: '0zOUO2Cbz0C1F8qbrebIxn' },
      { title: 'Simple Man', artist: 'Lynyrd Skynyrd', spotify: '0FTKlr5Ox1V00wNcZKYmcr' },
      { title: 'Smoke On The Water', artist: 'Deep Purple', spotify: '39xwg2bRxIozU84vrRgqXE' },
      { title: 'Don’t Fear the Reaper', artist: 'Blue Öyster Cult', spotify: '7H1E4sqAN1rsDsEtn7IWv2' },
      { title: 'Thunderstruck', artist: 'AC/DC', spotify: '57bgtoPSgt236HzfBOd8kj' },
      { title: 'Eye of the Tiger', artist: 'Survivor', spotify: '2KH16WveTQWT6KOG9Rg6e2' },
    ],
  },
];

export const LOADING_STEPS = [
  'Salting the doorways',
  'Loading the rock salt',
  'Waxing the chrome',
  'Checking the Devil’s Trap',
  'Rewinding the tapes',
];
