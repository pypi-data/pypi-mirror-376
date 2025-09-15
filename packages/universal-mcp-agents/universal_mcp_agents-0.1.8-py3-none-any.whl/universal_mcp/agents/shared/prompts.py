TASK_DECOMPOSITION_PROMPT = """
You are an expert planner. Your goal is to consolidate a complex user request into the minimum number of high-level sub-tasks required. Each sub-task should correspond to a major, consolidated action within a single target application.

**CORE PRINCIPLES:**
1.  **App-Centric Grouping:** Group all related actions for a single application into ONE sub-task.
2.  **Focus on Data Handoffs:** A good decomposition often involves one sub-task to *retrieve* information and a subsequent sub-task to *use* that information.
3.  **Assume Internal Capabilities:** Do NOT create sub-tasks for abstract cognitive work like 'summarize' or 'analyze'.
4.  **Simplify Single Actions:** If the user's task is already a single, simple action, the output should be a single sub-task that concisely describes that action. Do not make it identical to the user's input.

**--- EXAMPLES ---**

**EXAMPLE 1:**
- **User Task:** "Create a Google Doc summarizing the last 5 merged pull requests in my GitHub repo universal-mcp/universal-mcp."
- **CORRECT DECOMPOSITION:**
    - "Fetch the last 5 merged pull requests from the GitHub repository 'universal-mcp/universal-mcp'."
    - "Create a new Google Doc containing the summary of the pull requests."

**EXAMPLE 2:**
- **User Task:** "Find the best restaurants in Goa using perplexity web search."
- **CORRECT DECOMPOSITION:**
    - "Perform a web search using Perplexity to find the best restaurants in Goa."

**--- YOUR TASK ---**

**USER TASK:**
"{task}"

**YOUR DECOMPOSITION (as a list of strings):**
"""


APP_SEARCH_QUERY_PROMPT = """
You are an expert at extracting the name of an application or a category of application from a sub-task description. Your goal is to generate a query for an app search engine.

**INSTRUCTIONS:**
1.  Read the sub-task carefully.
2.  If an application is explicitly named (e.g., "Perplexity", "Gmail", "GitHub"), your query should be ONLY that name.
3.  If no specific application is named, generate a query for the *category* of application (e.g., "web search", "email client", "document editor").
4.  The query should be concise.

**EXAMPLES:**
- **Sub-task:** "Perform a web search using Perplexity to find the best restaurants in Goa."
- **Query:** "Perplexity"

- **Sub-task:** "Fetch all marketing emails received from Gmail in the last 7 days."
- **Query:** "Gmail"

- **Sub-task:** "Find the latest news about artificial intelligence."
- **Query:** "web search"

**SUB-TASK:**
"{sub_task}"

**YOUR CONCISE APP SEARCH QUERY:**
"""


TOOL_SEARCH_QUERY_PROMPT = """
You are an expert at summarizing the core *action* of a sub-task into a concise query for finding a tool. This query should ignore any application names.

**INSTRUCTIONS:**
1.  Focus only on the verb or action being performed in the sub-task.
2.  Include key entities related to the action.
3.  Do NOT include the names of applications (e.g., "Perplexity", "Gmail").

**EXAMPLES:**
- **Sub-task:** "Perform a web search using Perplexity to find the best restaurants in Goa."
- **Query:** "web search for restaurants"

- **Sub-task:** "Fetch all marketing emails received from Gmail in the last 7 days."
- **Query:** "get emails by date"

- **Sub-task:** "Create a new Google Doc and append a summary."
- **Query:** "create document, append text"

**SUB-TASK:**
"{sub_task}"

**YOUR CONCISE TOOL SEARCH QUERY:**
"""

REVISE_DECOMPOSITION_PROMPT = """
You are an expert planner who revises plans that have failed. Your previous attempt to break down a task resulted in a sub-task that could not be matched with any available tools.

**INSTRUCTIONS:**
1.  Analyze the original user task and the failed sub-task.
2.  Generate a NEW, alternative decomposition of the original task.
3.  This new plan should try to achieve the same overall goal but with different, perhaps broader or more combined, sub-tasks to increase the chance of finding a suitable tool.

**ORIGINAL USER TASK:**
"{task}"

**FAILED SUB-TASK FROM PREVIOUS PLAN:**
"{failed_sub_task}"

**YOUR NEW, REVISED DECOMPOSITION (as a list of strings):**
"""


TOOL_SELECTION_PROMPT = """
You are an AI assistant that selects the most appropriate tool(s) from a list to accomplish a specific sub-task.

**INSTRUCTIONS:**
1.  Carefully review the sub-task to understand the required action.
2.  Examine the list of available tools and their descriptions.
3.  Select the best tool ID that matches the sub-task. You are encouraged to select multiple tools if there are multiple tools with similar capabilties 
or names. It is always good to have more tools than having insufficent tools.
4.  If no tool is a good fit, return an empty list.
5.  Only return the tool IDs.

**SUB-TASK:**
"{sub_task}"

**AVAILABLE TOOLS:**
{tool_candidates}

**YOUR SELECTED TOOL ID(s):**
"""