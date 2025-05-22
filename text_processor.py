import spacy

# Load the spaCy model. Using en_core_web_sm for a balance of size and capability.
# This will be loaded once when the module is imported.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading language model for the first time. This may take a few minutes.")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def process_text_to_structure(text: str) -> list:
    """
    Processes input text using spaCy and converts it into a hierarchical
    dictionary structure suitable for mind map generation.

    The heuristic used is:
    1. Each sentence in the input text becomes a main branch (a top-level node).
    2. For each sentence:
        - Noun chunks are extracted as potential child nodes of the sentence.
        - Named entities are also extracted as potential child nodes of the sentence.
          (Duplicates between noun chunks and entities are not explicitly handled here
           but could be refined by checking for overlapping text).
    3. The structure is a list of dictionaries, where each dictionary represents a node
       and has a 'text' key and a 'children' key (a list of child node dictionaries).

    Args:
        text: The input string to process.

    Returns:
        A list of dictionaries representing the hierarchical structure.
        Returns an empty list if the input text is empty or only whitespace.
    """
    if not text or text.isspace():
        print("Input text is empty or whitespace. Returning empty structure.")
        return []

    doc = nlp(text)
    mind_map_structure = []

    for sent in doc.sents:
        sentence_node = {"text": sent.text, "children": []}

        # Extract Noun Chunks as children
        for chunk in sent.noun_chunks:
            sentence_node["children"].append({"text": chunk.text, "children": []})

        # Extract Named Entities as children
        # This might create some redundancy if a noun chunk is also a named entity,
        # but it ensures entities are captured.
        # A more sophisticated approach could merge or prioritize these.
        for ent in sent.ents:
            # Avoid adding duplicate text if already captured as a noun chunk (simple check)
            if not any(child["text"] == ent.text for child in sentence_node["children"]):
                sentence_node["children"].append({"text": ent.text, "children": []})
        
        mind_map_structure.append(sentence_node)

    return mind_map_structure

if __name__ == '__main__':
    # Example Usage
    example_text_1 = "The quick brown fox jumps over the lazy dog. The dog barks."
    structure_1 = process_text_to_structure(example_text_1)
    import json
    print("Structure for: '{}'".format(example_text_1))
    print(json.dumps(structure_1, indent=2))

    example_text_2 = "Apple is looking at buying U.K. startup for $1 billion. Meanwhile, Google announced new AI features."
    structure_2 = process_text_to_structure(example_text_2)
    print("\nStructure for: '{}'".format(example_text_2))
    print(json.dumps(structure_2, indent=2))

    example_text_empty = ""
    structure_empty = process_text_to_structure(example_text_empty)
    print("\nStructure for empty text:")
    print(json.dumps(structure_empty, indent=2))

    example_text_whitespace = "   "
    structure_whitespace = process_text_to_structure(example_text_whitespace)
    print("\nStructure for whitespace text:")
    print(json.dumps(structure_whitespace, indent=2))
