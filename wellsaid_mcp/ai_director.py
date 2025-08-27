# wellsaid_mcp/ai_director.py

import re
import xml.etree.ElementTree as ET
from wellsaid_mcp.mcp_server import mcp


@mcp.tool(name="Validate_AI_Director_tags",
          description="Validates the the ai director tags were placed correctly, and did not result if malformed markup")
def validate_ai_director_tags(text: str) -> bool:
    """
    Validates whether all AI Director tags are properly nested and closed.

    Returns True if XML is valid, False otherwise.
    """
    try:
        # Wrap in dummy root since WellSaid tags are partial XML
        ET.fromstring(f"<root>{text}</root>")
        return True
    except ET.ParseError:
        return False


# === Tag Wrappers ===
@mcp.tool(name="Adjust_pitch",
          description="""Adjusts pitch of the given text. The valid values are integers between -250 and +500.
          The default pitch is 0.

          Note that using this features requires the caruso model
          """)
def wrap_with_pitch(text: str, value: int) -> str:
    """
    Wraps text with a <pitch> tag. Value range: -250 to +500.
    """
    return f'<pitch value="{value}">{text}</pitch>'

@mcp.tool(name="Adjust_tempo",
          description="""Adjusts tempo of the given text. The valid values are decimals between 0.5 and 2.5. 
          The default tempo is 1.
          Note that using this features requires the caruso model
          """)
def wrap_with_tempo(text: str, value: float) -> str:
    """
    Wraps text with a <tempo> tag. Value range: 0.5 to 2.5.
    """
    return f'<tempo value="{value}">{text}</tempo>'


@mcp.tool(name="Adjust_loudness",
          description="""Adjusts loudness of the given text. The valid values are integers between -20 and +10.
          The default value is a neutral 0.
          Note that using this features requires the caruso model
          """)
def wrap_with_loudness(text: str, value: int) -> str:
    """
    Wraps text with a <loudness> tag. Value range: -20 to +10.
    """
    return f'<loudness value="{value}">{text}</loudness>'


@mcp.tool(name="Apply_respelling",
          description="""Adjusts the phonetic pronunciation of a word. Used to force a certain pronunciation, or 
          if the TTS engine is not pronouncing it correctly, most commonly with things like proper nouns, 
          medical or industry terminology. Emphasis can be indicated by a phonetic section being in all capital letters.
          Each section is delimited by a hyphen, and do not mix upper and lower case letters in a single phonetic section.

          Phonetic respellings reference
          Respellings Reference Chart

Vowels			
To hear	as in	type	For example,
a	ant	    A	 ::ANT::
a	spa	    AH	 ::SPAH::
a	all	    AW	 ::AWL::
a	eight	AY	::AYT::
e	egg	    EH	::EHG::
e	ease	EE	::EEZ::
i	in	    IH	::IHN::
i	isle	Y	::YL::
o	oat	    OH	::OHT::
o	ooh	    OO	::OO::
o	foot	UU	::FUUT::
u	up	    UH	::UHP::
			
			
VOWEL COMBINATIONS			
To hear	as in	type	For example,
ar	car	    AR	::KAR::
er	error	ERR	::ERR-ur::
or	more	OR	::MOR::
ow	cow	    OW	::KOW::
oy	oy	    OY	::OY::
ur	urn	    UR	::URN::

Consonants			
To hear	as in	type	For example,
b	bunk	B	::BUHNK::
ch	chart	CH	::CHAHRT::
d	dust	D	::DUHST::
f	first	F	::FURST::
g	glow	G	::GLOH::
h	horse	H	::HORS::
j	jell	J	::JEHL::
k	kite	K	::KYT::
l	laugh	K	::LAF::
m	mask	M	::MASK::
n	nest	N	::NEHST::
ng	ring	NG	::RIHNG::
nk	rink	NK	::RIHNK::
p	pop	    P	::PAHP::
qu	quote	KW	::KWOHT::
r	rain	R	::RAYN::
s	slice	S	::SLYS::
sh	shy	    SH	::SHY::
t	tarte	T	::TART::
th	though	DH	::DHOH::
th	think	TH	::THIHNK::
v	van	    V	::VAN::
w	win   	W	::WIHN::
x	axe	    KS	::AKS::
y	yes	    Y	::YEHS::
z	zen  	Z	::ZEHN::
zh	measure	ZH	::MEH-zhur::

          Arguments
            word: original word
            phonetic: phonetic respelling to use for the word


            Note that using this features requires the caruso model
          """)
def apply_respelling(word: str, phonetic: str) -> str:
    """
    Wraps a word with a <respell> tag to provide a custom pronunciation.
    """
    return f'<respell value="{phonetic}">{word}</respell>'


# === Multi-tag Composition ===

def apply_all_tags(
    text: str,
    pitch: int | None = None,
    tempo: float | None = None,
    loudness: int | None = None
) -> str:
    """
    Applies multiple AI Director tags in nested order.
    """
    if pitch is not None:
        text = wrap_with_pitch(text, pitch)
    if tempo is not None:
        text = wrap_with_tempo(text, tempo)
    if loudness is not None:
        text = wrap_with_loudness(text, loudness)
    return text


# === Extraction Helpers (Optional) ===

def extract_tagged_segments(text: str, tag: str) -> list[str]:
    """
    Returns all inner text segments wrapped with a given AI Director tag.
    """
    return re.findall(f"<{tag}[^>]*?>(.*?)</{tag}>", text, re.DOTALL)


# === Example Presets (Optional) ===

def suggest_emphasis(text: str) -> str:
    """
    Applies high pitch and louder volume to emphasize a phrase.
    """
    return apply_all_tags(text, pitch=150, loudness=6, tempo=1.1)