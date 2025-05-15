import os
from autogen import ConversableAgent
from dotenv import load_dotenv

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
    You are a data structurer, expert in manuscripts, the medieval period, manuscript cataloging, and proficient in multiple languages (including: Dutch, Italian, French, and German).
    You will receive some raw data from the analyzer agent. They may have, however a csv, turtle, json, XML or XML_TEI structure (as well as other).
    Your task is to process data from the Analyzer agent and return clean, structured JSON. You must identify all relevant details from the raw text (the "data_analyzed") and assign them to the correct fields. Anything that does not fit must go under "data_not_identified" or "extra_information" when appropriate.
    You can use your knowledge of different ways of organizing data (XML, json etc) to understand what are the values that needs to be filled in your json schema.  

    Additionally, you must return **all analyzed data**, including used and discarded elements, under the `"all_data"` field. This field should present a structured summary of everything analyzed.

    Your tasks:

    1. **Extract & Identify**: Carefully read through the provided raw data, looking for any mention of the manuscript’s identifying information and characteristics.
    2. **Organize**: Convert those findings into a strict JSON format with the exact fields listed below.
    3. **Preserve Completeness**: Do not omit important data. If a field is mentioned, include it. If the data is not present in the text, set that field to `null`.
    4. **Maintain Original Language**: Keep the source text in its original language. Do not translate unless explicitly told.
    5. **No Guessing**: If you are not certain about a field, leave it as `null`. Only fill data you can confidently extract from the raw text.

    ---
    ### **JSON Format** 

    Your response MUST be formatted as **valid JSON** with exactly the following fields for each manuscript identified:

    ```json

    {
    "manuscript_ID": "The official shelfmark or identifier assigned by a library, archive, or collection",
    "century_of_creation": "Century (e.g., '12th century', '15th century')",
    "support_type": "e.g. 'parchment', 'paper', 'vellum'...",
    "dimensions_of_the_manuscript": {
        "width": "Numeric value + unit (e.g. '20 cm', '150 mm', or null if not specified)",
        "length": "Numeric value + unit (e.g. '30 cm', '200 mm', or null if not specified)",
        "thickness": "Numeric value + unit (e.g. '3 mm', '0.5 cm', or null if not specified)"
        },
    "contained_works": ["List of works found in the manuscript"],
    "incipit": "The opening words of the text, if available.",
    "explicit": "The final words of the text, if available.",
    "handwriting_form": "The style of handwriting/script (e.g. 'Gothic textualis', 'Caroline minuscule', etc.)",
    "handwriting_notes": "Additional notes or remarks on the script (or null)",
    "decorations": {
      "types": ["Examples: 'miniatures', 'decorated initials', 'historiated initials, etc.'"],
      "details": "A text description of decorative features (or null if not described)"
    },
    "binding_type": "Material/style of the binding (e.g. 'leather over wooden boards', 'modern binding', etc.)",
    "total_folia": "The folio/page notation (e.g. '1r-112v', or null)",
    "ink_type": "Type of ink used (e.g. 'iron gall', 'carbon black', or null if not mentioned)",
    "authors": "List of authors whose works appear in the manuscript, or null if none are identified.",
    "copyists": "List of scribes who copied the text, or null if none are identified.",
    "miniaturists": "List of artists for the miniatures, or null if none are identified.",
    "bookbinders": "List of known binders or binding workshops, or null if none are identified.",
    "illuminators": "List of illuminators (if different from miniaturists), or null if none are identified.",
    "rubricators": "List of individuals who wrote rubrics in red, if known, or null if none are identified.",
    "work_folia": "Mapping of each included work to its corresponding folios (e.g. 'Divina Commedia: 1r-30r')",
    "extra_information": "Catch-all for any additional data not fitting other fields",
    "data_analyzed": "Raw text  of the data the Analyzer provided",
    "data_not_identified": "Any leftover data you could not categorize",
    "mention_of_people": "Any people mentioned",
    "mention_of_place": "Any place mentioned",
    "restoration_history": "Information about the restoration process the manuscript may have gone through",
    "additional_notes": "any additional notes",
    "ownership_history": "relevant information about who owned the manuscript and where it was and is preserved "
    }

    ```
    If any field is **missing**, use `null` instead of guessing.

    **STRICT RULES:**
    - Do NOT change, add, or remove keys.
    - Do NOT invent any data value.
    - Maintain clear JSON formatting.
    - Return `"STRUCTURING COMPLETE"` after finalizing the structure.
    - Do NOT communicate anything else but the structured json above.
    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: "STRUCTURING COMPLETE" in msg["content"],
    human_input_mode="NEVER"
)


def send_manuscipts(data):
    """
    Receives the text of the 3 manuscript boxes from the frontend
    and sends them to the Agents for processing if desired.
    """
    print("received data:", data)
    # Extract manuscripts from form data
    # manuscript1 = request.form.get('manuscript1', '')
    # manuscript2 = request.form.get('manuscript2', '')
    # manuscript3 = request.form.get('manuscript3', '')

    # Example: we show how to forward the combined text to the Analyzer->Structurer flow:
    combined_text = ''
    for key, value in data.items():
        print(f"{key}: {value}")
        combined_text += f"{key}:\n{value}\n\n"
        # combined_text += f"Manuscript1:\n{data['Manuscript1']}\n\nManuscript2:\n{data['Manuscript2']}\n\nManuscript3:\n{data['Manuscript3']}"
    print("\ncombined_text:", combined_text)

    try:
        # Initiate chat: Analyzer -> Structurer
        conversation_result = analyzer_agent.initiate_chat(
            recipient=structurer_agent,
            message=f"Here is the data:\n\n{combined_text}\n\n",
            max_turns=1
        )
        final_response = conversation_result.chat_history[-1]["content"]
        final_response_trimmed = final_response.rstrip('STRUCTURING COMPLETE')
        print("\n Final response:", final_response_trimmed)

        # Return whatever Structurer responded
        # return render_template('final.html', data=final_response)
        return {"message": "Data received successfully!", "response": final_response_trimmed}, 200

    except Exception as e:
        return {'error': str(e)}, 400