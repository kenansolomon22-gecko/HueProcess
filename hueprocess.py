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
        "wool": "Wool's natural resilience keeps you looking sharp across extended proceedings.",
        "pantsuit": "A well-cut pantsuit conveys authority equal to any suit in the room.",
        "skirt suit": "A skirt suit at mid-knee length reads professional and approachable simultaneously.",
        "sheath": "A structured sheath under a blazer projects precision and preparation.",
        "blazer": "A blazer anchors any outfit — the single most powerful upgrade available.",
    },
    "tie": {
        "silk": "Silk ties catch light subtly — signaling investment without distraction.",
        "repp": "Repp stripe ties communicate institutional affiliation and reliability.",
        "solid": "Solid ties minimize visual distraction, keeping the focus on your argument.",
        "muted": "Muted patterns acknowledge formality without claiming more than the moment requires.",
        "no tie": "Removing the tie shifts register from formal advocate to trusted counselor.",
        "conservative": "A conservative tie signals respect for the proceeding without drawing attention.",
    },
    "shoes": {
        "oxford": "Cap-toe oxfords are the universal signal of professional preparation.",
        "derby": "Derbies allow slightly more expressive silhouette while maintaining formality.",
        "monk": "Double monks project confident individualism — acceptable above deposition level.",
        "loafer": "Penny loafers signal relaxed authority appropriate for office and mediation contexts.",
        "pump": "A classic pump at 2-3 inches projects professional height and proportion.",
        "block heel": "Block heels provide stability across long hearing days without sacrificing authority.",
        "flat": "Pointed flats convey precision and professionalism without heel fatigue.",
        "kitten": "Kitten heels thread the needle between formal and accessible in client settings.",
        "polished": "Polished shoes signal attention to detail — judges and jurors notice.",
        "lace-up": "Lace-up shoes in dark leather are the civilian standard for court appearances.",
    },
    "pocket_square": {
        "white": "A white square in TV fold is the courtroom standard — nothing more is needed.",
        "silk": "Silk pocket squares signal deliberate attention to professional presentation.",
        "linen": "Linen squares project understated quality — a mark of the prepared professional.",
    }
}

def get_reasoning(field, value):
    if not value or value.lower() in ("none", "n/a", ""):
        return ""
    val_lower = value.lower()
    for key, reason in REASONING.get(field, {}).items():
        if key in val_lower:
            return reason
    return ""

# ══════════════════════════════════════════════════════════════════════════════
# WARDROBE DATABASE
# To edit recommendations: find the case type section and update the add() lines.
# Format: add("Case Type", "Role", "Gender", rank, "suit", "tie", "shoes", "socks", "accessories", "pocket_square", "note")
# ══════════════════════════════════════════════════════════════════════════════

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
    add("Jury Trial","Client","Male",1,"Dark navy or charcoal wool suit — off the rack is fine, pressed and fitted","Conservative solid or repp stripe tie in navy, burgundy or grey","Black or dark brown leather lace-up shoes, polished","Dark socks matching trouser color","None","None","Wool holds its shape across a full trial day. Jury members form impressions in the first 90 seconds — dark, fitted, and pressed is the non-negotiable baseline.")
    add("Jury Trial","Client","Male",2,"Dark charcoal or navy suit — avoid shiny or stretchy blends","Solid tie in a subdued color — no novelty patterns","Black or dark brown leather dress shoes","Dark matching socks","None","None","Avoid bold patterns anywhere — the jury's focus belongs on your testimony, not your clothes.")
    add("Jury Trial","Client","Male",3,"Charcoal or navy blazer + matching dark trousers — same color to read as a suit","Conservative tie","Polished leather dress shoes in black or dark brown","Dark matching socks","None","None","Matched separates in the same dark shade read nearly as well as a suit from the jury box.")
    add("Jury Trial","Client","Male",4,"Navy blazer + dark navy or charcoal trousers","Tie optional if blazer is sharp and shirt is crisp","Clean dark leather oxfords or loafers","Dark socks","None","None","Navy communicates honesty and stability — consistently rated favorably in mock juror studies.")
    add("Jury Trial","Client","Male",5,"Dark grey or charcoal slacks + dark structured sport coat","No tie needed if sport coat is structured","Dark leather oxfords","Dark socks","None","None","A structured sport coat over dark slacks elevates your appearance without requiring a full suit.")
    add("Jury Trial","Client","Male",6,"Dark neat pressed trousers + white or light blue button-down collar shirt","No tie","Clean dark shoes — no sneakers or athletic footwear","Dark socks","None","None","Absolute minimum: dark, pressed, clean, collared. No jeans, no sneakers. The court is not casual.")
    add("Jury Trial","Client","Female",1,"Dark navy or charcoal skirt suit or pantsuit — wool or wool blend preferred","N/A","Conservative low heel (2 inches max) or pointed flat in black or navy","Sheer nude or navy hosiery","Small stud earrings only in gold, silver or pearl — nothing dangling","None","Jurors assess credibility visually — understated, dark, and well-fitted communicates exactly the right message.")
    add("Jury Trial","Client","Female",2,"Dark blazer in navy or charcoal + matching trousers or knee-length skirt","N/A","Low block heel or pointed flat in black","Sheer hosiery or dark opaque tights","Small stud earrings","None","The blazer is the single most important piece — it signals intentionality and professionalism.")
    add("Jury Trial","Client","Female",3,"Navy or charcoal sheath dress (knee length or below) + structured blazer","N/A","Low heel in black or navy","Sheer nude or navy hosiery","Stud earrings only — no statement pieces","None","A blazer over a sheath dress is one of the most universally readable professional looks. Keep the dress solid and neckline conservative.")
    add("Jury Trial","Client","Female",4,"Dark pressed trousers + neat fitted blouse in white or pale blue + blazer if available","N/A","Modest flat or low heel in black or dark neutral","Sheer hosiery or dark trouser socks","Simple small earrings","None","The blazer is the single most elevating item — even over modest trousers it shifts the register to professional.")
    add("Jury Trial","Client","Female",5,"Dark knee-length skirt in wool or ponte fabric + fitted blouse","N/A","Modest flat shoes in dark neutral","Sheer hosiery recommended","Simple small earrings","None","Keep the skirt at or below the knee — modest length communicates respect for the proceeding.")
    add("Jury Trial","Client","Female",6,"Dark neat trousers or skirt + button-up blouse in white, cream or pale blue","N/A","Flat shoes in dark neutral, clean and unscuffed","Dark hosiery or trouser socks","None","None","Irreducible minimum: dark, pressed, modest, and clean. No jeans, no athleisure, no revealing necklines.")

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
    add("Bench Trial","Client","Male",1,"Dark wool suit in navy or charcoal — pressed and fitted","Conservative tie in navy, grey or burgundy","Polished black or dark brown leather lace-ups","Dark matching OTC socks","None","None","Judges read attire as a direct proxy for respect. A pressed wool suit communicates that you understand the gravity of the proceeding.")
    add("Bench Trial","Client","Male",2,"Navy blazer + dark charcoal or navy trousers in wool or ponte fabric","Solid conservative tie","Dark leather dress shoes, polished","Dark matching socks","None","None","Before a judge, blazer-and-trouser in dark structured fabric reads as serious business attire.")
    add("Bench Trial","Client","Male",3,"Dark matched separates — blazer and trousers in the same dark shade","Tie optional — if worn, keep it solid and subdued","Dark leather shoes","Dark socks","None","None","Pressed and dark is the floor-level requirement before any judge.")
    add("Bench Trial","Client","Male",4,"Dark charcoal or navy trousers + crisp white or light blue button-down","No tie","Dark leather shoes","Dark socks","None","None","A crisp collared shirt in white or pale blue with dark pressed trousers reads as business casual — acceptable as a minimum.")
    add("Bench Trial","Client","Male",5,"Dark slacks + polo shirt in a solid dark color — no logos or graphics","No tie","Clean dark leather shoes","Matching dark socks","None","None","A polo in a solid dark color is the marginal minimum — only if clean and untucked is not acceptable.")
    add("Bench Trial","Client","Male",6,"Clean dark pressed trousers + any collared shirt — no t-shirts","No tie","Clean closed-toe footwear — no sandals","Any dark socks","None","None","Bare minimum: collared, clean, dark, pressed. No jeans, no sneakers. The judge will notice.")
    add("Bench Trial","Client","Female",1,"Dark wool or ponte suit or pantsuit — navy or charcoal","N/A","Low heel in black or navy — 2 inches max","Sheer hosiery","Small studs only in gold, silver or pearl","None","A dark, fitted suit communicates professionalism and respect — which itself supports your credibility.")
    add("Bench Trial","Client","Female",2,"Dark blazer in navy or charcoal + matching trousers or knee skirt","N/A","Flat or low block heel in black","Sheer hosiery or opaque tights","Small stud earrings","None","A blazer is the single item that most elevates any civilian court appearance.")
    add("Bench Trial","Client","Female",3,"Dark sheath dress at or below the knee + structured blazer","N/A","Modest heel or flat in dark neutral","Sheer hosiery","None","None","Keep accessories minimal — nothing that moves, catches light, or makes sound.")
    add("Bench Trial","Client","Female",4,"Dark pressed trousers + neat fitted blouse in white or neutral tone","N/A","Flat shoes in dark neutral","Sheer hosiery or trouser socks","None","None","A blouse in white or cream over dark trousers reads cleanly and respectfully.")
    add("Bench Trial","Client","Female",5,"Dark knee-length or longer skirt + neat fitted top in a solid neutral","N/A","Flat shoes, clean and unscuffed","Sheer hosiery recommended","None","None","Knee-length or below; avoid anything sheer, fitted, or patterned.")
    add("Bench Trial","Client","Female",6,"Any dark pressed outfit that covers the knees and shoulders","N/A","Clean closed-toe footwear","Any dark hosiery","None","None","Pressed, modest, dark, and clean is the irreducible minimum before any judge.")

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
    add("Deposition","Client","Male",1,"Dark wool suit in navy or charcoal — pressed and well-fitted","Conservative solid or stripe tie in navy, grey or burgundy","Polished black or dark brown lace-up leather shoes","Dark OTC socks matching trouser color","None","None","You are on the record — the transcript may include video. Dress as you would for court: dark, fitted, and professional. Opposing counsel will note your appearance.")
    add("Deposition","Client","Male",2,"Navy blazer + dark matching trousers in wool or ponte","Solid conservative tie","Dark leather dress shoes, polished","Dark matching socks","None","None","Business professional is the correct register. Depositions feel informal but carry the weight of sworn testimony — dress to signal you understand that.")
    add("Deposition","Client","Male",3,"Dark matched separates — blazer and trousers in coordinating dark shades","Tie optional","Dark leather shoes","Dark socks","None","None","Avoid anything casual — opposing counsel observes everything. Matched dark separates read professionally when a full suit is unavailable.")
    add("Deposition","Client","Male",4,"Dark pressed trousers + crisp button-down in white or pale blue","No tie","Dark leather shoes","Dark socks","None","None","A crisp collared shirt over dark pressed trousers reads as business casual. Keep it tucked, pressed, and in a solid or subtle stripe.")
    add("Deposition","Client","Male",5,"Business casual separates — dark chinos or trousers + collared shirt","No tie","Clean leather shoes","Matching socks","None","None","Business casual is the minimum register — avoid jeans, athletic wear, or graphic shirts. You may be on video.")
    add("Deposition","Client","Male",6,"Neat collared shirt + dark pressed trousers","No tie","Clean closed-toe shoes","Any dark socks","None","None","You are being recorded. At minimum: clean, pressed, collared, and dark trousers. No denim or athletic footwear.")
    add("Deposition","Client","Female",1,"Dark wool or ponte suit or pantsuit","N/A","Low heel in black or navy","Sheer hosiery","Small stud earrings in gold or pearl","None","You are on record — a structured wool or ponte suit in navy or charcoal communicates professional seriousness on any video recording.")
    add("Deposition","Client","Female",2,"Dark blazer + matching trousers or knee-length skirt","N/A","Low heel or flat in black","Sheer hosiery","Small stud earrings","None","The blazer anchors the look — without it, even neat separates can read as under-dressed for sworn testimony.")
    add("Deposition","Client","Female",3,"Dark sheath dress (knee length) + structured blazer","N/A","Modest heel or flat","Sheer hosiery","Small earrings","None","Keep everything modest and camera-ready. Avoid anything that moves visibly, makes noise, or draws attention away from your words.")
    add("Deposition","Client","Female",4,"Dark pressed trousers + neat fitted blouse in white or neutral","N/A","Flat shoes in dark neutral","Trouser socks or light hosiery","None","None","A white or pale blouse over dark pressed trousers reads cleanly on camera. Avoid casual fabrics, loud patterns, or anything sheer.")
    add("Deposition","Client","Female",5,"Dark knee-length skirt + solid blouse in white or neutral","N/A","Flat shoes, unscuffed","Sheer hosiery","None","None","Below the knee and modest is the reliable floor. Solid, dark, and simple photographs best.")
    add("Deposition","Client","Female",6,"Any neat dark outfit covering knees and shoulders","N/A","Flat closed-toe footwear","Any","None","None","Pressed, dark, modest — the irreducible standard for sworn testimony. You may be on camera.")

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
    add("Mediation","Client","Male",1,"Dark wool suit in navy or charcoal — business professional register","Conservative tie optional but recommended","Polished leather dress shoes","Dark matching socks","None","None","Your visual presentation signals whether you are genuinely serious about reaching resolution. A professional appearance tells the mediator and opposing party that you are engaged and credible.")
    add("Mediation","Client","Male",2,"Navy blazer + dark wool or ponte trousers","Tie optional","Dark leather shoes, clean and polished","Dark matching socks","None","None","A blazer and dark trousers in a structured fabric project investment without the full formality of a suit.")
    add("Mediation","Client","Male",3,"Dark matched separates in navy or charcoal","No tie needed","Dark leather shoes","Dark socks","None","None","Mediation is less formal than court but more formal than a business meeting. Neat matched separates communicate professional engagement.")
    add("Mediation","Client","Male",4,"Dark pressed chinos or trousers + collared shirt in white or pale blue","No tie","Clean leather shoes","Matching dark socks","None","None","Business casual is the minimum register. Avoid anything too casual — the mediator and opposing party form impressions that affect the outcome.")
    add("Mediation","Client","Male",5,"Smart chinos in dark navy or charcoal + neat polo or button-down","No tie","Clean leather shoes","Matching socks","None","None","A polo in a solid dark color is acceptable only if perfectly pressed. Mediation tolerates smart casual for lower-stakes matters.")
    add("Mediation","Client","Male",6,"Clean collared shirt in solid color + dark pressed trousers","No tie","Clean closed-toe footwear","Any dark socks","None","None","At minimum: collared, pressed, and presentable. Your appearance affects how seriously your position is taken.")
    add("Mediation","Client","Female",1,"Dark professional suit or pantsuit in wool or ponte fabric","N/A","Low heel or flat in dark neutral","Sheer hosiery","Small stud jewelry","None","A structured suit in navy or charcoal communicates credibility to both the mediator and opposing counsel.")
    add("Mediation","Client","Female",2,"Dark blazer + matching trousers or knee-length skirt","N/A","Low heel or flat","Sheer hosiery or opaque tights","Small earrings","None","A blazer over coordinating separates reads as business professional without the full formality of a suit.")
    add("Mediation","Client","Female",3,"Dark sheath dress + structured blazer","N/A","Modest heel or flat","Sheer hosiery","Small earrings","None","A sheath under a blazer is versatile and consistently reads as prepared and credible.")
    add("Mediation","Client","Female",4,"Dark pressed trousers + neat blouse in white or neutral tone","N/A","Flat shoes in dark neutral","Any hosiery","Small earrings","None","Business casual is acceptable — stay neat, modest, and in dark or neutral tones. Avoid casual fabrics like jersey, denim, or athletic materials.")
    add("Mediation","Client","Female",5,"Smart casual separates in dark or neutral tones","N/A","Flat or low heel","Any","Simple jewelry","None","Smart casual is sufficient for lower-stakes mediations — but always err toward more formal when the stakes are high.")
    add("Mediation","Client","Female",6,"Any neat pressed outfit in dark or neutral tones","N/A","Comfortable closed-toe shoes","Any","None","None","Pressed and modest is the floor for any professional proceeding. Even at the most casual register, avoid jeans or athletic wear.")

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
    add("Office Day","Client","Male",1,"Business professional suit or blazer and trousers — match the firm's culture","Tie optional depending on firm formality","Polished leather shoes","Dark matching socks","None","None","Dress for the firm's culture. A top-tier litigation firm expects business professional even on ordinary days.")
    add("Office Day","Client","Male",2,"Smart business casual — dark chinos or trousers + collared shirt + optional blazer","No tie needed","Clean leather shoes","Matching socks","None","None","Business casual is the standard for most modern law firm office visits. A blazer over a collared shirt reads as polished and prepared.")
    add("Office Day","Client","Male",3,"Dark chinos + neat collared shirt + blazer or sport coat","No tie","Clean leather or dress shoes","Matching socks","None","None","Smart casual reads professional in most office environments. The blazer signals intentionality.")
    add("Office Day","Client","Male",4,"Dark chinos or pressed jeans + neat polo or button-down","No tie","Clean leather shoes","Matching socks","None","None","Polo and chinos is smart casual floor — keep everything pressed and in solid or subtle tones.")
    add("Office Day","Client","Male",5,"Dark jeans (no distressing) + neat collared shirt in solid color","No tie","Clean leather or casual shoes","Matching socks","None","None","Dark undistressed jeans are acceptable in casual firms if the shirt is crisp. Avoid graphic tees or athletic footwear.")
    add("Office Day","Client","Male",6,"Clean casual wear in neutral or dark tones — collared preferred","No tie","Clean closed-toe footwear","Any","None","None","Casual office environments have wide latitude — avoid only very sloppy, stained, or revealing clothing.")
    add("Office Day","Client","Female",1,"Business professional — suit, pantsuit, or polished separates matching firm culture","N/A","Low heel or pointed flat","Hosiery or trouser socks","Simple professional jewelry","None","Match the firm's dress culture — when uncertain, go more formal. A well-fitted blazer over coordinating pieces is consistently appropriate.")
    add("Office Day","Client","Female",2,"Business casual — blazer or structured cardigan + neat trousers or skirt","N/A","Low heel or flat","Any","Simple earrings or a watch","None","A structured top over dark pressed trousers or a knee-length skirt reads as professional and prepared.")
    add("Office Day","Client","Female",3,"Smart blouse or top + tailored trousers or a-line skirt in dark or neutral tone","N/A","Flat or low block heel","Any","Simple earrings","None","Smart casual covers most modern professional office environments — as long as fabrics are structured and colors are neutral or dark.")
    add("Office Day","Client","Female",4,"Neat casual separates in dark or neutral tones — avoid logos or graphics","N/A","Flat shoes in dark or neutral","Any","Simple jewelry","None","Neat and put-together is the minimum for any professional office.")
    add("Office Day","Client","Female",5,"Dark jeans (no distressing) + neat blouse or fitted top","N/A","Clean shoes in neutral tone","Any","Simple jewelry","None","Dark jeans plus a neat top are acceptable in casual law firm environments — keep colors simple and avoid anything very fitted or revealing.")
    add("Office Day","Client","Female",6,"Any neat casual outfit in neutral or dark tones","N/A","Clean closed-toe footwear","Any","None","None","Avoid only very casual, revealing, or sloppy clothing in any professional space.")

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
    add("Client Meeting","Client","Male",1,"Business professional suit in navy or charcoal — wool or wool blend preferred","Conservative tie in navy, grey or burgundy","Polished leather dress shoes","Dark matching socks","None","None","When meeting legal counsel for the first time or a high-stakes update, business professional communicates that you understand the seriousness of your matter.")
    add("Client Meeting","Client","Male",2,"Navy blazer + dark trousers in wool or ponte — coordinated and pressed","Tie optional","Clean polished leather shoes","Dark matching socks","None","None","A structured fabric in a dark shade signals investment without requiring a full suit.")
    add("Client Meeting","Client","Male",3,"Smart business casual — dark chinos or trousers + neat collared shirt + blazer","No tie","Clean leather shoes","Matching socks","None","None","Business casual is appropriate for most client meeting contexts. The blazer is the key item — it lifts any outfit into professional territory.")
    add("Client Meeting","Client","Male",4,"Dark pressed chinos + neat button-down in white or pale blue","No tie","Clean leather shoes","Matching socks","None","None","Smart casual reads appropriately for informal or long-standing relationship visits. Keep everything pressed and avoid casual fabrics or loud patterns.")
    add("Client Meeting","Client","Male",5,"Smart casual separates — dark trousers or chinos + polo or collared shirt","No tie","Clean shoes","Matching socks","None","None","Most modern law firms accommodate smart casual for established client relationships.")
    add("Client Meeting","Client","Male",6,"Neat collared casual outfit in dark or neutral tones","No tie","Clean closed-toe footwear","Any","None","None","At minimum: collared, clean, and presentable. Your appearance reflects on both you and your matter.")
    add("Client Meeting","Client","Female",1,"Business professional — dark suit, pantsuit, or polished skirt suit in wool or ponte","N/A","Low heel in black or navy","Sheer hosiery","Modest jewelry — small studs or a simple chain","None","Your attorney represents you; your appearance supports that narrative. Business professional dress communicates credibility and investment in your own case.")
    add("Client Meeting","Client","Female",2,"Business casual — blazer or structured jacket + neat separates","N/A","Low heel or pointed flat","Hosiery or trouser socks","Simple earrings or a watch","None","A blazer over coordinating separates elevates any law firm visit. In dark or neutral tones, it reads as professional and prepared.")
    add("Client Meeting","Client","Female",3,"Smart separates — neat blouse or top + tailored trousers or a-line skirt","N/A","Flat or low block heel","Any","Simple earrings","None","Smart and neat covers most client meeting scenarios. Keep fabrics structured and colors neutral or dark.")
    add("Client Meeting","Client","Female",4,"Neat blouse + pressed dark trousers or knee-length skirt","N/A","Flat shoes in dark neutral","Any","Simple jewelry","None","Business casual is widely accepted for ongoing relationship meetings. Keep it neat, modest, and in solid or subtle tones.")
    add("Client Meeting","Client","Female",5,"Smart casual separates in dark or neutral tones","N/A","Flat or low heel","Any","Any modest jewelry","None","Smart casual is appropriate for most ongoing or informal relationship meetings.")
    add("Client Meeting","Client","Female",6,"Any neat pressed outfit in neutral or dark tones","N/A","Clean closed-toe footwear","Any","None","None","Neat and put-together is always sufficient for any law office visit.")

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
    add("Settlement Conference","Client","Male",1,"Business professional suit in navy or charcoal wool","Conservative tie","Polished leather dress shoes","Dark matching socks","None","None","How you dress signals how seriously you take settlement. A professional appearance tells the opposing party that you are credible, prepared, and invested in resolution — which strengthens your negotiating position.")
    add("Settlement Conference","Client","Male",2,"Navy blazer + dark wool or ponte trousers","Tie optional","Polished leather shoes","Dark matching socks","None","None","A blazer over dark trousers in a structured fabric reads as business professional and signals good-faith engagement.")
    add("Settlement Conference","Client","Male",3,"Smart business casual — dark chinos or trousers + collared shirt + optional blazer","No tie","Clean leather shoes","Dark socks","None","None","Business casual is appropriate for most settlement contexts — but the more important the settlement, the more formal you should dress.")
    add("Settlement Conference","Client","Male",4,"Dark pressed chinos + neat button-down shirt","No tie","Clean leather shoes","Matching socks","None","None","Avoid looking like you don't care. The opposing party's perception of your seriousness affects the settlement dynamic.")
    add("Settlement Conference","Client","Male",5,"Smart casual separates — dark trousers or chinos + polo or collared shirt","No tie","Clean leather shoes","Matching socks","None","None","Smart casual is the minimum register. The stakes of a settlement warrant more effort than everyday casual dress.")
    add("Settlement Conference","Client","Male",6,"Neat collared outfit in dark or neutral tones","No tie","Clean closed-toe footwear","Any","None","None","At minimum: clean, pressed, and respectful. Your appearance at the settlement table is part of your presentation.")
    add("Settlement Conference","Client","Female",1,"Dark professional suit or pantsuit in wool or ponte — navy or charcoal","N/A","Low heel in dark neutral","Sheer hosiery","Small stud jewelry","None","A structured suit communicates credibility and investment — qualities that matter when opposing counsel sizes up your resolve.")
    add("Settlement Conference","Client","Female",2,"Dark blazer + matching separates in structured fabric","N/A","Low heel or pointed flat","Sheer hosiery","Simple earrings","None","In navy or charcoal, a blazer over coordinating separates reads as business professional without the full formality of a suit.")
    add("Settlement Conference","Client","Female",3,"Smart casual separates in dark or neutral tones + blazer if available","N/A","Flat or low heel","Any","Simple earrings","None","The more financially significant the settlement, the more formal your dress should be.")
    add("Settlement Conference","Client","Female",4,"Neat blouse + dark pressed trousers or knee skirt","N/A","Flat shoes in dark neutral","Any","Simple jewelry","None","Business casual is sufficient — stay neat, modest, and in dark or neutral tones.")
    add("Settlement Conference","Client","Female",5,"Smart casual separates in structured fabrics","N/A","Flat or low heel","Any","Simple jewelry","None","Smart casual is the minimum register for any settlement proceeding with real financial stakes.")
    add("Settlement Conference","Client","Female",6,"Any neat pressed outfit in dark or neutral tones","N/A","Clean closed-toe footwear","Any","None","None","Pressed, modest, and professional — always the correct baseline at a settlement table.")

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
    add("Arbitration","Client","Male",1,"Dark wool suit in navy or charcoal — arbitration is quasi-judicial","Conservative tie in navy, grey or burgundy","Polished leather dress shoes","Dark matching socks","None","None","Arbitration carries the same weight as court. A dark wool suit signals that you understand the seriousness of the proceeding and respect the arbitrator's authority.")
    add("Arbitration","Client","Male",2,"Navy blazer + dark wool or ponte trousers","Conservative tie or no tie","Polished leather shoes","Dark matching socks","None","None","A blazer and dark trousers in structured fabric reads as business professional — appropriate for any arbitration panel.")
    add("Arbitration","Client","Male",3,"Smart business casual — dark chinos or trousers + collared shirt + blazer","No tie","Clean leather shoes","Dark socks","None","None","Business casual with a blazer is appropriate for less formal arbitrations. The blazer is non-negotiable — it marks the register as professional.")
    add("Arbitration","Client","Male",4,"Dark pressed chinos + neat collared shirt in white or pale blue","No tie","Clean leather shoes","Matching socks","None","None","Neat casual is acceptable for informal arbitration proceedings — but keep it pressed, dark, and collared.")
    add("Arbitration","Client","Male",5,"Smart casual separates — dark trousers + collared shirt","No tie","Clean shoes","Matching socks","None","None","Smart casual signals basic professional engagement with the arbitration process.")
    add("Arbitration","Client","Male",6,"Neat collared attire in dark or neutral tones","No tie","Clean closed-toe footwear","Any","None","None","Collared and pressed is the minimum standard — no denim, athletic wear, or graphic shirts.")
    add("Arbitration","Client","Female",1,"Dark professional suit or pantsuit — treat arbitration as you would court","N/A","Low heel in dark neutral","Sheer hosiery","Small stud jewelry","None","A dark structured suit communicates credibility, preparedness, and respect for the panel — all qualities that support your position.")
    add("Arbitration","Client","Female",2,"Dark blazer + matching separates in structured fabric","N/A","Low heel or flat","Sheer hosiery","Simple earrings","None","A blazer over coordinating dark separates reads as business professional — appropriate for any arbitration setting.")
    add("Arbitration","Client","Female",3,"Smart separates in dark or neutral tones + blazer","N/A","Flat or low heel","Any","Simple earrings","None","Neat and professional is appropriate for most arbitration settings. Always include a blazer when possible.")
    add("Arbitration","Client","Female",4,"Neat blouse + dark pressed trousers or skirt","N/A","Flat shoes in dark neutral","Any","Simple jewelry","None","Business casual covers most non-formal arbitration proceedings — stay neat, dark, and modest.")
    add("Arbitration","Client","Female",5,"Smart casual separates in structured fabrics","N/A","Flat or low heel","Any","Simple jewelry","None","Smart casual is the minimum for any arbitration context with real stakes.")
    add("Arbitration","Client","Female",6,"Any neat pressed outfit in dark or neutral tones","N/A","Clean closed-toe footwear","Any","None","None","Pressed and modest is always acceptable — never arrive in denim or athletic wear.")

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
    add("Appellate Argument","Client","Male",1,"Dark formal suit in navy or charcoal wool — most formal outfit you own","Conservative tie in navy, grey or burgundy","Polished leather dress shoes — cap-toe oxford if available","Dark OTC socks","None","None","Appellate courts are the most formal proceedings in the legal system. A dark wool suit is the baseline — no exceptions for business casual.")
    add("Appellate Argument","Client","Male",2,"Dark blazer + formal dark trousers — matched as closely to a suit as possible","Conservative tie","Polished leather dress shoes","Dark matching socks","None","None","Formal business attire is appropriate for appellate participants and observers alike. Matched blazer and trousers in dark shade read as a suit from a distance.")
    add("Appellate Argument","Client","Male",3,"Business professional suit or separates — pressed and well-fitted","Tie optional","Dark leather shoes, polished","Dark socks","None","None","Professional dress is the minimum for appellate proceedings. Even as an observer, the courtroom demands a professional appearance.")
    add("Appellate Argument","Client","Male",4,"Dark smart casual — chinos or trousers + collared shirt + blazer","No tie","Clean leather shoes","Dark socks","None","None","Smart casual with a blazer is the minimum for appellate court attendance. The blazer is essential.")
    add("Appellate Argument","Client","Male",5,"Smart casual separates in dark or neutral tones","No tie","Clean leather shoes","Matching socks","None","None","Smart casual is the minimum for appellate court attendance as an observer.")
    add("Appellate Argument","Client","Male",6,"Neat collared attire in dark tones — no jeans or athletic wear","No tie","Clean leather or dress shoes","Any dark socks","None","None","Collared and pressed in dark tones is the floor for any appellate court appearance.")
    add("Appellate Argument","Client","Female",1,"Business professional formal — dark suit, pantsuit or skirt suit in wool","N/A","Low heel in black or navy — 2 inches max","Sheer hosiery","Minimal jewelry — small studs only","None","Appellate courts are formal. Dress as formally as possible — a dark wool suit or pantsuit is the baseline. This is not the occasion for anything casual.")
    add("Appellate Argument","Client","Female",2,"Dark formal separates — blazer and skirt or trousers in matching dark shade","N/A","Low heel or pointed flat","Sheer hosiery","Small stud earrings","None","Matched separates in dark wool or ponte read as a suit and are appropriate for any appellate proceeding.")
    add("Appellate Argument","Client","Female",3,"Dark blazer + formal trousers or knee-length skirt","N/A","Modest heel or flat in black","Sheer hosiery","Small stud earrings","None","A blazer is essential — it is the single item that most clearly marks an outfit as court-appropriate.")
    add("Appellate Argument","Client","Female",4,"Dark neat separates + blazer","N/A","Flat shoes in dark neutral","Any","Simple earrings","None","Business casual with a blazer is appropriate for appellate observers. Keep everything dark, structured, and conservative.")
    add("Appellate Argument","Client","Female",5,"Smart casual separates in dark or neutral tones","N/A","Flat or low heel","Any","Simple jewelry","None","Smart casual is the minimum for appellate court attendance — always err toward more formal if possible.")
    add("Appellate Argument","Client","Female",6,"Any neat dark outfit covering knees and shoulders","N/A","Clean closed-toe footwear","Any","None","None","Dark, pressed, and modest is always appropriate for any appellate appearance.")

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
    add("Networking Event","Client","Male",1,"Business casual or smart casual — match the event's stated formality","Tie optional — read the room","Clean leather shoes in dark brown or black","Matching socks","None","None","When uncertain, err toward business casual. A blazer over chinos reads well at any legal networking event regardless of formality level.")
    add("Networking Event","Client","Male",2,"Navy or charcoal blazer + dark chinos or smart trousers","No tie","Clean leather shoes","Matching socks","None","None","Blazer plus chinos is the universal smart casual standard for networking. It reads as deliberately dressed without the formality of a suit.")
    add("Networking Event","Client","Male",3,"Smart casual separates — dark chinos or trousers + neat collared shirt","No tie","Clean leather shoes","Matching socks","None","None","Smart casual is widely appropriate for most legal networking events. Keep fabrics structured and colors neutral or dark.")
    add("Networking Event","Client","Male",4,"Dark chinos + neat collared shirt in solid color","No tie","Clean leather or casual shoes","Matching socks","None","None","Neat casual is acceptable for informal networking — keep it pressed and avoid graphics or logos.")
    add("Networking Event","Client","Male",5,"Smart casual outfit in neutral or dark tones","No tie","Clean shoes","Any","None","None","Any smart casual outfit is appropriate for casual networking.")
    add("Networking Event","Client","Male",6,"Neat casual outfit in clean neutral tones","No tie","Clean closed-toe footwear","Any","None","None","Clean and presentable is sufficient for the most informal networking events.")
    add("Networking Event","Client","Female",1,"Business casual or cocktail-adjacent — match the event's formality level","N/A","Modest heel or elegant flat","Any","Any tasteful jewelry","None","Networking events allow more personal expression. A blazer over a dress or neat separates reads well at any legal networking function.")
    add("Networking Event","Client","Female",2,"Smart separates or neat blouse + tailored trousers or skirt","N/A","Low heel or elegant flat","Any","Any modest jewelry","None","One expressive jewelry piece or accessory is welcome at networking — this is where personality earns its place.")
    add("Networking Event","Client","Female",3,"Neat blouse + tailored trousers or a-line skirt in any professional color","N/A","Flat or low heel","Any","Simple or expressive jewelry","None","A bolder color or accessory is perfectly appropriate at networking events.")
    add("Networking Event","Client","Female",4,"Smart casual dress or separates in any professional tone","N/A","Flat or low heel","Any","Any jewelry you like","None","Smart casual is the reliable floor for networking events of any formality level.")
    add("Networking Event","Client","Female",5,"Any smart casual outfit — express your personal style within professional range","N/A","Flat or low heel","Any","Any","None","Networking tolerates the widest range of any legal occasion — avoid only very casual or revealing clothing.")
    add("Networking Event","Client","Female",6,"Any neat casual outfit that feels like you","N/A","Clean footwear","Any","Any","None","Clean and presentable is sufficient for informal networking. This is the one occasion where personal style is genuinely welcome.")

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

def get_coords_from_city(city_name):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(city_name)}&format=json&limit=1"
        r = requests.get(url, headers={"User-Agent": "HueProcess/1.0"}, timeout=5)
        results = r.json()
        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            display = results[0].get("display_name", city_name).split(",")[0]
            return lat, lon, display
        return None, None, None
    except Exception:
        return None, None, None

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
        # Just type your city name — no coordinates needed
        city_input = st.text_input("Enter your city", placeholder="e.g. Nashville, TN")
        if st.button("Get Weather"):
            if city_input.strip():
                with st.spinner("Finding your city..."):
                    lat, lon, display_name = get_coords_from_city(city_input.strip())
                if lat:
                    with st.spinner("Fetching weather..."):
                        weather_data = get_weather(lat, lon)
                        weather_location = display_name
                        st.session_state["weather"] = weather_data
                        st.session_state["weather_loc"] = weather_location
                else:
                    st.error("City not found — try a different spelling or add the state (e.g. Nashville, TN).")
            else:
                st.warning("Please enter a city name.")
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
