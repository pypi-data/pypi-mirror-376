import logging, os, re
from fastmcp import FastMCP
from fastmcp.prompts.prompt import PromptMessage, TextContent
from agentmake import agentmake, getDictionaryOutput, DEFAULT_AI_BACKEND, AGENTMAKE_USER_DIR
from biblemate import AGENTMAKE_CONFIG, config
from agentmake.plugins.uba.lib.BibleBooks import BibleBooks
from biblemate.core.bible_db import BibleVectorDatabase

# Configure logging before creating the FastMCP server
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.ERROR)

mcp = FastMCP(name="BibleMate AI")

def getResponse(messages:list) -> str:
    return messages[-1].get("content") if messages and "content" in messages[-1] else "Error!"

@mcp.tool
def search_bible(request:str) -> str:
    """search the bible; search string must be given"""
    bible_file = os.path.join(AGENTMAKE_USER_DIR, "biblemate", "data", "bibles", f"{config.default_bible}.bible")
    if os.path.isfile(bible_file):
        # extract the search string
        try:
            schema = {
                "name": "search_google",
                "description": "search the bible; search string must be given",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_string": {
                            "type": "string",
                            "description": "search string for searching the bible",
                        },
                    },
                    "required": ["search_string"],
                },
            }
            search_string = getDictionaryOutput(request, schema=schema, backend=DEFAULT_AI_BACKEND)["search_string"]
        except:
            search_string_system = "You are a Bible Search String Identifier. Your expertise lies in your ability to identity a search string from the user request. Response the search string ONLY. Enclose the search string with ```search_string and ```"
            search_string = agentmake(request, system=search_string_system)[-1].get("content", "").strip()
            search_string = re.sub(r"^.*?```search_string(.+?)```.*?$", r"\1", search_string, flags=re.DOTALL).strip()
        search_string = re.sub('''^['"]*(.+?)['"]*$''', r"\1", search_string).strip()
        # perform the searches
        abbr = BibleBooks.abbrev["eng"]
        db = BibleVectorDatabase(bible_file)
        exact_matches = [f"({abbr[str(b)][0]} {c}:{v}) {content.strip()}" for b, c, v, content in db.search_verses_partial([search_string])]
        if os.path.getsize(bible_file) > 380000000:
            semantic_matches = [f"({abbr[str(b)][0]} {c}:{v}) {content.strip()}" for b, c, v, content in db.search_meaning(search_string, top_k=config.max_semantic_matches)]
        else:
            semantic_matches = []
        output = f"""# Search for `{search_string}`


## Exact Matches ({len(exact_matches)} verse(s))

{"- " if semantic_matches else ""}{"\n- ".join(exact_matches)}

## Semantic Matches ({len(semantic_matches)} verse(s))

{"- " if semantic_matches else ""}{"\n- ".join(semantic_matches) if semantic_matches else "[`Ollama` is not found! BibleMate AI uses `Ollama` to generate embeddings for semantic searches. You may install it from https://ollama.com/ so that you can perform semantic searches of the Bible with BibleMate AI.]"}"""
        return output
    return ""

@mcp.tool
def compare_bible_translations(request:str) -> str:
    """compare Bible translations; bible verse reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'input_content_plugin': 'uba/every_single_ref', 'tool': 'uba/compare'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def retrieve_bible_study_indexes(request:str) -> str:
    """retrieve smart indexes on studying a particular bible verse; bible verse reference must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'input_content_plugin': 'uba/every_single_ref', 'tool': 'uba/index'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def retrieve_bible_cross_references(request:str) -> str:
    """retrieve cross-references of Bible verses; bible verse reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'input_content_plugin': 'uba/every_single_ref', 'tool': 'uba/xref'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def retrieve_pointed_hebrew_or_accented_greek_bible_verses(request:str) -> str:
    """retrieve Hebrew (with pointed vowels) or Greek (with accents) Bible verses; bible verse reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'tool': 'uba/ohgb'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def retrieve_hebrew_or_greek_bible_verses(request:str) -> str:
    """retrieve Hebrew (without pointed vowels) or Greek (without accents) Bible verses; bible verse reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'tool': 'uba/mob'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def retrieve_english_bible_verses(request:str) -> str:
    """retrieve English Bible verses; bible verse reference(s) must be given, e.g. John 3:16-17; multiple references accepted, e.g. John 3:16; Deut 6:4"""
    global agentmake, getResponse
    messages = agentmake(request, **{'tool': 'uba/net'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def retrieve_english_bible_chapter(request:str) -> str:
    """retrieve English Bible chapter, a whole chapter; bible chapter reference must be given, e.g. John 3"""
    global agentmake, getResponse
    messages = agentmake(request, **{'tool': 'uba/net_chapter'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def read_bible_commentary(request:str) -> str:
    """read bible commentary; bible verse reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'tool': 'uba/ai_comment'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def retrieve_chinese_bible_verses(request:str) -> str:
    """retrieve Chinese Bible verses; bible verse reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'tool': 'uba/cuv'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def refine_bible_translation(request:str) -> str:
    """refine the translation of a Bible verse or passage"""
    global agentmake, getResponse
    messages = agentmake(request, **{'system': 'bible/translate'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_pastor_prayer(request:str) -> str:
    """write a prayer, out of a church pastor heart, based on user input"""
    global agentmake, getResponse
    messages = agentmake(request, **{'system': 'bible/pray'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def ask_theologian(request:str) -> str:
    """ask a theologian about the bible"""
    global agentmake, getResponse
    messages = agentmake(request, **{'system': 'bible/theologian'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def quote_bible_verses(request:str) -> str:
    """quote multiple bible verses in response to user request"""
    global agentmake, getResponse
    messages = agentmake(request, **{'system': 'bible/quote'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def anyalyze_psalms(request:str) -> str:
    """analyze the context and background of the Psalms in the bible"""
    global agentmake, getResponse
    messages = agentmake(request, **{'system': 'bible/david'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def ask_pastor(request:str) -> str:
    """ask a church pastor about the bible"""
    global agentmake, getResponse
    messages = agentmake(request, **{'system': 'bible/billy'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def ask_bible_scholar(request:str) -> str:
    """ask a bible scholar about the bible"""
    global agentmake, getResponse
    messages = agentmake(request, **{'system': 'bible/scholar'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def explain_bible_meaning(request:str) -> str:
    """Explain the meaning of the user-given content in reference to the Bible"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/meaning', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_new_testament_historical_context(request:str) -> str:
    """write the Bible Historical Context of a New Testament passage in the bible; new testament bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/nt_context', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_questions(request:str) -> str:
    """Write thought-provoking questions for bible study group discussion; bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/questions', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_devotion(request:str) -> str:
    """Write a devotion on a bible passage; bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/devotion', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def translate_hebrew_bible_verse(request:str) -> str:
    """Translate a Hebrew bible verse; Hebrew bible text must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/translate_hebrew', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_location_study(request:str) -> str:
    """write comprehensive information on a bible location; a bible location name must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/location', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def translate_greek_bible_verse(request:str) -> str:
    """Translate a Greek bible verse: Greek bible text must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/translate_greek', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def identify_bible_keywords(request:str) -> str:
    """Identify bible key words from the user-given content"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/keywords', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def study_old_testament_themes(request:str) -> str:
    """Study Bible Themes in a Old Testament passage; old testatment bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/ot_themes', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def study_new_testament_themes(request:str) -> str:
    """Study Bible Themes in a New Testament passage; new testament bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/nt_themes', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_old_testament_highlights(request:str) -> str:
    """Write Highlights in a Old Testament passage in the bible; old testament bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/ot_highligths', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_prayer(request:str) -> str:
    """Write a prayer pertaining to the user content in reference to the Bible"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/prayer', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_short_bible_prayer(request:str) -> str:
    """Write a short prayer, in one paragraph only, pertaining to the user content in reference to the Bible"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/short_prayer', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_character_study(request:str) -> str:
    """Write comprehensive information on a given bible character in the bible; a bible character name must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/character', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_thought_progression(request:str) -> str:
    """write Bible Thought Progression of a bible book / chapter / passage; bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/flow', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def quote_bible_promises(request:str) -> str:
    """Quote relevant Bible promises in response to user request"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/promises', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_chapter_summary(request:str) -> str:
    """Write a detailed interpretation on a bible chapter; a bible chapter must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/chapter_summary', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_perspectives(request:str) -> str:
    """Write biblical perspectives and principles in relation to the user content"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/perspective', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def interpret_old_testament_verse(request:str) -> str:
    """Interpret the user-given bible verse from the Old Testament in the light of its context, together with insights of biblical Hebrew studies; an old testament bible verse / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/ot_meaning', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def expound_bible_topic(request:str) -> str:
    """Expound the user-given topic in reference to the Bible; a topic must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/topic', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_theology(request:str) -> str:
    """write the theological messages conveyed in the user-given content, in reference to the Bible"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/theology', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def study_bible_themes(request:str) -> str:
    """Study Bible Themes in relation to the user content"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/themes', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_canonical_context(request:str) -> str:
    """Write about canonical context of a bible book / chapter / passage; bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/canon', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_related_summary(request:str) -> str:
    """Write a summary on the user-given content in reference to the Bible"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/summary', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def interpret_new_testament_verse(request:str) -> str:
    """Interpret the user-given bible verse from the New Testament in the light of its context, together with insights of biblical Greek studies; a new testament bible verse / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/nt_meaning', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_new_testament_highlights(request:str) -> str:
    """Write Highlights in a New Testament passage in the bible; new testament bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/nt_highlights', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_applications(request:str) -> str:
    """Provide detailed applications of a bible passages; bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/application', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_book_introduction(request:str) -> str:
    """Write a detailed introduction on a book in the bible; bible book must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/introduce_book', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_old_testament_historical_context(request:str) -> str:
    """write the Bible Historical Context of a Old Testament passage in the bible; old testament bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/ot_context', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_outline(request:str) -> str:
    """provide a detailed outline of a bible book / chapter / passage; bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/outline', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_insights(request:str) -> str:
    """Write exegetical insights in detail on a bible passage; bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/insights', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def write_bible_sermon(request:str) -> str:
    """Write a bible sermon based on a bible passage; bible book / chapter / passage / reference(s) must be given"""
    global agentmake, getResponse
    messages = agentmake(request, **{'instruction': 'bible/sermon', 'system': 'auto'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.prompt
def simple_bible_study(request:str) -> PromptMessage:
    """Perform a simple bible study task"""
    global PromptMessage, TextContent
    prompt_text = f"""You are a bible study agent. You check the user request, under the `User Request` section, and resolve it with the following steps in order:
1. Call tool 'retrieve_english_bible_verses' for Bible text, 
2. Call tool 'retrieve_bible_cross_references' for Bible cross-references, 
3. Call tool 'study_old_testament_themes' for study old testament themes or 'study_new_testament_themes' for study old testament themes, and 
4. Call tool 'write_bible_theology' to explain its theology.

# User Request

---
{request}
---
"""
    return PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))

@mcp.prompt
def bible_devotion(request:str) -> PromptMessage:
    """Write bible devotion based on user content"""
    global PromptMessage, TextContent
    prompt_text = f"""
You are a bible devotional agent. You check the user content, under the `User Content` section, and write a devotional about it with the following steps in order:

1. Analyze the themes using @study_new_testament_themes for new testament passages or @study_old_testament_themes for old testament passages.
2. Identify and explain key biblical keywords from the passage using @identify_bible_keywords.
3. Write insights for the devotion using @write_bible_insights.
4. Relate the passage to daily life using @write_bible_applications.
5. Compose a touching devotion using @write_bible_devotion.
Ensure each step is clearly addressed and the final output is cohesive and inspiring.

# User Content

---
{request}
---
"""
    return PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))

mcp.run(show_banner=False)