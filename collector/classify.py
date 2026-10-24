"""Classification and spec extraction for DAC (digital-to-analog converter) papers.

Pure functions (no network, no files) so they can be unit-tested and re-run over the
cached records whenever the rules change. Abstracts are inputs only; they are never
written to the output.
"""
import re

I = re.IGNORECASE

# ---------------------------------------------------------------- relevance
DAC_PAT = re.compile(r"\bDACs?\b|digital[- ]to[- ]analog|\bD/A\b|\bRF[- ]?DACs?\b|digital[- ]to[- ]RF|direct[- ]digital[- ]RF", I)
# an ADC (or a modulator/quantizer) whose internal or feedback DAC is in the title is an ADC paper
ADC_HOST = re.compile(r"\bADCs?\b|analog[- ]to[- ]digital|\bA/D\b|(?:ΔΣ|Σ\s?Δ|delta[- –]sigma|sigma[- –]delta|noise[- ]shaping|\bDSM|\bSDM)\s*modulators?|"
                      r"\b(?:CT|DT)?[- ]?(?:DSMs?|SDMs?)\b|\bSAR\b(?![- ]?DAC)|successive[- ]approximation|\bCIM\b|in[- ]memory|"
                      r"\bPLLs?\b|frequency synthesi[sz]er(?! with)|regulator|\bLDO\b|DC[-–]DC|sensor", I)
# a transmitter / link / SoC built around a DAC: the numbers are the system's
HOST = re.compile(r"\b(?:transmitters?|\bTX\b|transceivers?|front[- ]ends?|SoCs?|radios?|radars?|links?|systems?|"
                  r"direct[- ]digital (?:frequency )?synthesi[sz]ers?|DDFS|DDS|waveform (?:generators?|synthesi[sz]ers?)|AWG|"
                  r"drivers?|power amplifiers?|\bPAs?\b|wireline)\b", I)
NON_PAPER = re.compile(
    r"^(front cover|back cover|table of contents|contents|author index|index|"
    r"call for papers|editorial|guest editorial|reviewers|session \d+ overview|"
    r"(?:tutorials?|short course|evening (?:event|session)|forum|panel)(?=\s*:|\s*$)|"
    r"(ieee )?(transactions|journal) .*information|blank page|copyright)\b", I)


def relevance(title, abstract):
    """Return 'core', 'related' or None."""
    t = title or ""
    m = DAC_PAT.search(t)
    if m and re.search(r"direct[- ]digital (?:frequency )?synthes|\bDDFS\b|\bDDS\b", t, I):
        return "related"                       # a DDFS built around its DAC: the numbers are the synthesizer's
    if m:
        if ADC_HOST.search(t) and not re.search(r"(?:ΔΣ|delta[- ]sigma|sigma[- ]delta|oversampling|noise[- ]shap\w*)\s+(?:DAC|D/A)", t, I):
            return None
        h = HOST.search(t)
        if h and h.start() < m.start() or re.search(r"DAC[- ]based\s+(?:\w+\s+){0,2}(?:transmitter|TX|driver|PA|synthesi)", t, I):
            return "related"
        return "core"
    if re.search(r"\b(?:RF[- ]?)?DAC\b|digital[- ]to[- ]analog converter", abstract or "") and HOST.search(t) and not ADC_HOST.search(t):
        return "related"
    return None


# ------------------------------------------------------------- type / architecture / application
def dac_type(title, abstract):
    text = (title or "") + " " + (abstract or "")
    if re.search(r"[ΔΣ]\s?[-–—]?\s?[ΔΣ]|delta[- –]sigma|sigma[- –]delta|oversampl|noise[- ]shap|\bPWM\b", text, I):
        return "Oversampling"
    return "Nyquist"


ARCH_RULES = [
    ("Current-steering", r"current[- ]steering|\bCS[- ]?DAC|current[- ]mode|current[- ]source"),
    ("RF-DAC",           r"\bRF[- ]?DAC|digital[- ]to[- ]RF|direct[- ]digital[- ]RF|RF power DAC|mixing DAC|\bmixing\b"),
    ("Time-interleaved", r"time[- ]interleav|\binterleaved\b|\bTI[- ]?DAC"),
    ("R-2R/resistor",    r"\bR[- ]?2R|resistor[- ]string|resistive|resistor"),
    ("Capacitive",       r"capacit|charge[- ](?:redistribution|sharing|domain)|switched[- ]capacitor"),
    ("ΔΣ/noise-shaping", r"[ΔΣ]\s?[-–—]?\s?[ΔΣ]|delta[- –]sigma|sigma[- –]delta|noise[- ]shap|oversampl|\bPWM\b|mismatch[- ]shap"),
    ("Segmented",        r"segment|unary|thermometer"),
    ("Return-to-zero",   r"return[- ]to[- ]zero|\bRZ\b|quad[- ]switch|\bRF mode\b"),
    ("DEM/calibration",  r"calibrat|dynamic element matching|\bDEM\b|scrambl|randomi[sz]|data[- ]weighted|rotation|trimming|predistortion"),
    ("Voltage-mode/SST", r"voltage[- ]mode|\bSST\b|source[- ]series"),
]
ARCH_RX = [(n, re.compile(p, I)) for n, p in ARCH_RULES]


def architectures(title, abstract):
    def scan(text):
        return [n for n, rx in ARCH_RX if rx.search(text or "")]
    tags = scan(title)
    if abstract:
        first = " ".join(re.split(r"(?<=[.!?])\s+", abstract)[:2])
        for t in scan(first):
            if t not in tags:
                tags.append(t)
    return tags


APP_RULES = [
    ("Wireless/RF",       r"\b[56]G\b|wireless|cellular|\bLTE\b|\bRF\b|direct[- ]digital|base[- ]station|transmitter|satellite|cable|DOCSIS|multi[- ]band|mm-?wave"),
    ("Wireline/optical",  r"wireline|optical|\bPAM[- ]?\d|Gb/s|coherent|serdes|data[- ]center|ethernet"),
    ("Audio",             r"audio|headphone|class[- ]D|\bdBA\b|hi-?fi|speaker"),
    ("Precision/instrumentation", r"precision|instrumentation|\b(?:1[6-9]|2\d)[- ]?b(?:it)?\b|static linearity|INL|calibrator|metrology"),
    ("Quantum/cryo",      r"quantum|qubit|cryo"),
    ("Display/bias",      r"display|LCD|OLED|bias(?:ing)? (?:generation|of)|reference"),
]
APP_RX = [(n, re.compile(p, I)) for n, p in APP_RULES]
CAL_RX = re.compile(r"calibrat|trimming|\bLMS\b|predistortion|correction", I)


def applications(title, abstract):
    text = (title or "") + " " + (abstract or "")
    return [n for n, rx in APP_RX if rx.search(text)]


def has_calibration(title, abstract):
    return bool(CAL_RX.search((title or "") + " " + (abstract or "")))


# ------------------------------------------------------------- spec parsing
NUM = r"(\d+(?:\.\d+)?)"
_SI = {"a": 1e-18, "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "μ": 1e-6,
       "m": 1e-3, "": 1.0, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}
RES_RX = re.compile(r"(?<![\w.])(\d{1,2})[- ]?(?:b(?:it)?s?)\b(?![- ]?/)", I)
FS_RX = re.compile(r"(?<![\w.])" + NUM + r"\s*-?\s*([kMG])\s?S/s", I)
SFDR_RX = [re.compile(r"SFDR[^.;\d−–-]{0,40}?(?:of\s+|is\s+|=\s*|>\s*|above\s+|over\s+)?" + NUM + r"\s*-?\s*dB", I),
           re.compile(NUM + r"\s*-?\s*dB[c]?[- ]+SFDR", I),
           # "SFDR is 70 dBc at 100 MHz and 55 dBc at 1 GHz": the later values make the field ambiguous
           re.compile(r"SFDR[^.;]{0,80}?\b(?:and|to|while|but)\s+(?:\w+\s+){0,3}?" + NUM + r"\s*-?\s*dBc", I)]
IMD_RX = [re.compile(r"(?:IM3|IMD3?|third[- ]order intermod\w*)[^.;\d−–-]{0,40}?([−–-]?\s?\d+(?:\.\d+)?)\s*-?\s*dBc", I),
          re.compile(r"([−–-]?\s?\d+(?:\.\d+)?)\s*-?\s*dBc[- ]+(?:IM3|IMD3?)", I)]
NSD_RX = [re.compile(r"(?:NSD|noise spectral density)[^.;\d−–-]{0,40}?([−–-]\s?\d{2,3}(?:\.\d+)?)\s*-?\s*dB(?:m|c|FS)/Hz", I),
          re.compile(r"([−–-]\s?\d{2,3}(?:\.\d+)?)\s*-?\s*dB(?:m|c|FS)/Hz[- ]+(?:small[- ]signal[- ])?NSD", I)]
ACLR_RX = [re.compile(r"ACLR[^.;\d−–-]{0,40}?([−–-]?\s?\d+(?:\.\d+)?)\s*-?\s*dB", I),
           re.compile(r"([−–-]?\s?\d+(?:\.\d+)?)\s*-?\s*dBc?[- ]+ACLR", I)]
SNDR_RX = [re.compile(r"\b(?:SNDR|SINAD|THD\s*\+\s*N|DR|dynamic range|SNR)\b[^.;\d−–-]{0,30}?(?:of\s+|is\s+|=\s*)?" + NUM + r"\s*-?\s*dB(?!m|c)", I),
           re.compile(NUM + r"\s*-?\s*dB[A]?[- ]+(?:SNDR|SINAD|DR|dynamic range|SNR)\b", I)]
NODE_NM_RX = re.compile(r"(?<![\w.])(\d{1,3})\s*-?\s*nm\b", I)
NODE_UM_RX = re.compile(r"(?<![\w.])(0\.\d{1,3})\s*-?\s*[µμu]m\b|(?<![\w.])([1-3](?:\.\d)?)\s*-?\s*[µμu]m\s+(?:\w+\s+){0,2}"
                        r"(?:CMOS|BiCMOS|process|technology|SOI|bipolar|InP|SiGe|GaAs)", I)
POWER_VAL = NUM + r"\s*-?\s*([nuµμm]?)W\b(?!\s*/)"
POWER_CTX_RX = re.compile(r"(?:consum\w*|dissipat\w*|power(?:\s+consumption)?|draw(?:s|ing)|drains?|burns?)[^.;]{0,40}?" + POWER_VAL, I)
POWER_AFTER_RX = re.compile(POWER_VAL + r"\s*(?:of\s+)?(?:total\s+|overall\s+)?(?:power|consumption|dissipation)", I)
POWER_TITLE_RX = re.compile(POWER_VAL)
AREA_RX = re.compile(NUM + r"\s*-?\s*mm\s*(?:2|²|\^2)", I)
_FIXES = [(re.compile(r"(\d)\.\s(\d)"), r"\1.\2"), (re.compile(r"(\d)\s*-?\s*mu(m|W|A|V|s)\b"), r"\1 µ\2"),
          (re.compile(r"([µμ])\s+m\b"), r"\1m"), (re.compile(r"\\?hbox\s*"), "")]


def _norm(text):
    for rx, rep in _FIXES:
        text = rx.sub(rep, text)
    return text


def _neg(s):
    return -abs(float(re.sub(r"[−–\s-]", "", s)))


def _vals(rxs, text, conv, lo, hi):
    """Every plausible value (rounded to 3 significant digits for comparison)."""
    out = {}
    for rx in rxs:
        for m in rx.finditer(text or ""):
            try:
                v = conv(m)
            except (ValueError, KeyError):
                continue
            if v is not None and lo <= v <= hi:
                out.setdefault(float("%.3g" % v), v)
    return set(out.values())


def _pick(t, a, cands, best=max):
    """The title's value if it states one, else the abstract's only value; nothing when the abstract lists several."""
    vt, va = cands(t), cands(a)
    if vt:
        return best(vt)
    if len(va) == 1:
        return va.pop()
    return None


def parse_specs(title, abstract):
    t, a = _norm(title or ""), _norm(abstract or "")
    out = {}

    def put(k, v):
        if v is not None:
            out[k] = v
    put("res", _pick(t, a, lambda x: _vals([RES_RX], x, lambda m: int(m.group(1)), 3, 24)))
    put("fs", _pick(t, a, lambda x: _vals([FS_RX], x, lambda m: float(m.group(1)) * _SI[m.group(2)], 1e2, 5e11)))
    put("sfdr", _pick(t, a, lambda x: _vals(SFDR_RX, x, lambda m: float(m.group(1)), 20, 140), best=min))
    put("imd", _pick(t, a, lambda x: _vals(IMD_RX, x, lambda m: _neg(m.group(1)), -140, -20), best=max))
    put("nsd", _pick(t, a, lambda x: _vals(NSD_RX, x, lambda m: _neg(m.group(1)), -200, -100), best=max))
    put("aclr", _pick(t, a, lambda x: _vals(ACLR_RX, x, lambda m: abs(_neg(m.group(1))), 20, 100), best=min))
    put("sndr", _pick(t, a, lambda x: _vals(SNDR_RX, x, lambda m: float(m.group(1)), 20, 140)))
    put("node", _pick(t, a, lambda x: _vals([NODE_NM_RX], x, lambda m: int(m.group(1)), 2, 500)
                      or _vals([NODE_UM_RX], x, lambda m: int(round(float(m.group(1) or m.group(2)) * 1000)), 10, 5000)))
    put("p", _pick(t, a, lambda x: _vals([POWER_TITLE_RX] if x is t else [POWER_CTX_RX, POWER_AFTER_RX], x,
                                         lambda m: float(m.group(1)) * _SI[m.group(2) or ""], 1e-9, 1e3)))
    put("area", _pick(t, a, lambda x: _vals([AREA_RX], x, lambda m: float(m.group(1)), 1e-4, 1e3)))
    return out


def spec_sources(title, abstract):
    """parse_specs() plus where each value came from: {"key": "t" | "a"}."""
    full = parse_specs(title, abstract)
    only_title = parse_specs(title, "")
    return full, {k: ("t" if only_title.get(k) == v else "a") for k, v in full.items()}


def derived(specs):
    """Energy per sample P/fs (J) when the paper gives both."""
    if specs.get("p") and specs.get("fs"):
        return {"e": specs["p"] / specs["fs"]}
    return {}
# ------------------------------------------------------------- affiliations and dates (same rules as adc-census)
ORG_HINT = re.compile(r"universit|institut|college|school|KAIST|POSTECH|UNIST|DGIST|GIST|\bETH\b|EPFL|\bMIT\b|"
                      r"laborator|\blabs?\b|inc\b|ltd|corp|company|co\.|electronics|semiconductor|technolog|"
                      r"research|centre|center|academy|imec|tsmc|samsung|sk hynix|intel|mediatek|qualcomm|"
                      r"apple|google|huawei|broadcom|analog devices|texas instruments|nvidia|\bamd\b|\bibm\b|microsoft", I)


def org_and_country(aff):
    if not aff:
        return None, None
    parts = [p.strip() for p in aff.split(",") if p.strip()]
    if not parts:
        return None, None
    country = re.sub(r"\s+\d[\d\- ]*$", "", parts[-1])
    if re.fullmatch(r"(korea|south korea|republic of korea|korea \(south\))", country, I):
        country = "South Korea"
    elif re.fullmatch(r"(usa|u\.s\.a\.|united states|united states of america|us)", country, I):
        country = "USA"
    elif re.fullmatch(r"(prc|p\.r\. china|people's republic of china)", country, I):
        country = "China"
    org = None
    for p in parts:
        if ORG_HINT.search(p) and not re.match(r"(department|dept|school of|faculty|division)\b", p, I):
            org = p
            break
    if org is None:
        org = parts[1] if len(parts) > 2 else parts[0]
    if len(country) > 30 or re.search(r"\d", country):
        country = None
    return org, country


MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def parse_month(pubdate, year):
    s = (pubdate or "").lower()
    m = re.match(r"((?:19|20)\d{2})-(\d{2})", s)     # ISO dates from Crossref/OpenAlex
    if m:
        return "%s-%s" % m.groups()
    years = re.findall(r"(?:19|20)\d{2}", s)
    y = years[-1] if years else (str(year) if year else None)
    mon = None
    for tok in re.findall(r"[a-z]{3,}", s):
        if tok[:3] in MONTHS:
            mon = MONTHS[tok[:3]]
            break
    if y and mon:
        return "%s-%02d" % (y, mon)
    return y or ""
