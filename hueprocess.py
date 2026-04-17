import streamlit as st
import requests
import json
import base64
from dataclasses import dataclass

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hue Process",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

section[data-testid="stSidebar"] { background: #0a1628; border-right: 1px solid #c9a84c33; }
section[data-testid="stSidebar"] * { color: #e8dfc8 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label {
    color: #c9a84c !important; font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 0.12em; font-weight: 500;
}

.main .block-container { background: #0d1e35; padding: 2rem 2.5rem; max-width: 1100px; }
.stApp { background: #0d1e35; }

.hp-title { font-family: 'Playfair Display', serif; font-size: 2.6rem; font-weight: 700;
    color: #e8dfc8; letter-spacing: 0.02em; margin: 0; line-height: 1.1; }
.hp-subtitle { color: #c9a84c; font-size: 0.8rem; text-transform: uppercase;
    letter-spacing: 0.18em; margin-top: 4px; }
.hp-divider { border: none; border-top: 1px solid #c9a84c44; margin: 1.2rem 0; }

.option-card { background: #112240; border: 1px solid #c9a84c33; border-radius: 10px;
    padding: 1.2rem 1.4rem; margin-bottom: 1rem; position: relative; }
.option-card.rank-1 { border-color: #c9a84c88; background: #152a4a; }
.rank-badge { position: absolute; top: -10px; left: 16px; background: #c9a84c;
    color: #0a1628; font-size: 0.65rem; font-weight: 700; padding: 2px 10px;
    border-radius: 20px; text-transform: uppercase; letter-spacing: 0.1em; }
.item-label { font-size: 0.68rem; color: #c9a84c; text-transform: uppercase;
    letter-spacing: 0.12em; font-weight: 500; margin-bottom: 2px; }
.item-value { font-size: 0.95rem; color: #e8dfc8; font-weight: 400; margin-bottom: 8px; }
.item-reasoning { font-size: 0.78rem; color: #8fa8c8; font-style: italic;
    margin-top: -4px; margin-bottom: 8px; }

.weather-box { background: #112240; border: 1px solid #c9a84c33; border-radius: 10px;
    padding: 1rem 1.2rem; margin-bottom: 1.2rem; }
.weather-temp { font-family: 'Playfair Display', serif; font-size: 2rem; color: #e8dfc8; }
.weather-label { font-size: 0.72rem; color: #c9a84c; text-transform: uppercase; letter-spacing: 0.1em; }
.weather-adj { background: #1a3050; border-left: 3px solid #c9a84c; padding: 0.5rem 0.8rem;
    border-radius: 0 6px 6px 0; font-size: 0.82rem; color: #b0c4de; margin-top: 0.5rem; }

.section-head { font-family: 'Playfair Display', serif; font-size: 1.3rem;
    color: #e8dfc8; margin-bottom: 0.2rem; font-weight: 600; }
.section-sub { font-size: 0.78rem; color: #7a94b0; margin-bottom: 1rem; }

.stSelectbox > div > div { background: #112240 !important; border-color: #c9a84c44 !important; color: #e8dfc8 !important; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

CASE_TYPES = [
    "Jury Trial", "Bench Trial", "Deposition", "Mediation",
    "Office Day", "Client Meeting", "Settlement Conference",
    "Arbitration", "Appellate Argument", "Networking Event"
]

@dataclass
class Outfit:
    rank: int
    suit: str
    tie: str
    shoes: str
    socks: str
    accessories: str
    pocket_square: str
    strategic_note: str

REASONING = {
    "suit": {
        "gabardine": "Gabardine's tight weave reads authority without visual noise — ideal for sustained jury scrutiny.",
        "serge": "Serge's diagonal twill gives structure and longevity under long hearing days.",
        "fresco": "Fresco breathes across extended proceedings, maintaining crisp silhouette despite courtroom heat.",
        "flannel": "Flannel's soft texture projects approachability — effective for bench arguments.",
        "sharkskin": "Sharkskin's subtle sheen commands attention without ostentation in formal settings.",
        "hopsack": "Hopsack's open weave handles climate shifts during multi-location days.",
        "navy": "Navy is the universal signal of competence and trustworthiness to any jury.",
        "charcoal": "Charcoal commands authority — the courtroom's equivalent of formal dress.",
        "pantsuit": "A well-cut pantsuit conveys authority equal to any suit in the room.",
        "skirt suit": "A skirt suit at mid-knee length reads professional and approachable simultaneously.",
        "sheath": "A structured sheath under a blazer projects precision and preparation.",
    },
    "tie": {
        "silk": "Silk ties catch light subtly — signaling investment without distraction.",
        "repp": "Repp stripe ties communicate institutional affiliation and reliability.",
        "solid": "Solid ties minimize visual distraction, keeping the focus on your argument.",
        "muted": "Muted patterns acknowledge formality without claiming more than the moment requires.",
        "no tie": "Removing the tie shifts register from formal advocate to trusted counselor.",
    },
    "shoes": {
        "oxford": "Cap-toe oxfords are the universal signal of professional preparation.",
        "derby": "Derbies allow slightly more expressive silhouette while maintaining formality.",
        "monk": "Double monks project confident individualism — acceptable above deposition level.",
        "loafer": "Penny loafers signal relaxed authority appropriate for office and mediation contexts.",
        "pump": "A classic pump at 2–3 inches projects professional height and proportion.",
        "block heel": "Block heels provide stability across long hearing days without sacrificing authority.",
        "flat": "Pointed flats convey precision and professionalism without heel fatigue.",
        "kitten": "Kitten heels thread the needle between formal and accessible in client settings.",
    },
    "pocket_square": {
        "white": "A white square in TV fold is the courtroom standard — nothing more is needed.",
        "silk": "Silk pocket squares signal deliberate attention to professional presentation.",
        "linen": "Linen squares project understated quality — a mark of the prepared professional.",
    }
}

def get_reasoning(field: str, value: str) -> str:
    if not value or value.lower() in ("none", "n/a", ""):
        return ""
    val_lower = value.lower()
    for key, reason in REASONING.get(field, {}).items():
        if key in val_lower:
            return reason
    return ""

# ── Wardrobe Database ─────────────────────────────────────────────────────────

def build_wardrobe():
    W = {}
    def add(case, role, gender, rank, suit, tie, shoes, socks, acc, ps, note):
        W.setdefault(case, {}).setdefault(role, {}).setdefault(gender, [])
        W[case][role][gender].append(Outfit(rank, suit, tie, shoes, socks, acc, ps, note))

    # ── JURY TRIAL ────────────────────────────────────────────────────────────
    add("Jury Trial","Attorney","Male",1,"Charcoal gabardine two-button","Burgundy silk repp stripe","Black cap-toe oxford","Navy over-the-calf wool","Gold bar cuff links","White linen TV fold","Charcoal gabardine reads sustained authority; burgundy anchors confidence without aggression.")
    add("Jury Trial","Attorney","Male",2,"Navy serge single-breasted","Silver-grey grenadine","Black oxford","Charcoal over-the-calf","Silver knot cuff links","White silk TV fold","Navy serge is the default signal of trustworthiness to any jury pool.")
    add("Jury Trial","Attorney","Male",3,"Mid-grey fresco","Slate blue silk mogadore","Black derby","Medium grey OTC","Gunmetal cuff links","Pale blue silk puff","Fresco breathes through extended proceedings without visible wrinkling.")
    add("Jury Trial","Attorney","Male",4,"Dark charcoal flannel","Dark navy solid wool","Black oxford","Black OTC","Plain silver cuff links","None","Flannel projects understated gravitas — appropriate when client demographics favor approachability.")
    add("Jury Trial","Attorney","Male",5,"Navy hopsack","Muted burgundy foulard","Dark brown derby","Navy OTC","No cuff links","White linen square","Hopsack handles climate shifts across long multi-day trials.")
    add("Jury Trial","Attorney","Male",6,"Charcoal sharkskin","Black silk tie","Black oxford","Black OTC","Black enamel cuff links","None","Reserve sharkskin for high-profile trials where visual authority is paramount.")
    add("Jury Trial","Attorney","Female",1,"Charcoal gabardine pantsuit","N/A","Black cap-toe pump 2.5\"","Sheer nude hosiery","Pearl or gold stud earrings only — nothing that catches light","White silk TV fold","Pantsuit in gabardine projects undivided authority; pearls add civility without distraction.")
    add("Jury Trial","Attorney","Female",2,"Navy serge skirt suit (knee)","N/A","Black block heel pump","Sheer navy hosiery","Pearl or gold stud earrings only — nothing that catches light","None","Skirt suit at exact knee length is the female equivalent of the male navy serge standard.")
    add("Jury Trial","Attorney","Female",3,"Mid-grey fresco pantsuit","N/A","Black pointed flat","Sheer nude hosiery","Pearl or gold stud earrings only — nothing that catches light","Pale blue silk","Fresco pantsuit breathes through multi-day trials without losing structure.")
    add("Jury Trial","Attorney","Female",4,"Dark charcoal blazer + matching trousers","N/A","Low block heel","Sheer nude hosiery","Pearl stud earrings only","None","Matched separates in charcoal read as a suit — flexibility without sacrificing formality.")
    add("Jury Trial","Attorney","Female",5,"Navy sheath + structured blazer","N/A","Navy pump 2\"","Sheer navy hosiery","Small gold stud earrings","None","Sheath under blazer projects precision; navy communicates institutional reliability.")
    add("Jury Trial","Attorney","Female",6,"Charcoal skirt suit","N/A","Black kitten heel","Sheer grey hosiery","Pearl or gold stud earrings only","White linen","Kitten heels on long trial days reduce fatigue while maintaining full professional register.")
    add("Jury Trial","Client","Male",1,"Dark navy or charcoal suit","Conservative solid or stripe tie","Dark dress shoes, polished","Dark socks matching trousers","None","None","Dress as if meeting your bank manager — neat, dark, and respectful of the court.")
    add("Jury Trial","Client","Male",2,"Dark suit, single-breasted","Solid tie, subdued color","Black or dark brown lace-up shoes","Dark matching socks","None","None","Avoid bold patterns — you want the jury focused on your character, not your clothes.")
    add("Jury Trial","Client","Male",3,"Charcoal trousers + matching blazer","Conservative tie","Polished dress shoes","Dark socks","None","None","If you don't own a suit, matched separates in dark tones read nearly as well.")
    add("Jury Trial","Client","Male",4,"Navy trousers + navy blazer","Tie optional if blazer is sharp","Clean loafers or oxfords","Dark socks","None","None","Navy communicates honesty — consistently rated favorably by mock jurors.")
    add("Jury Trial","Client","Male",5,"Dark grey slacks + sport coat","No tie needed","Dark oxfords","Dark socks","None","None","A sport coat elevates your appearance without requiring a full suit.")
    add("Jury Trial","Client","Male",6,"Dark neat trousers + button-down shirt","No tie","Clean dark shoes","Dark socks","None","None","Last resort: at minimum wear dark, pressed, clean clothing — no jeans, no sneakers.")
    add("Jury Trial","Client","Female",1,"Dark navy or charcoal skirt suit or pantsuit","N/A","Conservative low heel or flat","Hosiery recommended","Minimal jewelry — small stud earrings only","None","Mirror your attorney's level of formality; understated and respectful reads best.")
    add("Jury Trial","Client","Female",2,"Dark blazer + matching trousers or skirt","N/A","Low block heel or flat","Hosiery or dark tights","Small stud earrings only","None","Matched separates in dark tones are court-appropriate and widely available.")
    add("Jury Trial","Client","Female",3,"Navy or charcoal sheath dress + blazer","N/A","Low heel","Hosiery recommended","Stud earrings only","None","A blazer over a sheath dress is one of the most universally readable professional looks.")
    add("Jury Trial","Client","Female",4,"Dark pressed trousers + neat blouse + blazer","N/A","Modest flat or low heel","Hosiery optional","Simple earrings","None","The blazer is the single most elevating item — even over casual trousers.")
    add("Jury Trial","Client","Female",5,"Dark skirt (knee length) + blouse","N/A","Modest flats","Hosiery recommended","Simple earrings","None","Keep the skirt at or below the knee; modest length reads respect for the proceeding.")
    add("Jury Trial","Client","Female",6,"Dark neat trousers + button-up blouse","N/A","Flat shoes, clean","Dark hosiery or socks","None","None","At minimum: dark, pressed, and modest — jewelry-free is fine at this level.")

    # ── BENCH TRIAL ──────────────────────────────────────────────────────────
    add("Bench Trial","Attorney","Male",1,"Charcoal fresco single-breasted","Midnight blue silk repp","Black cap-toe oxford","Black OTC wool","Gunmetal cuff links","White linen TV fold","Judges notice sartorial competence — fresco signals deliberate professionalism.")
    add("Bench Trial","Attorney","Male",2,"Navy serge","Steel blue grenadine","Black oxford","Navy OTC","Silver bar cuff links","White silk fold","Navy serge is universally legible to judicial audiences as the appropriate register.")
    add("Bench Trial","Attorney","Male",3,"Charcoal flannel","Burgundy foulard","Black derby","Charcoal OTC","Plain links","Pale grey puff","Flannel softens the visual read — useful when judicial temperament is unknown.")
    add("Bench Trial","Attorney","Male",4,"Mid-grey hopsack","Dark navy solid","Black oxford","Grey OTC","No links","White linen","Hopsack's texture adds interest without departing from bench-appropriate formality.")
    add("Bench Trial","Attorney","Male",5,"Dark navy sharkskin","Charcoal mogadore","Black oxford","Black OTC","Plain cuff links","None","Sharkskin before a judge you know — it signals investment in the proceeding.")
    add("Bench Trial","Attorney","Male",6,"Charcoal wool blend","Solid dark tie","Black shoes","Black OTC","None","None","A reliable fallback for any judicial temperament.")
    add("Bench Trial","Attorney","Female",1,"Charcoal fresco pantsuit","N/A","Black pump 2.5\"","Sheer nude","Pearl or gold stud earrings only — nothing that catches light","White linen fold","Fresco pantsuit is the female benchmark for bench appearances.")
    add("Bench Trial","Attorney","Female",2,"Navy serge skirt suit","N/A","Black block heel","Sheer navy","Pearl or gold stud earrings only — nothing that catches light","None","Classic navy signals unambiguous professional seriousness.")
    add("Bench Trial","Attorney","Female",3,"Charcoal blazer + matching trousers","N/A","Black flat","Sheer nude","Pearl studs only","Pale grey silk","Matched separates read as a suit — full stop.")
    add("Bench Trial","Attorney","Female",4,"Mid-grey pantsuit","N/A","Low block heel","Sheer grey","Pearl or gold studs","None","Grey reads scholarly — effective before academic or intellectually-oriented judges.")
    add("Bench Trial","Attorney","Female",5,"Navy sheath + blazer","N/A","Navy pump","Sheer navy","Small gold studs","None","Sheath dresses under blazers photograph cleanly for any courtroom media.")
    add("Bench Trial","Attorney","Female",6,"Dark skirt suit","N/A","Black kitten heel","Sheer nude","Pearl studs","White linen","Kitten heels remain floor-appropriate without sacrificing formality.")
    add("Bench Trial","Client","Male",1,"Dark suit","Conservative tie","Polished dark shoes","Dark socks","None","None","Judges read attire as a proxy for respect — dress to convey you take the proceeding seriously.")
    add("Bench Trial","Client","Male",2,"Navy blazer + dark trousers","Solid tie","Dark shoes","Dark socks","None","None","Blazer plus matching trousers is court-appropriate without requiring a full suit.")
    add("Bench Trial","Client","Male",3,"Dark separates","Tie optional","Dark shoes","Dark socks","None","None","Pressed and dark is the floor-level requirement.")
    add("Bench Trial","Client","Male",4,"Charcoal trousers + button-down","No tie","Dark shoes","Dark socks","None","None","If no jacket is available, at minimum wear a crisp button-down in a dark color.")
    add("Bench Trial","Client","Male",5,"Dark slacks + polo or neat shirt","No tie","Clean shoes","Matching socks","None","None","A polo in dark, solid color is marginally acceptable — avoid graphics or logos.")
    add("Bench Trial","Client","Male",6,"Clean dark trousers + any collared shirt","No tie","Clean footwear","Any socks","None","None","Bare minimum: collared, clean, dark, no jeans.")
    add("Bench Trial","Client","Female",1,"Dark suit or pantsuit","N/A","Low heel","Hosiery","Small studs only","None","Mirror your attorney in formality level wherever possible.")
    add("Bench Trial","Client","Female",2,"Dark blazer + trousers","N/A","Flat or low heel","Hosiery","Small earrings","None","A blazer is the single item that most elevates a civilian court appearance.")
    add("Bench Trial","Client","Female",3,"Dark sheath + blazer","N/A","Modest heel","Hosiery","None","None","Keep accessories minimal — nothing distracting.")
    add("Bench Trial","Client","Female",4,"Dark trousers + blouse","N/A","Flat","Socks or hosiery","None","None","Neat and dark is the reliable floor for any courtroom appearance.")
    add("Bench Trial","Client","Female",5,"Dark skirt + neat top","N/A","Flat","Hosiery recommended","None","None","Knee-length or below; avoid anything fitted or sheer.")
    add("Bench Trial","Client","Female",6,"Any dark pressed outfit","N/A","Clean footwear","Any","None","None","Pressed, modest, and dark is the irreducible minimum for a judge.")

    # ── DEPOSITION ────────────────────────────────────────────────────────────
    add("Deposition","Attorney","Male",1,"Navy fresco single-breasted","Silver mogadore","Black cap-toe oxford","Navy OTC","Gold oval cuff links","White silk TV fold","Deposition signals professional investment to opposing counsel — fresco at the top.")
    add("Deposition","Attorney","Male",2,"Charcoal serge","Steel blue repp","Black oxford","Charcoal OTC","Silver knot links","Pale blue puff","Charcoal serge is legible across any opposing firm's aesthetic preferences.")
    add("Deposition","Attorney","Male",3,"Mid-grey gabardine","Dark navy solid","Black derby","Grey OTC","Gunmetal links","None","Gabardine's tight weave holds shape during extended seated depositions.")
    add("Deposition","Attorney","Male",4,"Dark navy hopsack","Burgundy foulard","Black oxford","Navy OTC","No cuff links","White linen","Hopsack allows natural movement during lengthy questioning sessions.")
    add("Deposition","Attorney","Male",5,"Charcoal flannel","Muted stripe","Dark brown derby","Charcoal OTC","Plain links","None","Flannel softens visual tone for less adversarial deposition contexts.")
    add("Deposition","Attorney","Male",6,"Navy wool blend","Solid tie","Black shoes","Dark OTC","None","None","A reliable everyday option that reads professional without statement.")
    add("Deposition","Attorney","Female",1,"Navy fresco pantsuit","N/A","Black pump 2\"","Sheer navy","Pearl or gold stud earrings; one ring maximum","White silk fold","Navy fresco projects meticulous preparation — the deposition gold standard.")
    add("Deposition","Attorney","Female",2,"Charcoal serge skirt suit","N/A","Black block heel","Sheer nude","Pearl or gold stud earrings; one ring maximum","None","Skirt suit at knee reads appropriately formal for video-recorded depositions.")
    add("Deposition","Attorney","Female",3,"Mid-grey pantsuit","N/A","Black pointed flat","Sheer grey","Pearl or gold studs; one ring","Pale blue puff","Grey pantsuit reads scholarly authority — effective in document-intensive depositions.")
    add("Deposition","Attorney","Female",4,"Dark navy blazer + matching trousers","N/A","Low block heel","Sheer navy","Small stud earrings; one ring","None","Matched separates are indistinguishable from a suit in video depositions.")
    add("Deposition","Attorney","Female",5,"Charcoal sheath + blazer","N/A","Kitten heel","Sheer nude","Small gold studs","None","Sheath under blazer allows natural movement during extended questioning.")
    add("Deposition","Attorney","Female",6,"Navy straight-leg trousers + structured blazer","N/A","Flat","Sheer nude","Pearl studs","None","Trousers plus blazer is the reliable fallback for any deposition setting.")
    add("Deposition","Client","Male",1,"Dark suit","Conservative tie","Polished shoes","Dark socks","None","None","Dress as if testifying before a judge — the record includes your appearance.")
    add("Deposition","Client","Male",2,"Navy blazer + dark trousers","Solid tie","Dark shoes","Dark socks","None","None","Business professional is the appropriate register — no lower.")
    add("Deposition","Client","Male",3,"Dark separates","Tie optional","Dark shoes","Dark socks","None","None","Avoid casual clothing — opposing counsel notes everything.")
    add("Deposition","Client","Male",4,"Dark trousers + button-down","No tie","Dark shoes","Dark socks","None","None","At minimum: a neat button-down in a dark color.")
    add("Deposition","Client","Male",5,"Business casual separates","No tie","Clean shoes","Matching socks","None","None","Business casual is the minimum — avoid jeans or athletic wear.")
    add("Deposition","Client","Male",6,"Neat collared shirt + dark trousers","No tie","Clean shoes","Any socks","None","None","You are being recorded — dress accordingly.")
    add("Deposition","Client","Female",1,"Dark suit or pantsuit","N/A","Low heel","Hosiery","Small studs","None","You are on record — dress with the same care as a court appearance.")
    add("Deposition","Client","Female",2,"Dark blazer + trousers","N/A","Low heel","Hosiery","Small earrings","None","Professional and understated is the correct register.")
    add("Deposition","Client","Female",3,"Dark sheath + blazer","N/A","Modest heel","Hosiery","Small earrings","None","Keep everything modest; you may be videotaped.")
    add("Deposition","Client","Female",4,"Dark trousers + neat blouse","N/A","Flat","Socks","None","None","Neat and professional — avoid casual fabrics or loud patterns.")
    add("Deposition","Client","Female",5,"Dark skirt + blouse","N/A","Flat","Hosiery","None","None","Below the knee and modest is the reliable floor.")
    add("Deposition","Client","Female",6,"Any neat dark outfit","N/A","Flat footwear","Any","None","None","Pressed, dark, modest — the irreducible standard for any deposition.")

    # ── MEDIATION ─────────────────────────────────────────────────────────────
    add("Mediation","Attorney","Male",1,"Navy hopsack single-breasted","Burgundy grenadine","Dark brown derby","Navy OTC","No cuff links","White linen","Mediation calls for approachability — hopsack and derby soften without abandoning authority.")
    add("Mediation","Attorney","Male",2,"Mid-grey fresco","Muted blue foulard","Black oxford","Grey OTC","Silver bar links","Pale grey puff","Grey fresco balances gravitas with the cooperative tone mediation requires.")
    add("Mediation","Attorney","Male",3,"Charcoal wool flannel","Slate grenadine","Black derby","Charcoal OTC","Plain links","None","Flannel signals collaborative disposition — read the mediator's style first.")
    add("Mediation","Attorney","Male",4,"Navy wool blend","Solid blue tie","Brown loafer","Navy OTC","None","None","A loafer introduces appropriate informality for settlement-focused proceedings.")
    add("Mediation","Attorney","Male",5,"Mid-blue hopsack","No tie or open collar","Brown derby","Navy OTC","None","White pocket square","Without a tie, the jacket does the authoritative work — keep it structured.")
    add("Mediation","Attorney","Male",6,"Charcoal blazer + matching trousers","Tie optional","Dark loafer","Dark socks","None","None","Blazer and trousers is the minimum formal register for mediation.")
    add("Mediation","Attorney","Female",1,"Navy hopsack pantsuit","N/A","Dark brown block heel","Sheer navy","Pearl or gold stud earrings; one ring maximum","White linen","Navy hopsack softens visual register while maintaining professional command.")
    add("Mediation","Attorney","Female",2,"Mid-grey fresco skirt suit","N/A","Black kitten heel","Sheer grey","Pearl studs; one ring","Pale grey puff","Grey fresco reads scholarly and cooperative — effective in commercial mediations.")
    add("Mediation","Attorney","Female",3,"Charcoal blazer + matching skirt","N/A","Black flat","Sheer nude","Small stud earrings; one ring","None","A matched skirt suit signals investment while allowing natural movement.")
    add("Mediation","Attorney","Female",4,"Navy straight-leg trousers + blazer","N/A","Brown loafer heel","Sheer navy","Gold studs, a watch","None","Loafer heels introduce approachability appropriate for settlement conversations.")
    add("Mediation","Attorney","Female",5,"Mid-blue sheath + blazer","N/A","Block heel","Sheer blue","Gold or pearl earrings, a watch — nothing elaborate","None","A slightly lighter blue signals openness to resolution.")
    add("Mediation","Attorney","Female",6,"Charcoal separates","N/A","Flat or low heel","Sheer nude","Gold or pearl earrings, a watch — nothing elaborate","None","Reliable fallback — pressed and professional is sufficient.")
    add("Mediation","Client","Male",1,"Business professional suit","Conservative tie","Polished shoes","Dark socks","None","None","Your visual presentation signals whether you are serious about settlement.")
    add("Mediation","Client","Male",2,"Navy blazer + dark trousers","Tie optional","Dark shoes","Dark socks","None","None","Business professional reads readiness to negotiate in good faith.")
    add("Mediation","Client","Male",3,"Dark separates","No tie","Clean shoes","Dark socks","None","None","Neat business attire — mediation is less formal than court but still professional.")
    add("Mediation","Client","Male",4,"Dark trousers + button-down","No tie","Clean shoes","Matching socks","None","None","Business casual is the minimum — avoid anything too casual.")
    add("Mediation","Client","Male",5,"Neat chinos + collared shirt","No tie","Clean leather shoes","Matching socks","None","None","Mediation tolerates smart casual, but err on the side of more formal.")
    add("Mediation","Client","Male",6,"Clean collared shirt + trousers","No tie","Clean footwear","Any socks","None","None","At minimum: collared, pressed, and presentable.")
    add("Mediation","Client","Female",1,"Business professional attire","N/A","Low heel or flat","Hosiery","Small jewelry","None","Mediation rewards professional dress — it signals you're serious.")
    add("Mediation","Client","Female",2,"Dark blazer + trousers","N/A","Low heel","Hosiery","Small earrings","None","Approachable professionalism is the target register for mediation.")
    add("Mediation","Client","Female",3,"Dark sheath + blazer","N/A","Modest heel","Hosiery","Small earrings","None","Neat and professional — no louder than business professional.")
    add("Mediation","Client","Female",4,"Dark trousers + neat blouse","N/A","Flat","Any","Small earrings","None","Business casual is acceptable at this rank; stay neat and modest.")
    add("Mediation","Client","Female",5,"Smart casual separates","N/A","Flat or low heel","Any","Simple jewelry","None","Smart casual is sufficient for lower-stakes mediations.")
    add("Mediation","Client","Female",6,"Neat pressed outfit","N/A","Comfortable shoes","Any","None","None","Pressed and modest is the floor for any professional proceeding.")

    # ── OFFICE DAY ────────────────────────────────────────────────────────────
    add("Office Day","Attorney","Male",1,"Navy fresco suit","Silk repp tie","Dark brown derby","Navy OTC","No cuff links","White linen","Office day calls for polished but practical — fresco moves well and photographs cleanly.")
    add("Office Day","Attorney","Male",2,"Charcoal hopsack","Foulard tie","Black oxford","Charcoal OTC","None","Pale puff","Hopsack handles a full office day without visible wrinkling.")
    add("Office Day","Attorney","Male",3,"Mid-grey gabardine","Solid tie","Brown derby","Grey OTC","None","None","Gabardine's tight weave holds up across back-to-back internal meetings.")
    add("Office Day","Attorney","Male",4,"Navy wool blend suit","Open collar or no tie","Loafer","Navy OTC","None","None","Open collar on non-client days signals approachability to colleagues.")
    add("Office Day","Attorney","Male",5,"Charcoal flannel","No tie","Black loafer","Black OTC","None","None","Flannel without a tie reads relaxed authority for internal-only days.")
    add("Office Day","Attorney","Male",6,"Navy blazer + grey trousers","No tie","Brown derby","Grey OTC","None","None","Blazer and odd trouser is the office day standard when no client appearances are scheduled.")
    add("Office Day","Attorney","Female",1,"Navy fresco pantsuit","N/A","Dark brown block heel","Sheer navy","Gold or pearl earrings, a watch — nothing elaborate","White linen","Office day calls for structured but easy-moving — fresco pantsuit is the benchmark.")
    add("Office Day","Attorney","Female",2,"Charcoal hopsack skirt suit","N/A","Black kitten heel","Sheer nude","Gold or pearl earrings, a watch — nothing elaborate","Pale puff","Hopsack is the best all-day fabric for back-to-back office meetings.")
    add("Office Day","Attorney","Female",3,"Mid-grey trousers + structured blazer","N/A","Brown block heel","Sheer nude","Gold earrings, a watch","None","Separates allow more flexibility for varied office day commitments.")
    add("Office Day","Attorney","Female",4,"Navy sheath + blazer","N/A","Low pump","Sheer navy","Gold or pearl earrings, a watch — nothing elaborate","None","A sheath under blazer is the reliable standard for non-appearance office days.")
    add("Office Day","Attorney","Female",5,"Charcoal wide-leg trousers + blazer","N/A","Flat leather","Sheer or opaque","Gold or pearl earrings, a watch — nothing elaborate","None","Wide-leg trousers signal fashion awareness while maintaining professional register.")
    add("Office Day","Attorney","Female",6,"Neat blouse + matching trousers","N/A","Flat or low heel","Any","Simple jewelry","None","Neat separates with a blazer close at hand covers any unexpected client encounter.")
    add("Office Day","Client","Male",1,"Business professional","Tie optional","Polished shoes","Dark socks","None","None","Dress for the firm's culture, not just the calendar.")
    add("Office Day","Client","Male",2,"Smart business casual","No tie","Clean leather shoes","Matching socks","None","None","Business casual is the standard for most modern law firm offices.")
    add("Office Day","Client","Male",3,"Chinos + collared shirt + blazer","No tie","Clean shoes","Matching socks","None","None","Smart casual reads professional in casual office environments.")
    add("Office Day","Client","Male",4,"Chinos + neat polo","No tie","Clean leather shoes","Matching socks","None","None","Polo and chinos is smart casual floor — appropriate for internal office visits.")
    add("Office Day","Client","Male",5,"Dark jeans + neat collared shirt","No tie","Clean shoes","Matching socks","None","None","Dark jeans in a casual firm are acceptable if the shirt is crisp.")
    add("Office Day","Client","Male",6,"Clean casual wear","No tie","Clean footwear","Any","None","None","Casual office environments have wide latitude — avoid only very sloppy or revealing clothing.")
    add("Office Day","Client","Female",1,"Business professional","N/A","Low heel or flat","Hosiery","Simple jewelry","None","Match the firm's dress culture — when uncertain, go more formal.")
    add("Office Day","Client","Female",2,"Business casual separates","N/A","Low heel or flat","Any","Simple earrings","None","Business casual is the standard for most office visits.")
    add("Office Day","Client","Female",3,"Smart blouse + trousers or skirt","N/A","Flat","Any","Simple earrings","None","Smart casual covers most modern professional office environments.")
    add("Office Day","Client","Female",4,"Neat casual separates","N/A","Flat","Any","Simple jewelry","None","Neat and put-together is the minimum for any professional office.")
    add("Office Day","Client","Female",5,"Dark jeans + neat blouse","N/A","Clean shoes","Any","Simple jewelry","None","Dark jeans plus a neat top are acceptable in casual law firm environments.")
    add("Office Day","Client","Female",6,"Any neat casual outfit","N/A","Clean footwear","Any","None","None","Avoid only very casual or revealing clothing in any professional space.")

    # ── CLIENT MEETING ────────────────────────────────────────────────────────
    add("Client Meeting","Attorney","Male",1,"Navy serge single-breasted","Solid burgundy silk","Black cap-toe oxford","Navy OTC","Silver oval cuff links","White linen TV fold","Client meetings reward visual consistency — navy serge is universally trustworthy.")
    add("Client Meeting","Attorney","Male",2,"Charcoal gabardine","Steel blue repp","Black oxford","Charcoal OTC","Gunmetal cuff links","Pale blue puff","Charcoal signals seriousness appropriate for first meetings and high-stakes updates.")
    add("Client Meeting","Attorney","Male",3,"Mid-grey fresco","Muted foulard","Dark brown derby","Grey OTC","No cuff links","White silk","Fresco in mid-grey is approachable enough for nervous clients without sacrificing authority.")
    add("Client Meeting","Attorney","Male",4,"Navy hopsack","Solid silk tie","Brown loafer","Navy OTC","None","None","Loafer signals accessibility for ongoing relationship meetings.")
    add("Client Meeting","Attorney","Male",5,"Charcoal flannel","Tie optional","Black oxford","Charcoal OTC","None","None","Flannel without a tie works for casual ongoing client relationships.")
    add("Client Meeting","Attorney","Male",6,"Navy blazer + grey trousers","No tie","Brown derby","Navy OTC","None","None","Blazer and trousers for the most casual client relationships or internal-only days.")
    add("Client Meeting","Attorney","Female",1,"Navy serge skirt suit (knee)","N/A","Black pump 2\"","Sheer navy","Pearl or gold stud earrings; one ring maximum","White linen fold","First impressions: navy serge skirt suit reads competent, trustworthy, and invested.")
    add("Client Meeting","Attorney","Female",2,"Charcoal gabardine pantsuit","N/A","Black block heel","Sheer nude","Pearl or gold stud earrings; one ring maximum","Pale blue puff","Charcoal pantsuit signals gravity appropriate for high-stakes client updates.")
    add("Client Meeting","Attorney","Female",3,"Mid-grey fresco pantsuit","N/A","Dark brown block heel","Sheer grey","Pearl studs; one ring","White silk","Grey fresco reads approachable and scholarly — effective for ongoing advisory relationships.")
    add("Client Meeting","Attorney","Female",4,"Navy blazer + matching straight-leg trousers","N/A","Brown loafer heel","Sheer navy","Gold or pearl earrings, a watch — nothing elaborate","None","Loafer heel introduces slight informality appropriate for established client relationships.")
    add("Client Meeting","Attorney","Female",5,"Charcoal blazer + sheath dress","N/A","Kitten heel","Sheer nude","Gold or pearl earrings, a watch — nothing elaborate","None","Blazer over sheath is the flexible all-situation option for recurring client meetings.")
    add("Client Meeting","Attorney","Female",6,"Neat structured separates","N/A","Low heel or flat","Sheer or opaque","Gold or pearl earrings, a watch — nothing elaborate","None","Neat and structured covers any client meeting scenario as a reliable fallback.")
    add("Client Meeting","Client","Male",1,"Business professional","Conservative tie","Polished shoes","Dark socks","None","None","When meeting legal counsel, business professional reads seriousness about your matter.")
    add("Client Meeting","Client","Male",2,"Blazer + dark trousers","Tie optional","Dark shoes","Dark socks","None","None","Blazer plus trousers is widely appropriate for law firm visits.")
    add("Client Meeting","Client","Male",3,"Smart business casual","No tie","Clean shoes","Matching socks","None","None","Business casual is acceptable for most client meeting contexts.")
    add("Client Meeting","Client","Male",4,"Chinos + neat button-down","No tie","Clean leather shoes","Matching socks","None","None","Smart casual reads appropriately for informal or ongoing-relationship visits.")
    add("Client Meeting","Client","Male",5,"Smart casual","No tie","Clean shoes","Matching socks","None","None","Most modern law firms accommodate smart casual for established client relationships.")
    add("Client Meeting","Client","Male",6,"Neat collared casual","No tie","Clean footwear","Any","None","None","At minimum: collared, clean, and presentable.")
    add("Client Meeting","Client","Female",1,"Business professional","N/A","Low heel","Hosiery","Modest jewelry","None","Dress professionally — your attorney represents you; your appearance supports that narrative.")
    add("Client Meeting","Client","Female",2,"Business casual suit or blazer","N/A","Low heel or flat","Any","Simple earrings","None","A blazer over separates elevates any law firm visit.")
    add("Client Meeting","Client","Female",3,"Smart separates","N/A","Flat or low heel","Any","Simple earrings","None","Smart and neat covers most client meeting scenarios comfortably.")
    add("Client Meeting","Client","Female",4,"Neat blouse + trousers or skirt","N/A","Flat","Any","Simple jewelry","None","Business casual is widely accepted — avoid only very casual fabrics.")
    add("Client Meeting","Client","Female",5,"Smart casual separates","N/A","Flat","Any","Any modest jewelry","None","Smart casual is appropriate for most ongoing relationship meetings.")
    add("Client Meeting","Client","Female",6,"Neat pressed outfit","N/A","Clean footwear","Any","None","None","Neat and put-together is always sufficient for a law office visit.")

    # ── SETTLEMENT CONFERENCE ─────────────────────────────────────────────────
    add("Settlement Conference","Attorney","Male",1,"Navy fresco","Muted repp tie","Black oxford","Navy OTC","Silver cuff links","White linen","Settlement conferences reward professional authority tempered with approachability.")
    add("Settlement Conference","Attorney","Male",2,"Charcoal gabardine","Steel blue foulard","Black derby","Charcoal OTC","Gunmetal links","Pale puff","Gabardine signals meticulous preparation — effective when leverage matters.")
    add("Settlement Conference","Attorney","Male",3,"Mid-grey serge","Solid navy tie","Brown derby","Grey OTC","No links","White silk","Mid-grey invites collaborative settlement discussion without ceding authority.")
    add("Settlement Conference","Attorney","Male",4,"Navy hopsack","Burgundy tie","Black oxford","Navy OTC","None","None","Hopsack reads ready to resolve — without appearing eager.")
    add("Settlement Conference","Attorney","Male",5,"Charcoal flannel","No tie","Dark loafer","Black OTC","None","None","Flannel without tie signals willingness to settle without formal posturing.")
    add("Settlement Conference","Attorney","Male",6,"Navy blazer + dark trousers","No tie","Derby","Dark OTC","None","None","Reliable professional fallback for any settlement context.")
    add("Settlement Conference","Attorney","Female",1,"Navy fresco pantsuit","N/A","Black pump 2\"","Sheer navy","Pearl or gold stud earrings; one ring maximum","White linen","Authority and approachability in equal measure — fresco navy pantsuit achieves both.")
    add("Settlement Conference","Attorney","Female",2,"Charcoal gabardine skirt suit","N/A","Black block heel","Sheer nude","Pearl or gold stud earrings; one ring maximum","Pale puff","Skirt suit signals formality calibrated to the stakes of the settlement.")
    add("Settlement Conference","Attorney","Female",3,"Mid-grey blazer + matching trousers","N/A","Brown block heel","Sheer grey","Pearl studs; one ring","White silk","Grey invites resolution; brown heel softens visual authority appropriately.")
    add("Settlement Conference","Attorney","Female",4,"Navy hopsack separates","N/A","Low block heel","Sheer navy","Gold or pearl earrings, a watch — nothing elaborate","None","Hopsack reads ready to resolve without signaling submission.")
    add("Settlement Conference","Attorney","Female",5,"Charcoal sheath + blazer","N/A","Kitten heel","Sheer nude","Gold or pearl earrings, a watch — nothing elaborate","None","Classic professional register — covers any settlement conference dynamic.")
    add("Settlement Conference","Attorney","Female",6,"Neat structured blazer + separates","N/A","Flat","Sheer nude","Gold or pearl earrings, a watch — nothing elaborate","None","Reliable and professional in any context.")
    add("Settlement Conference","Client","Male",1,"Business professional suit","Conservative tie","Polished shoes","Dark socks","None","None","How you dress signals how seriously you take settlement — dress professionally.")
    add("Settlement Conference","Client","Male",2,"Blazer + dark trousers","Tie optional","Dark shoes","Dark socks","None","None","Professional appearance supports your negotiating credibility.")
    add("Settlement Conference","Client","Male",3,"Smart business casual","No tie","Clean shoes","Dark socks","None","None","Business casual is appropriate for most settlement contexts.")
    add("Settlement Conference","Client","Male",4,"Chinos + button-down","No tie","Clean shoes","Matching socks","None","None","Neat and professional — avoid looking like you don't care.")
    add("Settlement Conference","Client","Male",5,"Smart casual","No tie","Clean leather shoes","Matching socks","None","None","Smart casual is the minimum for settlement discussions.")
    add("Settlement Conference","Client","Male",6,"Neat collared casual","No tie","Clean footwear","Any","None","None","At minimum: clean, pressed, and respectful.")
    add("Settlement Conference","Client","Female",1,"Business professional","N/A","Low heel","Hosiery","Modest jewelry","None","Professional dress supports your position at the settlement table.")
    add("Settlement Conference","Client","Female",2,"Blazer + separates","N/A","Low heel","Any","Simple earrings","None","A blazer elevates any negotiation appearance.")
    add("Settlement Conference","Client","Female",3,"Smart casual separates","N/A","Flat or low heel","Any","Simple earrings","None","Neat and professional is appropriate for most settlement contexts.")
    add("Settlement Conference","Client","Female",4,"Neat blouse + trousers","N/A","Flat","Any","Simple jewelry","None","Business casual is sufficient for most settlement conferences.")
    add("Settlement Conference","Client","Female",5,"Smart casual","N/A","Flat","Any","Simple jewelry","None","Smart casual is the minimum register for any settlement proceeding.")
    add("Settlement Conference","Client","Female",6,"Any neat pressed outfit","N/A","Clean footwear","Any","None","None","Pressed, modest, professional — always appropriate.")

    # ── ARBITRATION ───────────────────────────────────────────────────────────
    add("Arbitration","Attorney","Male",1,"Charcoal gabardine","Burgundy repp","Black cap-toe oxford","Black OTC","Gold bar cuff links","White linen TV fold","Arbitrators often come from specific industry backgrounds — read them before proceeding.")
    add("Arbitration","Attorney","Male",2,"Navy serge","Steel blue grenadine","Black oxford","Navy OTC","Silver knot links","White silk fold","Navy serge is universally safe across arbitrator backgrounds.")
    add("Arbitration","Attorney","Male",3,"Mid-grey fresco","Muted foulard","Black derby","Grey OTC","Gunmetal links","Pale puff","Mid-grey reads technical competence — effective before financial or engineering arbitrators.")
    add("Arbitration","Attorney","Male",4,"Dark navy hopsack","Solid silk tie","Black oxford","Navy OTC","No links","White linen","Hopsack for multi-day arbitration proceedings — holds shape under sustained wear.")
    add("Arbitration","Attorney","Male",5,"Charcoal flannel","Muted stripe","Brown derby","Charcoal OTC","Plain links","None","Flannel softens formality appropriate for domestic or less adversarial arbitrations.")
    add("Arbitration","Attorney","Male",6,"Navy wool blend","Solid tie","Black shoes","Dark OTC","None","None","Reliable professional standard across any arbitration context.")
    add("Arbitration","Attorney","Female",1,"Charcoal gabardine pantsuit","N/A","Black pump 2.5\"","Sheer nude","Pearl or gold stud earrings; one ring maximum","White linen fold","Arbitrators respond to visual authority signals — gabardine pantsuit delivers both.")
    add("Arbitration","Attorney","Female",2,"Navy serge skirt suit","N/A","Black block heel","Sheer navy","Pearl or gold stud earrings; one ring maximum","White silk","Navy serge is the safe, universally effective choice across arbitrator profiles.")
    add("Arbitration","Attorney","Female",3,"Mid-grey fresco pantsuit","N/A","Black flat","Sheer grey","Pearl studs; one ring","Pale puff","Grey fresco reads technical precision — effective before transactional arbitrators.")
    add("Arbitration","Attorney","Female",4,"Dark navy hopsack separates","N/A","Low block heel","Sheer navy","Small stud earrings; one ring","None","Hopsack for multi-day arbitration — maintains structure throughout.")
    add("Arbitration","Attorney","Female",5,"Charcoal blazer + sheath","N/A","Kitten heel","Sheer nude","Pearl or gold studs","None","Classic professional register for any arbitration dynamic.")
    add("Arbitration","Attorney","Female",6,"Structured separates in dark tones","N/A","Flat","Sheer nude","Pearl studs","None","Reliable fallback — structured and dark covers any arbitration context.")
    add("Arbitration","Client","Male",1,"Business professional suit","Conservative tie","Polished shoes","Dark socks","None","None","Arbitration is quasi-judicial — dress as you would for court.")
    add("Arbitration","Client","Male",2,"Blazer + dark trousers","Tie optional","Dark shoes","Dark socks","None","None","Professional dress signals respect for the arbitration process.")
    add("Arbitration","Client","Male",3,"Smart business casual","No tie","Clean shoes","Dark socks","None","None","Business casual is appropriate for less formal arbitrations.")
    add("Arbitration","Client","Male",4,"Chinos + button-down","No tie","Clean shoes","Matching socks","None","None","Neat casual is acceptable for informal arbitration proceedings.")
    add("Arbitration","Client","Male",5,"Smart casual","No tie","Clean shoes","Matching socks","None","None","Smart casual signals basic professional engagement.")
    add("Arbitration","Client","Male",6,"Neat collared attire","No tie","Clean footwear","Any","None","None","Collared and pressed is the minimum standard.")
    add("Arbitration","Client","Female",1,"Business professional","N/A","Low heel","Hosiery","Modest jewelry","None","Dress for arbitration as you would for court — it carries similar weight.")
    add("Arbitration","Client","Female",2,"Blazer + separates","N/A","Low heel","Any","Simple earrings","None","Professional attire supports your credibility in the arbitration record.")
    add("Arbitration","Client","Female",3,"Smart separates","N/A","Flat or low heel","Any","Simple earrings","None","Neat and professional is appropriate for most arbitration settings.")
    add("Arbitration","Client","Female",4,"Neat blouse + trousers","N/A","Flat","Any","Simple jewelry","None","Business casual covers most non-formal arbitration proceedings.")
    add("Arbitration","Client","Female",5,"Smart casual separates","N/A","Flat","Any","Simple jewelry","None","Smart casual is the minimum for any arbitration context.")
    add("Arbitration","Client","Female",6,"Any neat pressed outfit","N/A","Clean footwear","Any","None","None","Pressed and modest is always acceptable.")

    # ── APPELLATE ARGUMENT ────────────────────────────────────────────────────
    add("Appellate Argument","Attorney","Male",1,"Charcoal gabardine two-button","Midnight blue silk repp","Black cap-toe oxford","Black OTC","Gold oval cuff links","White linen TV fold","Appellate courts demand maximum visual authority — charcoal gabardine with gold links is the benchmark.")
    add("Appellate Argument","Attorney","Male",2,"Navy serge single-breasted","Burgundy grenadine","Black oxford","Navy OTC","Silver knot cuff links","White silk fold","Navy serge signals institutional legitimacy — a universal appellate choice.")
    add("Appellate Argument","Attorney","Male",3,"Charcoal fresco","Steel blue mogadore","Black oxford","Charcoal OTC","Gunmetal cuff links","Pale blue puff","Fresco in charcoal holds shape during extended standing arguments.")
    add("Appellate Argument","Attorney","Male",4,"Mid-grey gabardine","Dark navy solid","Black derby","Grey OTC","Plain silver links","White linen","Mid-grey projects scholarly authority appropriate for academic appellate panels.")
    add("Appellate Argument","Attorney","Male",5,"Dark navy sharkskin","Charcoal silk tie","Black oxford","Black OTC","Black enamel links","None","Sharkskin at the appellate level signals serious investment in the proceeding.")
    add("Appellate Argument","Attorney","Male",6,"Navy flannel","Solid burgundy tie","Black oxford","Navy OTC","Silver links","White pocket square","Flannel adds gravitas while remaining well within appellate dress expectations.")
    add("Appellate Argument","Attorney","Female",1,"Charcoal gabardine pantsuit","N/A","Black pump 2.5\"","Sheer nude","Pearl or gold stud earrings only — nothing that catches light","White linen fold","Appellate panels notice everything — charcoal gabardine with pearl studs is the gold standard.")
    add("Appellate Argument","Attorney","Female",2,"Navy serge skirt suit (knee)","N/A","Black block heel 2\"","Sheer navy","Pearl or gold stud earrings only — nothing that catches light","White silk fold","Navy serge signals the gravity of appellate proceedings — universally appropriate.")
    add("Appellate Argument","Attorney","Female",3,"Charcoal fresco pantsuit","N/A","Black pointed flat","Sheer nude","Pearl or gold stud earrings only — nothing that catches light","Pale blue puff","Fresco holds shape through extended standing arguments before multi-judge panels.")
    add("Appellate Argument","Attorney","Female",4,"Mid-grey gabardine suit","N/A","Black pump 2\"","Sheer grey","Pearl studs only","White linen","Grey gabardine reads scholarly authority — effective before academic appellate panels.")
    add("Appellate Argument","Attorney","Female",5,"Dark navy sharkskin pantsuit","N/A","Black heel 2\"","Sheer navy","Pearl or gold stud earrings only","None","Sharkskin signals maximum investment for high-profile appellate arguments.")
    add("Appellate Argument","Attorney","Female",6,"Navy flannel suit","N/A","Black kitten heel","Sheer navy","Pearl stud earrings only","White pocket square","Flannel adds warmth while remaining within the strictest appellate dress standards.")
    add("Appellate Argument","Client","Male",1,"Dark formal suit","Conservative tie","Polished shoes","Dark socks","None","None","Appellate courts are formal — dress as you would for any superior court proceeding.")
    add("Appellate Argument","Client","Male",2,"Blazer + dark formal trousers","Conservative tie","Polished shoes","Dark socks","None","None","Formal business attire is appropriate for appellate spectators and participants.")
    add("Appellate Argument","Client","Male",3,"Business professional","Tie optional","Dark shoes","Dark socks","None","None","Professional dress is the minimum for appellate proceedings.")
    add("Appellate Argument","Client","Male",4,"Dark smart casual","No tie","Clean leather shoes","Dark socks","None","None","Smart casual is acceptable for appellate observers.")
    add("Appellate Argument","Client","Male",5,"Smart casual","No tie","Clean shoes","Matching socks","None","None","Smart casual is the minimum for appellate court attendance.")
    add("Appellate Argument","Client","Male",6,"Neat collared attire","No tie","Clean footwear","Any","None","None","Collared and pressed for any appellate appearance.")
    add("Appellate Argument","Client","Female",1,"Business professional formal","N/A","Low heel","Hosiery","Minimal jewelry","None","Appellate courts are formal — dress as you would for any serious court proceeding.")
    add("Appellate Argument","Client","Female",2,"Dark suit or formal separates","N/A","Low heel","Hosiery","Small earrings","None","Formal and conservative is the reliable standard for appellate proceedings.")
    add("Appellate Argument","Client","Female",3,"Dark blazer + formal trousers","N/A","Modest heel","Hosiery","Small earrings","None","Professional dress signals respect for the appellate process.")
    add("Appellate Argument","Client","Female",4,"Dark neat separates","N/A","Flat","Any","Simple earrings","None","Business casual is appropriate for appellate observers.")
    add("Appellate Argument","Client","Female",5,"Smart casual separates","N/A","Flat","Any","Simple jewelry","None","Smart casual is the minimum for appellate court attendance.")
    add("Appellate Argument","Client","Female",6,"Any neat dark outfit","N/A","Clean footwear","Any","None","None","Dark, pressed, and modest is always appropriate.")

    # ── NETWORKING EVENT ──────────────────────────────────────────────────────
    add("Networking Event","Attorney","Male",1,"Navy fresco single-breasted","Silk grenadine in interest color","Dark brown suede derby","Navy OTC","Enamel or fabric cuff links","Silk puff in accent color","Networking events allow sartorial personality — one expressive element lifts the entire look.")
    add("Networking Event","Attorney","Male",2,"Charcoal hopsack","Printed silk tie","Brown leather derby","Charcoal OTC","Silver chain links","Pocket square with pattern","Hopsack moves well through a room; a printed tie opens conversations.")
    add("Networking Event","Attorney","Male",3,"Mid-grey fresco","Knit tie in burgundy or green","Brown suede loafer","Grey OTC","No cuff links","Textured silk puff","A knit tie at networking strikes precisely the right note between authority and personality.")
    add("Networking Event","Attorney","Male",4,"Navy wool","Open collar","Brown suede monk","Navy OTC","None","None","Without a tie the jacket carries the look — keep it structured and the collar crisp.")
    add("Networking Event","Attorney","Male",5,"Charcoal blazer + coordinating trousers","Open collar","Brown derby","Coordinating socks","None","None","Blazer and complementary trouser is the networking standard when no suit is required.")
    add("Networking Event","Attorney","Male",6,"Smart blazer + open collar","No tie","Clean leather shoe","Any coordinating socks","None","None","The most casual but professional option for low-formality networking.")
    add("Networking Event","Attorney","Female",1,"Navy fresco pantsuit","N/A","Brown suede heel","Sheer navy","Gold or pearl earrings, a delicate necklace or bracelet","Silk puff in accent color","Networking allows personality — one jewelry piece or accessory makes you memorable.")
    add("Networking Event","Attorney","Female",2,"Charcoal hopsack blazer + coordinating trousers","N/A","Brown leather heel","Sheer nude","Gold or pearl earrings, a delicate necklace or bracelet","Textured silk puff","Separates allow expressive coordination appropriate for evening networking.")
    add("Networking Event","Attorney","Female",3,"Mid-grey fresco skirt suit","N/A","Brown suede block heel","Sheer grey","Gold or pearl earrings, a delicate necklace or bracelet","None","A delicate necklace at networking completes the look without competing with conversation.")
    add("Networking Event","Attorney","Female",4,"Navy blazer + coordinating dress","N/A","Brown suede heel","Sheer navy","Gold earrings, delicate necklace","None","A blazer over a dress threads the professional-social needle at networking events.")
    add("Networking Event","Attorney","Female",5,"Charcoal wide-leg trousers + structured blouse","N/A","Block heel or loafer","Opaque or sheer","Gold or pearl earrings, a delicate necklace or bracelet","None","Wide-leg trousers signal fashion confidence appropriate for bar and firm networking.")
    add("Networking Event","Attorney","Female",6,"Smart blazer + smart casual separates","N/A","Low heel or flat","Any","Gold or pearl earrings, a delicate necklace or bracelet","None","Smart casual with one jewelry statement is the minimum for professional networking.")
    add("Networking Event","Client","Male",1,"Business casual or smart casual","Tie optional","Clean leather shoes","Matching socks","None","None","Dress to the level of the event — when uncertain, err toward business casual.")
    add("Networking Event","Client","Male",2,"Blazer + chinos or smart trousers","No tie","Clean shoes","Matching socks","None","None","Blazer plus chinos is the universal smart casual standard for networking.")
    add("Networking Event","Client","Male",3,"Smart casual separates","No tie","Clean leather shoes","Matching socks","None","None","Smart casual is widely appropriate for most legal networking events.")
    add("Networking Event","Client","Male",4,"Chinos + neat collared shirt","No tie","Clean shoes","Matching socks","None","None","Neat casual is acceptable for informal networking gatherings.")
    add("Networking Event","Client","Male",5,"Smart casual","No tie","Clean shoes","Any","None","None","Any smart casual outfit is appropriate for casual networking.")
    add("Networking Event","Client","Male",6,"Neat casual outfit","No tie","Clean footwear","Any","None","None","Clean and presentable is sufficient for the most informal networking events.")
    add("Networking Event","Client","Female",1,"Business casual or cocktail attire","N/A","Modest heel or flat","Any","Any","None","Match the event's level — networking events allow more personal expression.")
    add("Networking Event","Client","Female",2,"Smart separates or blouse + trousers","N/A","Low heel or flat","Any","Any modest jewelry","None","Smart casual is broadly appropriate for most legal networking events.")
    add("Networking Event","Client","Female",3,"Neat blouse + trousers or skirt","N/A","Flat or low heel","Any","Simple jewelry","None","Neat and put-together is appropriate across most networking contexts.")
    add("Networking Event","Client","Female",4,"Smart casual dress or separates","N/A","Flat","Any","Any","None","Smart casual is the reliable floor for networking events of any formality level.")
    add("Networking Event","Client","Female",5,"Any smart casual outfit","N/A","Flat or low heel","Any","Any","None","Networking tolerates a wide range — avoid only very casual or work-wear clothing.")
    add("Networking Event","Client","Female",6,"Any neat casual outfit","N/A","Clean footwear","Any","Any","None","Clean and presentable is sufficient for informal networking gatherings.")

    return W

WARDROBE = build_wardrobe()

# ── Weather ───────────────────────────────────────────────────────────────────

WMO_CODES = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Icy fog", "🌫️"),
    51: ("Light drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Heavy drizzle", "🌧️"),
    61: ("Light rain", "🌧️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "🌨️"), 73: ("Snow", "🌨️"), 75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌦️"), 81: ("Showers", "🌧️"), 82: ("Violent showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm + hail", "⛈️"),
}

def get_weather(lat, lon):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,weathercode,windspeed_10m"
            f"&temperature_unit=fahrenheit&windspeed_unit=mph"
        )
        r = requests.get(url, timeout=5)
        data = r.json()["current"]
        code = data["weathercode"]
        desc, icon = WMO_CODES.get(code, ("Unknown", "🌡️"))
        return {
            "temp_f": round(data["temperature_2m"]),
            "humidity": data["relative_humidity_2m"],
            "precip": data["precipitation"],
            "wind_mph": round(data["windspeed_10m"]),
            "description": desc,
            "icon": icon,
        }
    except Exception:
        return None

def get_location_name(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        r = requests.get(url, headers={"User-Agent": "HueProcess/1.0"}, timeout=5)
        d = r.json()
        addr = d.get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village") or ""
        state = addr.get("state", "")
        return f"{city}, {state}".strip(", ") if city else state or "Your location"
    except Exception:
        return "Your location"

def weather_adjustments(w):
    notes = []
    t = w["temp_f"]
    if t < 32:
        notes.append("🧥 Below freezing — add a heavyweight overcoat; consider cashmere liner gloves.")
    elif t < 45:
        notes.append("🧥 Cold — a wool overcoat is essential. Merino undershirt recommended.")
    elif t < 55:
        notes.append("🧣 Cool — a light overcoat or heavy sport coat layer is advisable.")
    elif t > 85:
        notes.append("🌡️ Hot — choose open-weave fabrics (fresco, hopsack, tropical wool). Avoid flannel.")
    elif t > 75:
        notes.append("☀️ Warm — lighter-weight fabrics recommended. Pocket square optional.")
    if w["precip"] > 0.1:
        notes.append("☔ Rain expected — rubber-soled shoes strongly recommended. Protect suede.")
    elif w["precip"] > 0:
        notes.append("🌂 Light rain possible — pack a compact umbrella.")
    if w["wind_mph"] > 20:
        notes.append("💨 Windy — secure pocket square tightly; avoid open-collar looks outdoors.")
    if w["humidity"] > 75:
        notes.append("💧 High humidity — fresco and hopsack fabrics resist heat-humidity wilting.")
    if not notes:
        notes.append("✅ Favorable conditions — no wardrobe modifications needed.")
    return notes

# ── Closet Analysis ───────────────────────────────────────────────────────────

def analyze_closet_image(image_bytes, media_type):
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "model": "claude-opus-4-5",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": (
                    "Analyze this wardrobe photo. Identify every clothing item visible. "
                    "Return ONLY a JSON object with these keys: "
                    "suits, ties, shoes, socks, cuff_links, pocket_squares, jewelry, "
                    "blazers, trousers, dresses, blouses. "
                    "Each key maps to a list of description strings (color + material + pattern). "
                    "Empty list if none found. No markdown, no preamble, just raw JSON."
                )}
            ]
        }]
    }
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        text = r.json()["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return {}

def closet_matches(field, value, inventory):
    if not inventory or not value or value.lower() in ("none", "n/a", ""):
        return False
    val_lower = value.lower()
    field_map = {
        "suit": ["suits", "blazers", "trousers", "dresses", "blouses"],
        "tie": ["ties"],
        "shoes": ["shoes"],
        "socks": ["socks"],
        "accessories": ["cuff_links", "jewelry"],
        "pocket_square": ["pocket_squares"],
    }
    keywords = [w for w in val_lower.split() if len(w) > 3]
    for cat in field_map.get(field, []):
        for item in inventory.get(cat, []):
            if any(kw in item.lower() for kw in keywords):
                return True
    return False

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="hp-title" style="font-size:1.6rem;">⚖️ Hue Process</div>', unsafe_allow_html=True)
    st.markdown('<div class="hp-subtitle">Legal Attire Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<hr class="hp-divider">', unsafe_allow_html=True)

    case_type = st.selectbox("Case Type", CASE_TYPES)
    role = st.radio("Role", ["Attorney", "Client"], horizontal=True)
    gender = st.radio("Gender", ["Male", "Female"], horizontal=True)

    st.markdown('<hr class="hp-divider">', unsafe_allow_html=True)
    st.markdown('<div class="weather-label">🌤 Weather</div>', unsafe_allow_html=True)

    use_weather = st.toggle("Enable weather context", value=True)
    weather_data = None
    weather_location = ""

    if use_weather:
        col_lat, col_lon = st.columns(2)
        lat = col_lat.number_input("Lat", value=36.17, format="%.2f")
        lon = col_lon.number_input("Lon", value=-86.78, format="%.2f")
        if st.button("Get Weather"):
            with st.spinner("Fetching…"):
                weather_data = get_weather(lat, lon)
                weather_location = get_location_name(lat, lon)
                st.session_state["weather"] = weather_data
                st.session_state["weather_loc"] = weather_location
        elif "weather" in st.session_state:
            weather_data = st.session_state["weather"]
            weather_location = st.session_state.get("weather_loc", "")

    st.markdown('<hr class="hp-divider">', unsafe_allow_html=True)
    ranks_to_show = st.slider("Options to show", 1, 6, 6)

# ── Main ──────────────────────────────────────────────────────────────────────

st.markdown(
    '<div class="hp-title">Hue Process</div>'
    '<div class="hp-subtitle">Sartorial intelligence for legal professionals</div>'
    '<hr class="hp-divider">',
    unsafe_allow_html=True
)

# Weather panel
if weather_data:
    adj = weather_adjustments(weather_data)
    st.markdown(f"""
    <div class="weather-box">
      <div style="display:flex;align-items:baseline;gap:1rem;flex-wrap:wrap;">
        <span class="weather-temp">{weather_data['icon']} {weather_data['temp_f']}°F</span>
        <span style="color:#8fa8c8;font-size:0.9rem;">{weather_data['description']} · {weather_location}</span>
        <span style="color:#7a94b0;font-size:0.82rem;">💧 {weather_data['humidity']}% · 💨 {weather_data['wind_mph']} mph</span>
      </div>
      {''.join(f'<div class="weather-adj">{a}</div>' for a in adj)}
    </div>
    """, unsafe_allow_html=True)

# Formality header
formality_map = {
    "Jury Trial": ("Maximum", "#c9a84c"),
    "Bench Trial": ("Maximum", "#c9a84c"),
    "Appellate Argument": ("Maximum", "#c9a84c"),
    "Deposition": ("High", "#8fa8c8"),
    "Settlement Conference": ("High", "#8fa8c8"),
    "Arbitration": ("High", "#8fa8c8"),
    "Client Meeting": ("Moderate", "#7fb8a4"),
    "Mediation": ("Moderate", "#7fb8a4"),
    "Office Day": ("Professional", "#9090b8"),
    "Networking Event": ("Flexible", "#b08080"),
}
formality, f_color = formality_map.get(case_type, ("Standard", "#8fa8c8"))

st.markdown(f"""
<div style="display:flex;align-items:baseline;gap:1rem;margin-bottom:0.3rem;flex-wrap:wrap;">
  <span class="section-head">{case_type}</span>
  <span style="font-size:0.72rem;color:{f_color};text-transform:uppercase;letter-spacing:0.12em;
        border:1px solid {f_color}55;padding:2px 10px;border-radius:20px;">{formality} Formality</span>
  <span style="font-size:0.78rem;color:#7a94b0;">{role} · {gender}</span>
</div>
""", unsafe_allow_html=True)

# Get outfits
outfits = WARDROBE.get(case_type, {}).get(role, {}).get(gender, [])
outfits_sorted = sorted(outfits, key=lambda o: o.rank)[:ranks_to_show]
inventory = st.session_state.get("closet", {})

if not outfits_sorted:
    st.warning("No recommendations found for this combination.")
else:
    for o in outfits_sorted:
        rank_label = "Top Pick" if o.rank == 1 else f"Option {o.rank}"
        card_class = "option-card rank-1" if o.rank == 1 else "option-card"

        fields = [
            ("suit", "Suit / Attire", o.suit),
            ("tie", "Tie / Neckwear", o.tie),
            ("shoes", "Shoes", o.shoes),
            ("socks", "Hosiery / Socks", o.socks),
            ("accessories", "Jewelry" if gender == "Female" else "Cuff Links / Accessories", o.accessories),
            ("pocket_square", "Pocket Square", o.pocket_square),
        ]

        def field_html(fname, label, value):
            if not value or value.lower() in ("none", "n/a", ""):
                return ""
            reasoning = get_reasoning(fname, value)
            r_html = f'<div class="item-reasoning">{reasoning}</div>' if reasoning else ""
            if inventory:
                match = closet_matches(fname, value, inventory)
                icon = "✅ " if match else "🟠 "
            else:
                icon = ""
            return f'<div class="item-label">{label}</div><div class="item-value">{icon}{value}</div>{r_html}'

        # Match percentage badge
        if inventory:
            all_fields = [(fn, val) for fn, _, val in fields if val and val.lower() not in ("none", "n/a", "")]
            matched = sum(1 for fn, val in all_fields if closet_matches(fn, val, inventory))
            pct = round((matched / len(all_fields)) * 100) if all_fields else 0
            pct_badge = f' · <span style="color:#4a8c6a;">{pct}% match</span>'
        else:
            pct_badge = ""

        fields_html = "".join(field_html(fn, lbl, val) for fn, lbl, val in fields)
        note_html = (
            f'<div style="margin-top:0.6rem;padding-top:0.6rem;border-top:1px solid #c9a84c22;'
            f'font-size:0.78rem;color:#8fa8c8;font-style:italic;">{o.strategic_note}</div>'
        ) if o.strategic_note else ""

        st.markdown(f"""
        <div class="{card_class}">
          <div class="rank-badge">{rank_label}{pct_badge}</div>
          <div style="margin-top:0.6rem;">{fields_html}{note_html}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Closet Upload ─────────────────────────────────────────────────────────────

st.markdown('<hr class="hp-divider">', unsafe_allow_html=True)
st.markdown('<div class="section-head">👔 My Closet</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">Upload photos of your wardrobe — Claude will identify what you own and highlight matches above.</div>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload wardrobe photos",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

if uploaded_files:
    cols = st.columns(min(len(uploaded_files), 4))
    for i, f in enumerate(uploaded_files):
        cols[i % 4].image(f, use_column_width=True)

    if st.button("🔍 Analyze My Closet"):
        new_inventory = {}
        with st.spinner("Analyzing your wardrobe with AI..."):
            for f in uploaded_files:
                img_bytes = f.read()
                result = analyze_closet_image(img_bytes, f.type)
                for k, v in result.items():
                    existing = new_inventory.get(k, [])
                    for item in v:
                        if item.lower() not in [x.lower() for x in existing]:
                            existing.append(item)
                    new_inventory[k] = existing
        st.session_state["closet"] = new_inventory
        st.success("✅ Closet analyzed! Scroll up to see matches highlighted on your outfit cards.")
        st.rerun()

if inventory:
    st.markdown("**Items identified in your closet:**")
    for cat, items in inventory.items():
        if items:
            st.markdown(f"- **{cat.replace('_', ' ').title()}**: {', '.join(items)}")
    if st.button("🗑️ Clear Closet"):
        del st.session_state["closet"]
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown(
    '<hr class="hp-divider"><div style="font-size:0.72rem;color:#3a5070;text-align:center;">'
    'Hue Process · Sartorial Jurisprudence · Weather via Open-Meteo · Geocoding via Nominatim</div>',
    unsafe_allow_html=True
)