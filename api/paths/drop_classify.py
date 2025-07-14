import os
from autogen import ConversableAgent
from dotenv import load_dotenv
import csv
import json
import xml.etree.ElementTree as ET
from langchain.text_splitter import RecursiveCharacterTextSplitter


try:
    import tiktoken
except ImportError:
    tiktoken = None

# Load environment variables
load_dotenv()

model = "gpt-3.5-turbo-16k"
llm_config = {
    "model": model,
    "temperature": 0.0,
    "api_key": os.getenv('OPENAI_API_KEY'),
    "cache": None
}

########################################
# Agents: Data_drop_agent (former analyzer) & Structurer.
########################################

data_drop_agent = ConversableAgent(
    name="DataDropAgent",
    system_message="""
    You are a data provider responsible for presenting raw manuscript data to the Structurer Agent. 
    Your tasks:

    - Present the original manuscript data without modification.
    - Ensure clarity and completeness.
    - Do NOT analyze, structure, or summarize the data.
    - Do NOT interact further with agents or engage with them. Your sole task is to provide data.  

    """,
    llm_config=llm_config,
    is_termination_msg=lambda msg: False,
    human_input_mode="NEVER"
)

structurer_agent = ConversableAgent(
    name="Structurer",
    system_message="""

    You are a data structurer specializing in medieval manuscripts, manuscript cataloging, and multiple modern and ancient languages (including Latin, Dutch, Italian, French, and German). 
    You will receive raw manuscript data in various file formats (CSV, Turtle, JSON, XML, TEI, text, etc.) from the DataDrop Agent.    

    Your task is to:
    
    1. Extract & Identify all pertinent manuscript information from the provided data (the “data_analyzed”).
    2. Organize that information into the strict JSON schema (see below).
    3. Preserve completeness: include all relevant data; if a field is absent in the text, set it to `null`.
    4. Maintain Original Language (no translations).
     4.a  **Verbatim transcribe**: for every extracted field, copy exactly the characters you see in the input (including accents, case, abbreviations).  
      Do NOT translate, normalize spelling, or map to English synonyms.
    5. No Guessing: if unsure, use `null`.
     
    ---
    ### **JSON Format** 
    
    For each manuscript you identify, you MUST produce a single JSON object containing exactly these fields:

    {
    "manuscript_ID": "The official shelfmark or identifier assigned by a library, archive, or collection; null if not present",
    "century_of_creation": "The exact string from the source (e.g. ‘1353; ‘14th century’, or a data range); null if not present",
    "support_type": "The exact support description (e.g. 'parchment', 'paper', 'vellum') as in the source (verbatim, including language and spelling); null if not present",
    "dimensions_of_the_manuscript": {
        "width": "Numeric value + unit (e.g. '20 cm', '150 mm', or null if not specified)",
        "length": "Numeric value + unit (e.g. '30 cm', '200 mm', or null if not specified)",
        "thickness": "Numeric value + unit (e.g. '3 mm', '0.5 cm', or null if not specified)"
        },
    "contained_works": "The exact title(s) of contained work(s) in the manuscript, comma-separated verbatim; null if none",
    "incipit": "The full incipit text exactly as in the source (preserving line breaks and punctuation); null if not present",
    "explicit": "The full explicit text exactly as in the source (preserving line breaks and punctuation); null if not present",
    "handwriting_form": "The script style string exactly as given (e.g. ‘Littera gothica textualis’), or null if not specified",
    "decorations": "The exact decoration‐related text as in the source, including any mentions of miniatures, decorated initials, historiated initials, borders, marginal illustrations, headpieces, tailpieces, frames, etc.; if multiple, concatenate verbatim separated by commas; null if none",
    "binding": "The exact binding description string as in the source; null if not present",
    "total_folia_count": "The sum total of leaves computed: guard leaves + numbered folios (e.g. 2 + 191 = 193), or null",
    "ink": "The exact ink description string as in the source; null if not present",
    "format": "Type of format such as quarto, duodecimo etc. by using the string term in the source, or null",
    "authors": "The exact name(s) of medieval or/and ancient author(s) as reported in the source, comma-separated verbatim; null if none",
    "copyists": "The exact name(s) of medieval copyist(s) as reported in the source, comma-separated verbatim; null if none",
    "miniaturists": "The exact name(s) of medieval miniaturist(s) as reported in the source, comma-separated verbatim; null if none",
    "bookbinders": "The exact name(s) of medieval bookbinder(s) as reported in the source, comma-separated verbatim; null if none",
    "illuminators": "The exact name(s) of medieval illuminator(s) as reported in the source, comma-separated verbatim; null if none",
    "rubricators": "The exact name(s) of medieval rubricator(s) as reported in the source, comma-separated verbatim; null if none",
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


#######################
# Token Counting
#######################

def count_tokens(text: str, model_name: str = "gpt-3.5-turbo-16k") -> int:
    """
    Use tiktoken (if installed) to count tokens for 'text'
    under the given 'model_name'. If tiktoken is absent,
    fallback to len(text)//4 as a naive approximation.
    """
    if tiktoken is None:
        # fallback
        return len(text) // 4
    else:
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))


TOKEN_THRESHOLD = 14000

#######################
# Chunking Functions
#######################

CHUNK_SIZE = 2000  # approx chars per chunk
OVERLAP_PERCENT = 10  # 10% overlap


def chunk_plain_text(text: str) -> list[str]:
    """
    Use RecursiveCharacterTextSplitter for smart context-aware splitting.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * OVERLAP_PERCENT / 100),
        separators=["\n\n", "\n", ".", " "]
    )
    return text_splitter.split_text(text)


def chunk_csv_tsv(content: str, is_tsv=False, max_rows=50) -> list[str]:
    """
    Splits CSV or TSV data into chunk_str blocks, each with up to `max_rows` rows.
    Repeats the header row in each chunk to maintain context.
    """
    delimiter = "\t" if is_tsv else ","
    lines = content.strip().split("\n")
    reader = csv.reader(lines, delimiter=delimiter)

    header = next(reader, None)
    if not header:
        return []

    chunks = []
    current_rows = [header]
    row_count = 0

    for row in reader:
        current_rows.append(row)
        row_count += 1
        if row_count >= max_rows:
            chunk_str = "\n".join(delimiter.join(r) for r in current_rows)
            chunks.append(chunk_str)
            current_rows = [header]  # reset with header again
            row_count = 0

    # leftover rows
    if len(current_rows) > 1:
        chunk_str = "\n".join(delimiter.join(r) for r in current_rows)
        chunks.append(chunk_str)

    # Optionally, you could do some overlap of the last 1-2 rows if your scenario requires it,
    # but typically for CSV data you don't overlap entire rows.
    return chunks


def chunk_json(content: str) -> list[str]:
    """
    Splits JSON data by top-level objects if it's an array,
    or returns a single chunk if it's just one object.
    If invalid JSON, fallback to plain text chunking.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # fallback => treat as plain text with chunk overlap
        return chunk_plain_text(content)

    if isinstance(data, list):
        # create one chunk per item in the list
        # each chunk is a valid JSON array with a single element
        chunks = []
        for item in data:
            chunk_text = json.dumps([item], ensure_ascii=False)
            chunks.append(chunk_text)
        return chunks
    else:
        # single JSON object => single chunk
        return [json.dumps(data, ensure_ascii=False)]


# we are not using this function at the moment
def chunk_tei_by_msdesc(content: str) -> list[str]:
    """
    Splits TEI XML into separate chunks per <msDesc> element
    in the TEI namespace (http://www.tei-c.org/ns/1.0).
    If no <msDesc> is found, returns the entire content as a single chunk.
    """
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        # fallback => plain text chunk
        return chunk_plain_text(content)

    # TEI namespace
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    # check if this is actually TEI by looking at the root tag
    # often root.tag == '{http://www.tei-c.org/ns/1.0}TEI'
    if not root.tag.endswith('TEI'):
        # Not a TEI root => fallback or standard chunk_xml approach
        return [content]

    msdesc_list = root.findall(".//tei:msDesc", ns)  # or ms:item?
    if not msdesc_list:
        # No <msDesc> => return entire TEI as a single chunk
        return [content]

    # Return each <msDesc> as its own chunk (XML string)
    chunks = []
    for msdesc in msdesc_list:
        chunk_str = ET.tostring(msdesc, encoding="unicode")
        chunks.append(chunk_str)

    return chunks


def chunk_xml_general(content: str) -> list[str]:
    """
    1. Parse the XML.
    2. Split by top-level child elements.
    3. If any child's string is longer than CHUNK_SIZE, chunk it further.
    4. If no children exist, or parsing fails, fall back to chunk_plain_text.
    """
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return chunk_plain_text(content)

    children = list(root)

    # If no top-level children, just chunk the entire doc
    if not children:
        entire_doc_str = ET.tostring(root, encoding="unicode")
        # If this entire doc is bigger than CHUNK_SIZE, chunk it
        if len(entire_doc_str) > CHUNK_SIZE:
            return chunk_plain_text(entire_doc_str)
        else:
            return [entire_doc_str]

    # Otherwise, for each top-level child, check size
    chunks = []
    for child in children:
        child_str = ET.tostring(child, encoding="unicode")

        if len(child_str) > CHUNK_SIZE:
            # If the child is still too big, do text-based chunking
            sub_chunks = chunk_plain_text(child_str)
            chunks.extend(sub_chunks)
        else:
            # Child is small enough to be a single chunk
            chunks.append(child_str)

    # 'chunks' now contains all children, with big children chunked further
    return chunks


def chunk_turtle(content: str) -> list[str]:
    """
    Naive: Splits Turtle data by double newlines, with overlap in characters.
    """
    blocks = content.strip().split("\n\n")
    chunk_size = CHUNK_SIZE
    overlap = int(chunk_size * OVERLAP_PERCENT / 100)

    chunks = []
    i = 0
    total_blocks = len(blocks)

    while i < total_blocks:
        end = min(i + chunk_size, total_blocks)
        # join the blocks from i..end as a single chunk
        joined = "\n\n".join(blocks[i:end])
        chunks.append(joined)

        i = end - overlap
        if i < 0:
            i = end

    return chunks


def chunk_file_by_type(content: str, extension: str) -> list[str]:
    """
    Decide chunking strategy based on extension.
    """
    ext = extension.lower().strip()
    if ext in ("csv", "tsv"):
        return chunk_csv_tsv(content, is_tsv=(ext == "tsv"))
    elif ext == "json":
        return chunk_json(content)
    elif ext in ("xml", "tei"):
        return chunk_xml_general(content)
    elif ext in ("ttl", "turtle"):
        return chunk_turtle(content)
    else:
        return chunk_plain_text(content)


###############
# Main function
###############
def drop_classify(data):
    raw_text = data.get("content", "")
    extension = data.get("extension", "txt").lower().strip()

    # 1) Split the file into chunks
    chunks = chunk_file_by_type(raw_text, extension)

    # 2) Process each chunk sequentially, keeping both reply and chunk
    results: list[tuple[str, str]] = []
    for chunk_text in chunks:
        conversation_result = data_drop_agent.initiate_chat(
            recipient=structurer_agent,
            message=f"Here is the data:\n{chunk_text}",
            max_turns=1
        )
        # The structurer agent's final message is the last message => must be valid JSON (object or array)
        final_msg = conversation_result.chat_history[-1]["content"]
        results.append((final_msg, chunk_text))

    # 3) Parse every agent reply into a flat list of (parsed_json, chunk_text)
    parsed_sequence: list[tuple[dict, str]] = []
    for structurer_json, chunk_text in results:
        try:
            parsed = json.loads(structurer_json)
        except json.JSONDecodeError:
            print("[WARNING] Could not parse Structurer JSON:\n", structurer_json)
            continue

        if isinstance(parsed, dict):
            parsed_sequence.append((parsed, chunk_text))
        elif isinstance(parsed, list):
            for item in parsed:
                parsed_sequence.append((item, chunk_text))
        else:
            print("[WARNING] Unexpected JSON shape:", type(parsed))

    # 4) Helper: merge source→target (skip manuscript_ID, skip empty values)
    def merge_dicts_in_place(target: dict, source: dict) -> None:
        for key, val_src in source.items():
            if key == "manuscript_ID" or val_src in (None, "", [], {}):
                continue

            val_tgt = target.get(key)
            if isinstance(val_src, dict) and isinstance(val_tgt, dict):
                merge_dicts_in_place(val_tgt, val_src)
            elif not val_tgt:
                target[key] = val_src
            elif val_tgt != val_src:
                target[key] = f"{val_tgt} / {val_src}"

    # 5) Merge records, using chunk_text to build data_analyzed
    merged_manuscripts: list[dict] = []
    last_with_id: dict | None = None

    for ms_dict, chunk_text in parsed_sequence:
        has_id = bool(ms_dict.get("manuscript_ID") and str(ms_dict["manuscript_ID"]).strip())
        if has_id:
            #  initialize data_analyzed to this chunk
            ms_dict["data_analyzed"] = chunk_text
            merged_manuscripts.append(ms_dict)
            last_with_id = ms_dict
        else:
            if last_with_id is not None:
                # Merge other fields
                merge_dicts_in_place(last_with_id, ms_dict)
                # Append this chunk to data_analyzed
                existing = last_with_id.get("data_analyzed", "")
                last_with_id["data_analyzed"] = (existing + "\n" + chunk_text).strip()
            else:
                # No prior ID: treat this as its own record, but still record the chunk
                ms_dict["data_analyzed"] = chunk_text
                # Edge-case: first record has no ID
                merged_manuscripts.append(ms_dict)

    # 6) Return the merged list
    return {"structured_data": merged_manuscripts}


