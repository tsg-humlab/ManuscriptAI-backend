import rdflib
import re
from rdflib.namespace import RDFS
from autogen import ConversableAgent
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import random

# Load environment variables
load_dotenv()

# ===============================
# LLM Config
# ===============================
llm_config = {
    "model": "gpt-3.5-turbo-16k",
    "api_key": os.getenv('OPENAI_API_KEY'),
    "temperature": 0.0
}

# ===============================
#  Presenter Agents
# ===============================
support_presenter_agent = ConversableAgent(
    name="SupportPresenter",
    system_message="""
    You are a data provider for a manuscript's support material.
    You receive a single piece of text describing the support (possibly in various languages).
    You must send a message to the MaterialClassifier:
      "Guess what is this data about? [DATA: <support_val>]"
    No extra commentary or transformations.
    """,
    llm_config=llm_config,
    # We'll rely on max_turns to limit conversation
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

script_presenter_agent = ConversableAgent(
    name="ScriptPresenter",
    system_message="""
    You are a data provider for manuscript handwriting form.
    You receive a single piece of text describing the script (possibly in various languages).
    You must send a message to the ScriptClassifier:
      "Guess what is this data about? [DATA: <script_val>]"
    No extra commentary or transformations.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

decorations_presenter_agent = ConversableAgent(
    name="DecorationsPresenter",
    system_message="""
    You are a data provider for manuscript decorations.
    You receive a piece of text describing possible decorations (in various languages/synonyms),
    and you must send a message to the DecorationsClassifier:
      "Guess what is this data about? [DATA: <decoration_val>]"
    No extra commentary or transformations.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

format_presenter_agent = ConversableAgent(
    name="FormatPresenter",
    system_message="""
    You are a data provider for manuscript format.
    You receive a piece of text describing possible format(s) 
    (e.g., "folio, quarto" or synonyms in various languages).
    You must send a message to the FormatClassifier:
      "Guess what is this data about? [DATA: <format_val>]"
    No extra commentary or transformations.
  """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

binding_presenter_agent = ConversableAgent(
    name="BindingPresenter",
    system_message="""
    You are a data provider for manuscript binding.
    You receive a piece of text describing possible binding technique(s) 
    (in various languages or synonyms).
    You must send a message to the BindingClassifier:
      "Guess what is this data about? [DATA: <binding_val>]"
    No extra commentary or transformations.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

ink_presenter_agent = ConversableAgent(
    name="InkPresenter",
    system_message="""
    You are a data provider for manuscript ink.
    You receive a piece of text describing possible ink(s) (e.g., 'ironGallInk, redInk').
    You must send a message to the InkClassifier:
      'Guess what is this data about? [DATA: <ink_val>]'
    No extra commentary or transformations.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

# ===============================
# Classifier Agents
# ===============================

# A. MaterialClassifier for support_type
valid_materials = {
    "papyrus", "parchment", "silk", "bark", "palmLeaves", "paper", "vellum",
    "donkeySkin", "marbledPaper", "uterineVellum", "russiaLeather", "calico",
    "canvas", "sheepskin", "velvet", "naturalGoatskin", "roughSkin", "satin",
    "deerskin", "pigskin", "morocco"
}


def classifier_termination(msg):
    """
    Ends conversation once the classifier agent's final reply is:
      - one of the valid materials, or
      - 'null'
    """
    content = msg["content"].strip()
    return (content in valid_materials) or (content == "null")


material_classifier_agent = ConversableAgent(
    name="MaterialClassifier",
    system_message="""
    You are a classification agent for manuscript support materials.
    The text you receive may describe exactly one of the following 
    materials (in various languages or synonyms):
    [
    papyrus, parchment, silk, bark, palmLeaves, paper, vellum, donkeySkin,
    marbledPaper, uterineVellum, russiaLeather, calico, canvas, sheepskin,
    velvet, naturalGoatskin, roughSkin, satin, deerskin, pigskin, morocco
    ]

    If the text indicates one or more of these materials (from the list), respond only with a comma-separated list indicating the exact corresponding value(s) from the list, e.g. "calico, paper". 
    If there's no match, respond with "null".
    No extra commentary.
    """,
    llm_config=llm_config,
    is_termination_msg=classifier_termination,
    human_input_mode="NEVER"
)

# B. ScriptClassifier for handwriting_form
valid_scripts = {
    "uncial", "halfUncial", "carolingianMinuscule", "textualis", "cursiva",
    "bastarda", "mercantesca", "anglosaxonMinuscule", "rotunda", "notarile",
    "humanistic", "insularScript", "visigothic", "beneventan", "merovingian",
    "luxueilMinuscule", "ashuriScript", "byzantineMinuscule", "kufic", "maghrebi",
    "nandinagari", "brahmi", "kana", "pallava", "baybayin", "nahuatlWriting",
    "chanceryHand", "cyrillicScript", "naskh", "devanagari", "chineseCalligraphy",
    "phagsPa", "khmer", "geez", "mayaHieroglyphs"
}


def script_classifier_termination(msg):
    content = msg["content"].strip()
    return (content in valid_scripts) or (content == "null")


script_classifier_agent = ConversableAgent(
    name="ScriptClassifier",
    system_message="""
    You are a classification agent for manuscript handwriting forms.
    The text may describe exactly one of these script forms (in various languages or synonyms):
    [
    uncial, halfUncial, carolingianMinuscule, textualis, cursiva,
    bastarda, mercantesca, anglosaxonMinuscule, rotunda, notarile,
    humanistic, insularScript, visigothic, beneventan, merovingian,
    luxueilMinuscule, ashuriScript, byzantineMinuscule, kufic, maghrebi,
    nandinagari, brahmi, kana, pallava, baybayin, nahuatlWriting,
    chanceryHand, cyrillicScript, naskh, devanagari, chineseCalligraphy,
    phagspa, khmer, geez, mayaHieroglyphs
    ]

    If the text indicates one or more of these script forms (from the list), respond only with a comma-separated list indicating the exact corresponding value(s) from the list, e.g. "uncial, bastarda". 
    If there's no match, respond with "null".
    No extra commentary or explanation.
    """,
    llm_config=llm_config,
    is_termination_msg=script_classifier_termination,
    human_input_mode="NEVER"
)

valid_decorations = {
    "illumination", "miniature", "historiatedInitial", "borderDesign", "drollerie", "bindingDecoration", "tooling",
    "embossing", "decoratedInitial", "schematicDrawing", "penworkInitial", "coloredDrawing", "figure", "ornamentation",
    "illustrationCycle", "panel", "fastener", "clasp"
}

decorations_classifier_agent = ConversableAgent(
    name="DecorationsClassifier",
    system_message="""
    You are a classification agent for manuscript decorations.
    The text may describe one or MORE decorations from this list (in various languages/synonyms):
    [
    illumination, miniature, historiatedInitial, borderDesign, drollerie,
    bindingDecoration, tooling, embossing, decoratedInitial, schematicDrawing,
    penworkInitial, coloredDrawing, figure, ornamentation, illustrationCycle,
    panel, fastener, clasp
    ]
    If the text indicates one or more of these decorations (from the list), respond only with a comma-separated list indicating the exact corresponding value(s) from the list, e.g. "illumination, miniature". 
    If none, respond with "null".
    No extra commentary or explanation.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

valid_formats = {
    "quarto", "folio", "octavo", "duodecimo", "sextodecimo"
}

format_classifier_agent = ConversableAgent(
    name="FormatClassifier",
    system_message="""
      You are a classification agent for manuscript format. You are also an expert of medieval manuscript format. 
      The text may describe one or MORE of these known manuscript formats from the list (in various languages/synonyms):
      [
        quarto (4to),
        folio (2to),
        octavo (8vo),
        duodecimo (12mo),
        sextodecimo (16mo)
      ]
      If recognized, respond with a comma-separated list of the matching items (e.g., "folio, quarto").
      If none, respond with "null".
      No extra commentary or explanation.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

valid_bindings = {
    "copticBinding", "carolingianBinding", "romanesqueBinding", "gothicBinding", "limpVellumBinding",
    "sewnOnCordsBinding"
}

binding_classifier_agent = ConversableAgent(
    name="BindingClassifier",
    system_message="""
    You are a classification agent for manuscript binding techniques.
    You are also an expert of binding techniques. 
    The text may describe one or MORE of the binding techniques from this list (in various languages/synonyms):

    [copticBinding, carolingianBinding, romanesqueBinding, gothicBinding, limpVellumBinding, sewnOnCordsBinding]

    If recognized, respond with a comma-separated list of the matching items from the list, e.g. "copticBinding, gothicBinding", respecting their capitalization
    If none, respond "null".
    No extra commentary or explanation.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

valid_inks = {
    "carbonInk",
    "invisibleInk",
    "copperGallInk",
    "redInk",
    "ironGallInk",
    "coloredInk",
    "organicInk"
}

ink_classifier_agent = ConversableAgent(
    name="InkClassifier",
    system_message="""
    You are a classification agent for manuscript ink.
    The text may reference one or MORE of these (in various languages or synonyms):
    [
      carbonInk,
      invisibleInk,
      copperGallInk,
      redInk,
      ironGallInk,
      coloredInk,
      organicInk
    ]
    If recognized, respond with a comma-separated list of the matching inks (e.g. "ironGallInk, redInk").
    If none, respond with "null".
    No extra commentary or explanation.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)


# ===============================
#  Agents with tools
# ===============================

def wikidata_query_with_mwapi(name: str) -> str:
    query = f"""
    SELECT ?item WHERE {{
      SERVICE wikibase:mwapi {{
        bd:serviceParam wikibase:endpoint "www.wikidata.org";
                        wikibase:api "EntitySearch";
                        mwapi:search "{name}";
                        mwapi:language "en".
        ?item wikibase:apiOutputItem mwapi:item.
      }}
      ?item wdt:P31 wd:Q5.  # must be a human
    }}
    LIMIT 1
    """
    # Now do the GET:
    params = {
        "query": query,
        "format": "json"
    }
    endpoint = "https://query.wikidata.org/sparql"
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        data = r.json()
        bindings = data.get("results", {}).get("bindings", [])
        if bindings:
            return bindings[0]["item"]["value"]
    except Exception as e:
        print(f"[mwapi tool] Error searching for '{name}': {e}")
    return ""  # no match or error



names_wikidata_agent = ConversableAgent(
    name="AuthorsWikidataAgent",
    system_message="""
    You are a 'Wikidata lookup' agent.

You receive a list of personal names (e.g., "Alice, Bob"), and for each name:
  1) Call the function 'wikidata_query_with_mwapi' exactly once.
  2) If there's a Wikidata URI, collect it (e.g., "http://www.wikidata.org/entity/Q999").
  3) If no URI is found, collect nothing for that name.

At the end:
  - If you found one or more URIs, output them in a single comma-separated line, e.g.:
       http://www.wikidata.org/entity/Q999, http://www.wikidata.org/entity/Q123
  - If none were found, output just the word "null".

No extra commentary. No repeated lines. 
Produce exactly one final message, then end immediately.
""",
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

# We register the function for LLM usage (the agent can “see” it and call it by name).
names_wikidata_agent.register_for_llm(
    name="wikidata_query_with_mwapi",
    description="Queries Wikidata for an author name and returns a single URI or empty string"
)(wikidata_query_with_mwapi)

# The agent that actually executes the calls:
user_proxy = ConversableAgent(
    name="LocalUserProxy",
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

# 3) Register the real Python function under the same name:
user_proxy.register_for_execution(name="wikidata_query_with_mwapi")(wikidata_query_with_mwapi)


def wikidata_query_for_work(work_title: str = None) -> str:
    """
    Queries Wikidata for a creative/literary work **by title only**.

    Returns:
      - The matched work's URI (e.g. "http://www.wikidata.org/entity/QXXXX"), or
      - An empty string if no match is found.
    """
    #  TODO: check if importing the module is needed
    import requests

    # Trim whitespace
    work_title = (work_title or "").strip()

    # If no title, nothing to query
    if not work_title:
        return ""

    # Title-only query: checks for an entity that is (or subclasses) a "creative work" (Q47461344)
    query = f"""
    SELECT ?work WHERE {{
      SERVICE wikibase:mwapi {{
        bd:serviceParam wikibase:endpoint "www.wikidata.org";
                        wikibase:api "EntitySearch";
                        mwapi:search "{work_title}";
                        mwapi:language "en".
        ?work wikibase:apiOutputItem mwapi:item.
      }}
      ?work wdt:P31/wdt:P279* wd:Q47461344 .
    }}
    LIMIT 1
    """

    endpoint = "https://query.wikidata.org/sparql"
    params = {"query": query, "format": "json"}

    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()
        bindings = data.get("results", {}).get("bindings", [])
        if bindings:
            # Return the first match's URI (e.g. "http://www.wikidata.org/entity/QXXXX")
            return bindings[0]["work"]["value"]
    except Exception as e:
        print(f"[work lookup] Error searching for '{work_title}': {e}")

    return ""


works_wikidata_agent = ConversableAgent(
    name="WorksWikidataAgent",
    system_message="""
    You are a 'Wikidata lookup' agent for works. Given a list of work titles, you must:
    1) parse each title (split by commas or semicolons, etc.),
    2) call the function 'wikidata_query_for_work' for each,
    3) collect results (full URIs) in a comma-separated list (or 'null' if none),
    4) Return only that final list, with no extra commentary.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

# Register the new function for LLM usage
works_wikidata_agent.register_for_llm(
    name="wikidata_query_for_work",
    description="Queries Wikidata for a creative/literary work by name"
)(wikidata_query_for_work)

user_proxy_works = ConversableAgent(
    name="LocalUserProxyWorks",
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

user_proxy_works.register_for_execution(name="wikidata_query_for_work")(wikidata_query_for_work)


# ===============================
# Helper functions
# ===============================

def get_last_nonempty_content_excluding_tools(conversation):
    """
    Returns the last non-empty 'content' from conversation.chat_history,
    ignoring any messages from sender='tool' or content='None'.
    """
    for msg in reversed(conversation.chat_history):
        sender = msg.get("sender")
        content = (msg.get("content") or "").strip()
        # Skip tool messages
        if sender == "tool":
            continue
        # Skip empty or explicit "None" content
        if not content or content.lower() == "none":
            continue
        # Found a non-empty, non-tool message
        return content
    return None

def estimate_max_turns_for_works(works_str: str) -> int:
    """
    Estimate how many conversation turns we need based on how many works are listed.
    This is important for the agents that are calling the tools.
    For each item, we allow 2 turns: 1 for calling the tool, 1 for receiving final text.
    Then add 2 as a buffer.
    Example: 3 works => max_turns = 2 + 3*2 = 8
    """
    # split on commas (or semicolons), ignoring empty
    items = [x.strip() for x in works_str.split(",") if x.strip()]
    n = len(items)
    # formula: base + 2 per item
    return 2*n + 2


def get_last_nonempty_content(conversation):
    """
    Look from the end of conversation.chat_history backwards
    and return the first non-empty 'content' we find.
    Return None if none is found.
    """
    for msg in reversed(conversation.chat_history):
        content = msg.get("content")
        if content:
            # non-empty => return
            return content.strip()
    return None

def safe_uri_or_none(candidate: str) -> str:
    """
    If 'candidate' is a valid URI or recognized Q-code, return the full URI string.
    Otherwise return an empty string to signal 'skip it.'
    """
    candidate = candidate.strip()
    if not candidate or candidate.lower() == "null":
        return ""

    # Case A: it starts with http or https => assume it's valid
    if candidate.startswith("http://") or candidate.startswith("https://"):
        return candidate

    # Case B: maybe it's a Q-code like "Q12345" => build a Wikidata URL
    import re
    if re.match(r"^Q\d+$", candidate):
        return f"http://www.wikidata.org/entity/{candidate}"

    # Otherwise, we consider it invalid for our RDF URIs => skip
    return ""


# ===============================
# 4) RDF + Classification Logic
# ===============================
def sanitize_for_uri(value: str) -> str:
    """
    Removes punctuation/spaces to form a clean URI segment.
    """
    return re.sub(r'[^A-Za-z0-9_-]+', '', value)


def transform_data_into_rdf(data):
    g = rdflib.Graph()

    # Namespaces
    EX = rdflib.Namespace("http://example.org/")
    RDF_ = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    XSD = rdflib.Namespace("http://www.w3.org/2001/XMLSchema#")
    MS4AI = rdflib.Namespace("http://ontology.tno.nl/manuscriptAI/")

    # Bind prefixes
    g.namespace_manager.bind("ex", EX)
    g.namespace_manager.bind("rdf", RDF_)
    g.namespace_manager.bind("xsd", XSD)
    g.namespace_manager.bind("ms4ai", MS4AI)

    def add_if_present_literal(graph, subj, pred, key, row):
        """
        If row[key] exists and is not empty, add triple (subj, pred, that_value).
        """
        val = row.get(key)
        if val:
            graph.add((subj, pred, rdflib.Literal(val, datatype=XSD.string)))

    def add_locus(graph, ms_node, ms_id_clean, feature_uri, feature_key, text_val):

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rand_num = random.randint(1000, 9999)

        locus_local_name = f"LOC{timestamp}{rand_num}"

        locus_uri = EX[locus_local_name]
        graph.add((ms_node, MS4AI.includesLocus, locus_uri))
        graph.add((locus_uri, RDF_.type, MS4AI.Locus))
        graph.add((locus_uri, MS4AI.concernsFeature, feature_uri))
        graph.add((locus_uri, MS4AI.includesText, rdflib.Literal(text_val, datatype=XSD.string)))

    # Process each manuscript
    for manuscript in data:
        row = manuscript.get("data", {})
        ms_id = row.get("manuscript_ID")
        if not ms_id:
            # Skip if no ID
            continue

        cleaned_id = sanitize_for_uri(ms_id)
        ms_node = EX[cleaned_id]

        # Mark as ms4ai:Manuscript + shelfmark
        g.add((ms_node, RDF_.type, MS4AI.Manuscript))
        g.add((ms_node, MS4AI.shelfmark, rdflib.Literal(ms_id, datatype=XSD.string)))

        # Add standard fields
        add_if_present_literal(g, ms_node, MS4AI.attributedDate, "century_of_creation", row)
        add_if_present_literal(g, ms_node, MS4AI.width, "dimensions_of_the_manuscript.width", row)
        add_if_present_literal(g, ms_node, MS4AI.length, "dimensions_of_the_manuscript.length", row)
        add_if_present_literal(g, ms_node, MS4AI.thickness, "dimensions_of_the_manuscript.thickness", row)
        add_if_present_literal(g, ms_node, MS4AI.containedWork, "contained_works", row)
        add_if_present_literal(g, ms_node, MS4AI.attributedAuthor, "authors", row)
        add_if_present_literal(g, ms_node, MS4AI.attributedCopyist, "copyists", row)
        add_if_present_literal(g, ms_node, MS4AI.attributedMiniaturist, "miniaturists", row)
        add_if_present_literal(g, ms_node, MS4AI.attributedBookbinder, "bookbinders", row)
        add_if_present_literal(g, ms_node, MS4AI.attributedIlluminator, "illuminators", row)
        add_if_present_literal(g, ms_node, MS4AI.attributedRubricator, "rubricators", row)
        add_if_present_literal(g, ms_node, MS4AI.conservationIntervention, "restoration_history", row)
        add_if_present_literal(g, ms_node, MS4AI.historyOfOwnership, "ownership_history", row)
        add_if_present_literal(g, ms_node, MS4AI.support, "support_type", row)
        add_if_present_literal(g, ms_node, MS4AI.script, "handwriting_form", row)
        add_if_present_literal(g, ms_node, MS4AI.includesDecoration, "decorations", row)
        add_if_present_literal(g, ms_node, MS4AI.foliaCount, "total_folia_count", row)
        add_if_present_literal(g, ms_node, MS4AI.ink, "ink", row)
        add_if_present_literal(g, ms_node, MS4AI.binding, "binding", row)
        add_if_present_literal(g, ms_node, MS4AI["format"], "format", row)

        # rdfs:comment from additional_notes
        notes_val = row.get("additional_notes", "")
        if notes_val:
            g.add((ms_node, RDFS.comment, rdflib.Literal(notes_val, datatype=XSD.string)))

        # incipit => locus
        incipit_val = row.get("incipit")
        if incipit_val:
            add_locus(g, ms_node, cleaned_id, MS4AI.incipit, "incipit", incipit_val)

        # explicit => locus
        explicit_val = row.get("explicit")
        if explicit_val:
            add_locus(g, ms_node, cleaned_id, MS4AI.explicit, "explicit", explicit_val)

        # Classification if support_type is present and not empty
        raw_support = row.get("support_type")
        if raw_support:
            support_val = raw_support.strip()  # avoids NoneType error
            if support_val:
                # 2-agent approach: single-turn
                conversation_result = support_presenter_agent.initiate_chat(
                    recipient=material_classifier_agent,
                    message=f"Guess what is this data about? [DATA: {support_val}]",
                    max_turns=1
                )

                # The classifier's final message
                final_msg = conversation_result.chat_history[-1]["content"].strip()

                print("\n=== FULL CONVERSATION ===")
                for turn in conversation_result.chat_history:
                    role = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{role} => {text}")
                print("=== END OF CONVERSATION ===")

                print(f"[DEBUG] support='{support_val}', classifier_reply='{final_msg}'")

                # if final_msg is in valid_materials => add triple
                if final_msg != "null":
                    # Split by commas to allow multiple recognized items
                    splitted_items = [x.strip() for x in final_msg.split(",")]
                    for mat_item in splitted_items:
                        if mat_item in valid_materials:
                            mat_node = rdflib.URIRef(f"{MS4AI}{mat_item}")
                            g.add((ms_node, MS4AI.hasSupport, mat_node))
                        # else => skip unknown items

        # If handwriting_form is present => classify with script
        raw_script = row.get("handwriting_form")
        if raw_script:
            script_val = raw_script.strip()
            if script_val:
                # Single-turn conversation
                conv_script = script_presenter_agent.initiate_chat(
                    recipient=script_classifier_agent,
                    message=f"Guess what is this data about? [DATA: {script_val}]",
                    max_turns=1
                )
                final_script = conv_script.chat_history[-1]["content"].strip()

                print("\n=== SCRIPT CONVERSATION ===")
                for turn in conv_script.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END SCRIPT ===\n")

                print(f"[DEBUG] handwriting_form='{script_val}', classifier_reply='{final_script}'")

                if final_script != "null":
                    # Split on commas for multiple recognized items
                    splitted_scripts = [x.strip() for x in final_script.split(",")]
                    for scr_item in splitted_scripts:
                        if scr_item in valid_scripts:
                            g.add((ms_node, MS4AI.hasScript, rdflib.URIRef(f"{MS4AI}{scr_item}")))
                        # else => skip unrecognized

        raw_decorations = row.get("decorations")
        if raw_decorations:
            decor_val = raw_decorations.strip()
            if decor_val:
                conv_decor = decorations_presenter_agent.initiate_chat(
                    recipient=decorations_classifier_agent,
                    message=f"Guess what is this data about? [DATA: {decor_val}]",
                    max_turns=1
                )
                final_decor = conv_decor.chat_history[-1]["content"].strip()

                print("\n=== DECORATIONS CONVERSATION ===")
                for turn in conv_decor.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END DECORATIONS ===\n")

                if final_decor != "null":
                    splitted = [x.strip() for x in final_decor.split(",")]
                    for deco_item in splitted:
                        if deco_item in valid_decorations:
                            g.add((ms_node, MS4AI.hasDecoration, rdflib.URIRef(f"{MS4AI}{deco_item}")))
                        # else => skip

        raw_format = row.get("format")
        if raw_format:
            format_val = raw_format.strip()
            if format_val:
                conv_format = format_presenter_agent.initiate_chat(
                    recipient=format_classifier_agent,
                    message=f"Guess what is this data about? [DATA: {format_val}]",
                    max_turns=1
                )
                final_format = conv_format.chat_history[-1]["content"].strip()

                print("\n=== FORMAT CONVERSATION ===")
                for turn in conv_format.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END FORMAT ===\n")

                if final_format != "null":
                    splitted = [x.strip() for x in final_format.split(",")]
                    for fmt in splitted:
                        if fmt in valid_formats:
                            g.add((ms_node, MS4AI.hasFormat, rdflib.URIRef(f"{MS4AI}{fmt}")))
                        # else => skip

        raw_binding = row.get("binding")
        if raw_binding:
            bind_val = raw_binding.strip()
            if bind_val:
                conv_bind = binding_presenter_agent.initiate_chat(
                    recipient=binding_classifier_agent,
                    message=f"Guess what is this data about? [DATA: {bind_val}]",
                    max_turns=1
                )
                final_bind = conv_bind.chat_history[-1]["content"].strip()

                print("\n=== BINDING CONVERSATION ===")
                for turn in conv_bind.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END BINDING ===\n")

                if final_bind != "null":
                    splitted = [x.strip() for x in final_bind.split(",")]
                    for bItem in splitted:
                        if bItem in valid_bindings:
                            g.add((ms_node, MS4AI.hasBinding, rdflib.URIRef(f"{MS4AI}{bItem}")))

        # Ink classification
        raw_ink = row.get("ink")
        if raw_ink:
            ink_val = raw_ink.strip()
            if ink_val:
                conv_ink = ink_presenter_agent.initiate_chat(
                    recipient=ink_classifier_agent,
                    message=f"Guess what is this data about? [DATA: {ink_val}]",
                    max_turns=1
                )
                final_ink = conv_ink.chat_history[-1]["content"].strip()

                print("\n=== INK CONVERSATION ===")
                for turn in conv_ink.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END INK ===\n")

                if final_ink != "null":
                    splitted = [x.strip() for x in final_ink.split(",")]
                    for ink_item in splitted:
                        if ink_item in valid_inks:
                            g.add((ms_node, MS4AI.hasInk, rdflib.URIRef(f"{MS4AI}{ink_item}")))
                        # else skip


        # authors wikidata classification
        # Extract author field
        raw_authors = (row.get("authors", "") or "").strip()
        # Only proceed if we actually have authors
        if raw_authors:
            # Split authors on comma
            authors_list = [auth.strip() for auth in raw_authors.split(",")]

            # For each individual author, perform a separate lookup
            for author_name in authors_list:


                # Initiate the conversation for this single author
                conv_auth = user_proxy.initiate_chat(
                    recipient=names_wikidata_agent,
                    message=f"Please do a Wikidata lookup for: [AUTHOR_LIST: {author_name}] using the function 'wikidata_query_with_mwapi'",
                    max_turns=2
                )

                # Use the helper to retrieve final URIs from the conversation
                final_uris = get_last_nonempty_content_excluding_tools(conv_auth)
                if not final_uris:
                    final_uris = "null"
                else:
                    final_uris = final_uris.strip()

                # Print out the conversation details for debugging or logging
                print("\n=== AUTHORS WIKIDATA CONVERSATION ===")
                for turn in conv_auth.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END AUTHORS CONVERSATION ===\n")

                # If URIs were found, add them to your graph
                if final_uris.lower() != "null":
                    splitted = [uri.strip() for uri in final_uris.split(",")]
                    for u in splitted:
                        g.add((ms_node, MS4AI.hasAttributedAuthor, rdflib.URIRef(u)))

        # Copyists
        # Handle copyists in a similar way to authors
        raw_copyists = (row.get("copyists", "") or "").strip()

        # Only proceed if we actually have copyists
        if raw_copyists:
            # Split copyists on comma
            copyists_list = [c.strip() for c in raw_copyists.split(",")]

            # For each individual copyist, perform a separate lookup
            for copyist_name in copyists_list:
                # Estimate max turns for this single copyist

                conv_copyists = user_proxy.initiate_chat(
                    recipient=names_wikidata_agent,
                    message=f"Please do a Wikidata lookup for: [COPYISTS_LIST: {copyist_name}] using the function 'wikidata_query_with_mwapi'",
                    max_turns=2
                )

                final_uris_copyists = get_last_nonempty_content_excluding_tools(conv_copyists)
                if not final_uris_copyists:
                    final_uris_copyists = "null"
                else:
                    final_uris_copyists = final_uris_copyists.strip()


                print("\n=== COPYISTS WIKIDATA CONVERSATION ===")
                for turn in conv_copyists.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END COPYISTS CONVERSATION ===\n")


                if final_uris_copyists.lower() != "null":
                    splitted_copyists = [x.strip() for x in final_uris_copyists.split(",")]
                    for uri in splitted_copyists:
                        g.add((ms_node, MS4AI.hasAttributedCopyist, rdflib.URIRef(uri)))

        # Miniaturists
        raw_minis = (row.get("miniaturists", "") or "").strip()
        if raw_minis:
            # Split miniaturists on comma
            minis_list = [m.strip() for m in raw_minis.split(",")]

            # For each individual miniaturist, perform a separate lookup
            for mini_name in minis_list:
                conv_minis = user_proxy.initiate_chat(
                    recipient=names_wikidata_agent,
                    message=f"Please do a Wikidata lookup for: [MINIATURISTS_LIST: {mini_name}] using the function 'wikidata_query_with_mwapi'",
                    max_turns=2
                )

                final_uris_minis = get_last_nonempty_content_excluding_tools(conv_minis)
                if not final_uris_minis:
                    final_uris_minis = "null"
                else:
                    final_uris_minis = final_uris_minis.strip()

                # Log the conversation for debugging
                print("\n=== MINIATURISTS WIKIDATA CONVERSATION ===")
                for turn in conv_minis.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END MINIATURISTS CONVERSATION ===\n")


                if final_uris_minis.lower() != "null":
                    splitted_minis = [x.strip() for x in final_uris_minis.split(",")]
                    for uri in splitted_minis:
                        g.add((ms_node, MS4AI.hasAttributedMiniaturist, rdflib.URIRef(uri)))


        # bookbinders
        raw_binders = (row.get("bookbinders", "") or "").strip()
        if raw_binders:
            binders_list = [b.strip() for b in raw_binders.split(",")]
            for binder_name in binders_list:
                # Optionally estimate max turns for each binder (if you want different conversation lengths)
                #dynamic_turns_binders = estimate_max_turns_for_works(binder_name)

                conv_binders = user_proxy.initiate_chat(
                    recipient=names_wikidata_agent,
                    message=f"Please do a Wikidata lookup for: [BOOKBINDERS_LIST: {binder_name}] using the function 'wikidata_query_with_mwapi'",
                    max_turns=2
                )

                final_uris_binders = get_last_nonempty_content_excluding_tools(conv_binders)
                if not final_uris_binders:
                    final_uris_binders = "null"
                else:
                    final_uris_binders = final_uris_binders.strip()

                print("\n=== BOOKBINDERS WIKIDATA CONVERSATION ===")
                for turn in conv_binders.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END BOOKBINDERS CONVERSATION ===\n")

                if final_uris_binders.lower() != "null":
                    splitted_binders = [x.strip() for x in final_uris_binders.split(",")]
                    for uri in splitted_binders:
                        g.add((ms_node, MS4AI.hasAttributedBookbinder, rdflib.URIRef(uri)))

        # illuminators => hasAttributedIlluminator
        raw_illums = (row.get("illuminators", "") or "").strip()
        if raw_illums:
            illums_list = [i.strip() for i in raw_illums.split(",")]
            for illum_name in illums_list:
                #dynamic_turns_illums = estimate_max_turns_for_works(illum_name)

                conv_illums = user_proxy.initiate_chat(
                    recipient=names_wikidata_agent,
                    message=f"Please do a Wikidata lookup for: [ILLUMINATORS_LIST: {illum_name}] using the function 'wikidata_query_with_mwapi'",
                    max_turns=2
                )

                final_uris_illums = get_last_nonempty_content_excluding_tools(conv_illums)
                if not final_uris_illums:
                    final_uris_illums = "null"
                else:
                    final_uris_illums = final_uris_illums.strip()

                print("\n=== ILLUMINATORS WIKIDATA CONVERSATION ===")
                for turn in conv_illums.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END ILLUMINATORS CONVERSATION ===\n")

                if final_uris_illums.lower() != "null":
                    splitted_illums = [x.strip() for x in final_uris_illums.split(",")]
                    for uri in splitted_illums:
                        g.add((ms_node, MS4AI.hasAttributedIlluminator, rdflib.URIRef(uri)))

        # rubricators => hasAttributedRubricator
        raw_rubrics = (row.get("rubricators", "") or "").strip()
        if raw_rubrics:
            rubrics_list = [r.strip() for r in raw_rubrics.split(",")]
            for rubric_name in rubrics_list:
                #dynamic_turns_rub = estimate_max_turns_for_works(rubric_name)

                conv_rubrics = user_proxy.initiate_chat(
                    recipient=names_wikidata_agent,
                    message=f"Please do a Wikidata lookup for: [RUBRICATORS_LIST: {rubric_name}] using the function 'wikidata_query_with_mwapi'",
                    max_turns=2
                )

                final_uris_rubrics = get_last_nonempty_content_excluding_tools(conv_rubrics)
                if not final_uris_rubrics:
                    final_uris_rubrics = "null"
                else:
                    final_uris_rubrics = final_uris_rubrics.strip()

                print("\n=== RUBRICATORS WIKIDATA CONVERSATION ===")
                for turn in conv_rubrics.chat_history:
                    who = turn.get("sender") or turn.get("role") or "unknown"
                    text = turn.get("content", "")
                    print(f"{who} => {text}")
                print("=== END RUBRICATORS CONVERSATION ===\n")

                if final_uris_rubrics.lower() != "null":
                    splitted_rubrics = [x.strip() for x in final_uris_rubrics.split(",")]
                    for uri in splitted_rubrics:
                        g.add((ms_node, MS4AI.hasAttributedRubricator, rdflib.URIRef(uri)))

                    # contained_works => includesWork
   # raw_works = (row.get("contained_works", "") or "").strip()
    #dynamic_turns_works = estimate_max_turns_for_works(raw_works)  # replicate logic

    #if raw_works:
     #   conv_works = user_proxy_works.initiate_chat(
      #      recipient=works_wikidata_agent,
            # Only pass the work titles, ignoring authors
       #     message=f"Please do a Wikidata lookup for: [WORKS_LIST: {raw_works}] using the function 'wikidata_query_for_work'",
        #    max_turns=dynamic_turns_works
        #)

        # Use helper to handle tool-only or empty responses
        #final_uris_works = get_last_nonempty_content_excluding_tools(conv_works)
        #if not final_uris_works:
         #   final_uris_works = "null"
        #else:
         #   final_uris_works = final_uris_works.strip()

        # Print entire conversation for debugging/logging
        #print("\n=== WORKS WIKIDATA CONVERSATION ===")
        #for turn in conv_works.chat_history:
         #   who = turn.get("sender") or turn.get("role") or "unknown"
          #  text = turn.get("content", "")
           # print(f"{who} => {text}")
        #print("=== END WORKS CONVERSATION ===\n")

        # If valid URIs, add them to the graph
      #  if final_uris_works.lower() != "null":
       #     splitted_works = [x.strip() for x in final_uris_works.split(",")]
        #    for work_uri in splitted_works:
         #       g.add((ms_node, MS4AI.includesWork, rdflib.URIRef(work_uri)))

    return g.serialize(format="turtle")


