import os
from autogen import ConversableAgent
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# LLM Configuration
model = "gpt-3.5-turbo-16k"
llm_config = {
    "model": model,
    "temperature": 0.0,
    "api_key": os.getenv('OPENAI_API_KEY'),
    "cache": None
}

# --- Agents ---

# User Agent
analyzer_agent = ConversableAgent(
    name="Analyzer",
    system_message="""
    You are a **data provider** responsible for presenting raw manuscript data to the Structurer Agent. 
    Your tasks:

    - Present the original manuscript data **without modification**.
    - Ensure clarity and completeness.
    - Do NOT analyze, structure, or summarize the data.
    - Do NOT interact further with agents or engage with them. Your sole task is to provide data.  

    Always return the full dataset without making assumptions.
    Only provide the data without engaging in further conversation out of topic.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: "Here is the data" in msg["content"],
    human_input_mode="NEVER"
)

# Structurer Agent
structurer_agent = ConversableAgent(
    name="Structurer",
    system_message="""

    You are a data structurer specializing in medieval manuscripts, manuscript cataloging, and multiple languages (including Dutch, Italian, French, and German). 
    You will receive raw manuscript data in various file formats (CSV, Turtle, JSON, XML, TEI, text, etc.) from the DataDrop Agent.

    Your task is to:

    1. Extract & Identify all pertinent manuscript information from the provided data (the “data_analyzed”).
    2. Organize that information into the strict JSON schema (see below).
    3. Preserve completeness: include all relevant data; if a field is absent in the text, set it to `null`.
    4. Maintain Original Language (no translations).
    5. No Guessing: if unsure, use `null`.


    ---
    ### **JSON Format** 

    For each manuscript you identify, you MUST produce a single JSON object containing exactly these fields:

    {
    "manuscript_ID": "The official shelfmark or identifier assigned by a library, archive, or collection, or null if not specified",
    "century_of_creation": "Century (e.g., '12th century', '15th century')",
    "support_type": "e.g. 'parchment', 'paper', 'vellum'...",
    "dimensions_of_the_manuscript": {
        "width": "Numeric value + unit (e.g. '20 cm', '150 mm', or null if not specified)",
        "length": "Numeric value + unit (e.g. '30 cm', '200 mm', or null if not specified)",
        "thickness": "Numeric value + unit (e.g. '3 mm', '0.5 cm', or null if not specified)"
        },
    "contained_works": "A single comma-separated string of the works found in the manuscript",
    "incipit": "The opening words of the text, if available.",
    "explicit": "The final words of the text, if available.",
    "handwriting_form": "The style of handwriting/script (e.g. 'Gothic textualis', 'Caroline minuscule', etc.)",
    "decorations": "all information regarding decorations such as 'miniatures', 'decorated initials', 'historiated initials, etc.'",
    "binding_type": "Information about the type or/and material or style of the binding in the manuscript",
    "total_folia": "The folio/page notation (e.g. '1r-112v', or null)",
    "ink_type": "Type of ink used (e.g. 'iron gall', 'carbon black', or null if not mentioned)",
    "format": "Type of format such as quarto, duodecimo etc., or null",
    "authors": "A single comma-separated string of authors (e.g. 'Author1, Author2'), or null if none are identified.",
    "copyists": "A single comma-separated string of copyists (e.g. 'Copyist1, Copyist2'), or null if none are identified.",
    "miniaturists": "A single comma-separated string of miniaturists, or null if none.",
    "bookbinders": "A single comma-separated string of bookbinders, or null if none.",
    "illuminators": "A single comma-separated string of illuminators, or null if none.",
    "rubricators": "A single comma-separated string of rubricators, or null if none.",
    "restoration_history": "Information about the restoration process the manuscript may have gone through",
    "additional_notes": "any additional notes/texts that are about the manuscript but do not fit any of the above indicated categories",
    "ownership_history": "relevant information about who owned the manuscript and where it was and is preserved "
    }

    ---

    #### Important Rules:

    1. **No extra keys** beyond those listed above.  
    2. **No arrays** for authors, copyists, miniaturists, etc. Instead, a single **string** with items separated by commas.  
    3. If a field is missing or uncertain, use `null`.  
    4. Output MUST be valid JSON only—no extra commentary, no lines before or after the JSON.  
    5. End your message **immediately** after the final brace "}".  

    If you find multiple manuscripts in the data, produce an array of such JSON objects in one single valid JSON structure, for example:

    [
        {
            "manuscript_ID": "...",
            ...  // all the fields
        },
        {
            "manuscript_ID": "...",
            ... // second manuscript
        }
    ]

    No extra text or commentary beyond this array.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)


def send_manuscipts(data):
    """
    Receives the text of the (potentially) multiple manuscript boxes from the frontend
    and sends them separately to the Agents for processing.
    """
    # 1. Read the incoming JSON data:
    # data might look like:
    # {
    #   "Manuscript1": "<manuscript> ... </manuscript>",
    #   "Manuscript2": "<manuscript> ... </manuscript>",
    #   ...
    # }

    # 2. We'll store individual structured results here:
    results = []

    # 3. For each manuscript key in the incoming data, we start a new conversation
    #    with the Analyzer agent, which then hands off to the Structurer agent.
    for manuscript_key, manuscript_value in data.items():
        # ----- STEP A: Prepare the text for the Analyzer agent -----

        # This is what is sent to the Analyzer agent:
        analyzer_input_text = f"Here is the data for {manuscript_key}:\n\n{manuscript_value}\n\n"

        # Show it in server logs so we can see EXACTLY how the text looks before sending.
        print("\n----------")
        print(f"Sending to Analyzer for {manuscript_key}:")
        print(analyzer_input_text)
        print("----------\n")

        # ----- STEP B: Initiate the conversation with Analyzer, specifying that it should
        #               forward the data to Structurer. -----
        conversation_result = analyzer_agent.initiate_chat(
            recipient=structurer_agent,
            message=analyzer_input_text,
            max_turns=1
        )

        # conversation_result contains the entire conversation (Analyzer + Structurer).
        # We'll retrieve the Structurer's final response:
        final_response = conversation_result.chat_history[-1]["content"]

        # The Structurer's response usually ended with "STRUCTURING COMPLETE".
        final_response_trimmed = final_response.rstrip("STRUCTURING COMPLETE")

        # ----- STEP C: Append the final structured JSON to our results -----
        # We store the result as something like: { "Manuscript1": "structured JSON" }
        results.append({manuscript_key: final_response_trimmed})
        print(results)

    # 4. Return all the results as a JSON array back to your frontend
    return {"structured_results": results}, 200
