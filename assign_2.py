# app.py
"""
Multi-Agent Travel Planner

Highlights:
- Clear separation of concerns (tools, agents, orchestration, UI)
- Simple global logger to display tool calls live in the sidebar
- Planner → Reviewer pipeline enforced before rendering any answer
- Minimal dependencies and straightforward control flow
"""

from __future__ import annotations

import os
import asyncio
import time
from typing import Callable, Dict, List, Optional, Any

import streamlit as st
from dotenv import load_dotenv
from tavily import TavilyClient

# ──────────────────────────────────────────────────────────────────────────────
# Environment & Globals
# ──────────────────────────────────────────────────────────────────────────────

load_dotenv()  # Loads variables from a local .env if present
os.environ.setdefault("OPENAI_LOG", "error")
os.environ.setdefault("OPENAI_TRACING", "false")

# Tool call logger: the UI sets this per request. The tool checks it and logs.
# Using a simple global makes this easy to teach and reason about.
TOOL_LOGGER: Optional[Callable[[Dict[str, Any]], None]] = None


def set_tool_logger(logger: Optional[Callable[[Dict[str, Any]], None]]) -> None:
    """Install or remove the UI logger used by tools to report activity."""
    global TOOL_LOGGER
    TOOL_LOGGER = logger


def log_tool_event(event: Dict[str, Any]) -> None:
    """If a logger is installed, send the event to the UI."""
    if TOOL_LOGGER is not None:
        try:
            TOOL_LOGGER(event)
        except Exception:
            # Logging should never break the app or the tool itself
            pass


def redact_for_logs(value: Any) -> Any:
    """
    Make sure we don't leak secrets and keep logs small.
    This is deliberately simple for teaching.
    """
    if isinstance(value, str):
        low = value.lower()
        if any(k in low for k in ("api_key", "token", "secret", "password")):
            return "[redacted]"
        return value if len(value) <= 300 else value[:120] + "… [truncated]"
    if isinstance(value, dict):
        return {k: ("[redacted]" if any(s in k.lower() for s in ("key", "token", "secret", "password"))
                    else redact_for_logs(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [redact_for_logs(v) for v in value]
    return value


# ──────────────────────────────────────────────────────────────────────────────
# Agent Framework Imports (provided by you)
# ──────────────────────────────────────────────────────────────────────────────
# These come from your own framework. We assume:
# - Agent: defines a model + instructions + optional tools
# - Runner.run(agent, input): executes an agent and returns an object with text
from agents import Agent, Runner, function_tool  # type: ignore


# ──────────────────────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────────────────────

@function_tool
def internet_search(query: str) -> str:
    """
    Internet search backed by Tavily.
    - Reads TAVILY_API_KEY from environment.
    - Sends simple log events before/after the call so the UI can show activity.
    """
    log_tool_event({"type": "call", "tool": "internet_search", "args": {"query": redact_for_logs(query)}})

    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            msg = "missing TAVILY_API_KEY in environment."
            log_tool_event({"type": "error", "tool": "internet_search", "error": msg})
            return f"Search error: {msg}"

        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=3)

        items = response.get("results", [])
        lines = [f"- {it.get('title', 'N/A')}: {it.get('content', 'N/A')}" for it in items]
        output = "\n".join(lines) if lines else "No results found."

        log_tool_event({
            "type": "result",
            "tool": "internet_search",
            "preview": redact_for_logs(output[:400] + ("…" if len(output) > 400 else "")),
        })
        return output

    except Exception as e:
        log_tool_event({"type": "error", "tool": "internet_search", "error": str(e)})
        return f"Search error: {e}"

    finally:
        log_tool_event({"type": "end", "tool": "internet_search"})


# ──────────────────────────────────────────────────────────────────────────────
# Agents
# ──────────────────────────────────────────────────────────────────────────────

# BEGIN SOLUTION
PLANNER_INSTRUCTIONS = """You are an expert Travel Planner Agent specializing in creating detailed, personalized itineraries.

Your role is to transform travel requests into comprehensive day-by-day travel plans.

When creating an itinerary, you must:

1. **Analyze the User Request**: Carefully extract key information including:
   - Travel duration and dates (if provided)
   - Budget constraints
   - Destination(s)
   - Traveler interests and preferences (history, food, adventure, culture, etc.)
   - Travel style (budget, mid-range, luxury)

2. **Generate a Structured Itinerary** that includes:
   - Clear day-by-day breakdown (Day 1, Day 2, etc.)
   - Morning, afternoon, and evening activities for each day
   - Specific locations, attractions, and restaurants with names
   - Approximate timing for each activity (e.g., "9:00 AM - 12:00 PM")
   - Estimated costs for major expenses (accommodation, meals, attractions, transport)
   - Travel logistics between cities/locations
   - Accommodation suggestions with approximate costs per night

3. **Consider Practical Constraints**:
   - Keep activities within the stated budget
   - Ensure reasonable pacing (don't over-schedule)
   - Group activities by geographic proximity when possible
   - Include meal times and dining suggestions
   - Account for travel time between locations
   - Balance popular attractions with authentic local experiences

4. **Format Requirements**:
   - Use clear markdown headers for each day (## Day 1, ## Day 2)
   - Present information in an organized, readable format
   - Include a budget breakdown at the end showing:
     * Accommodation total
     * Food total
     * Activities total
     * Transportation total
     * Estimated grand total
   - Provide helpful tips or notes where relevant

5. **Important Notes**:
   - You work from your existing knowledge (no internet access)
   - Be specific with names of places, attractions, and restaurants
   - If the request is vague, make reasonable assumptions but state them clearly
   - Prioritize user preferences in activity selection

Your output should be detailed enough that someone could follow it, but concise enough to be readable. Focus on creating a realistic, enjoyable travel experience within the given constraints."""

REVIEWER_INSTRUCTIONS = """You are a Travel Reviewer Agent responsible for validating and improving travel itineraries through real-time fact-checking.

Your role is to review the Planner's itinerary using internet searches and identify issues before it reaches the user.

**Your Process**:

1. **Thorough Review**: Analyze the itinerary for:
   - Factual accuracy (opening hours, ticket prices, seasonal closures)
   - Feasibility (travel times, distances, scheduling conflicts)
   - Budget accuracy (current prices, hidden costs)
   - Logical flow (geographic routing, activity sequencing)
   - Practical concerns (booking requirements, crowds, local events)

2. **Use Internet Search - MANDATORY**: You MUST use the internet_search tool to verify:
   - Current opening hours and days of operation for major attractions
   - Ticket prices and booking requirements
   - Travel times between locations (search for "travel time [A] to [B]")
   - Seasonal closures or special conditions
   - Restaurant/venue existence and current operational status
   - Any time-sensitive information

   Search for at least 5-7 key items per itinerary. Example searches:
   - "[attraction name] opening hours 2025"
   - "[attraction name] ticket price 2025"
   - "[restaurant name] [city]"
   - "travel time from [location A] to [location B]"

3. **Create a Delta List**: For each issue found, provide:
   - **Issue**: Specific problem identified
   - **Evidence**: What you found through your internet research
   - **Recommendation**: Concrete fix with specific details
   - **Priority**: High (makes itinerary impossible), Medium (significantly impacts experience), Low (minor improvement)

4. **Output Format**:
```
   ## Validation Summary
   [Brief overview of review findings - what was checked, overall assessment]

   ## Delta List (Changes Needed)
   
   ### 🔴 High Priority Issues
   1. **[Issue Title]**
      - **Problem**: [Specific description]
      - **Evidence**: [What you found via internet_search]
      - **Fix**: [Specific, actionable recommendation]
   
   ### 🟡 Medium Priority Issues
   [Same format as above]
   
   ### 🔵 Low Priority Issues / Suggestions
   [Same format as above]

   ## Budget Verification
   [Check if costs are realistic based on your research]
   - Accommodation: [Assessment]
   - Activities: [Assessment]
   - Food: [Assessment]
   - Transportation: [Assessment]

   ## Overall Assessment
   **Feasibility Score**: [X/10]
   **Confidence Level**: [High/Medium/Low]
   **Ready for Traveler**: [Yes with minor tweaks / Needs revisions / Major issues found]
   
   [Brief summary of whether the itinerary is ready to use]
```

5. **Search Strategy Tips**:
   - Be specific in your searches
   - Verify the most critical elements first (venues that might be closed)
   - Check for recent news or events that might affect the plan
   - Look for current pricing information
   - Verify transportation feasibility

**Important Formatting Rules**:
- **NEVER use the dollar sign symbol ($)** as it causes formatting issues in the display
- When writing US currency, use formats like "10 USD" or "10 US dollars" instead of "$10"
- Write "approximately 10 USD" not "~$10"
- For price ranges, write "from 10 USD to 20 USD" not "$10-$20"
- Use ¥ for yen, € for euros, £ for pounds (these symbols are safe to use)
- Example CORRECT: "Tendon bowl ranges from 1,490 yen (approximately 10 USD) to 2,700 yen (approximately 18 USD)"
- Example WRONG: "Tendon bowl ranges from ¥1,490 (~$10) to ¥2,700 ($18)"

**Important Guidelines**:
- Be thorough but constructive in your feedback
- Provide specific, actionable recommendations with exact details
- If something is verified as correct, acknowledge it in the Validation Summary
- Focus on factual corrections, not subjective preferences
- Prioritize issues that would actually break or significantly impact the itinerary
- Always cite your sources from internet searches

Your goal is to ensure the traveler receives an accurate, feasible, and enjoyable itinerary that won't have nasty surprises."""

reviewer_agent = Agent(
    name="Reviewer Agent",
    model="openai.gpt-4o",
    instructions=REVIEWER_INSTRUCTIONS.strip(),
    tools=[internet_search]  # CRITICAL: Add the internet_search tool here
)

planner_agent = Agent(
    name="Planner Agent",
    model="openai.gpt-4o",
    instructions=PLANNER_INSTRUCTIONS.strip(),
)

# END SOLUTION


# ──────────────────────────────────────────────────────────────────────────────
# Orchestration Helpers
# ──────────────────────────────────────────────────────────────────────────────

def extract_text(result_obj: Any) -> str:
    """
    Pull a usable string from the Runner result in a tolerant way.
    Your Runner may expose final_output, text, or __str__.
    """
    return (
        getattr(result_obj, "final_output", None)
        or getattr(result_obj, "text", None)
        or str(result_obj)
    )


def run_planner(user_text: str) -> str:
    """Run the Planner and return its itinerary text."""
    result = asyncio.run(Runner.run(planner_agent, user_text))
    return extract_text(result)


def run_reviewer(plan_text: str) -> str:
    """Run the Reviewer on the planner’s output and return validated text."""
    result = asyncio.run(Runner.run(reviewer_agent, plan_text))
    return extract_text(result)


# ──────────────────────────────────────────────────────────────────────────────
# Streamlit UI
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Travel Planner", page_icon="✈️")

st.title("✈️ Multi-Agent Travel Planner")
st.caption("Planner → Reviewer (with live tool calls in the sidebar)")

# Sidebar: session controls + examples + dev panel
with st.sidebar:
    st.header("Session")
    if st.button("🔄 Reset conversation"):
        st.session_state.clear()
        st.rerun()

    st.subheader("Try these prompts")
    st.code("Plan a week-long Europe trip for a student on a $1,500 budget who loves history and food")
    st.code("3-day Paris trip for art lovers with $800 budget")

    st.subheader("Developer view")
    show_tools = st.toggle("Show tool activity (live)", value=True)
    if show_tools:
        tool_expander = st.expander("🔧 Tool activity", expanded=True)
        tool_panel = tool_expander.container()
    else:
        tool_panel = st.container()  # inert sink

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []  # list[dict(role, content)]
if "meta" not in st.session_state:
    st.session_state.meta = []      # list[dict(trace)]

# Render history
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and i < len(st.session_state.meta):
            meta = st.session_state.meta[i]
            if meta:
                st.caption(meta.get("trace", ""))

# Chat input
user_input = st.chat_input("Describe your travel (destination, duration, budget, interests)…")

if user_input:
    # Add user message to history and render it
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.meta.append(None)
    with st.chat_message("user"):
        st.markdown(user_input)

    # Assistant output block
    with st.chat_message("assistant"):
        # Live “working…” text and progress bar
        live_msg = st.empty()
        progress = st.progress(0)

        # Per-request tool log (shown in the sidebar)
        tool_events: List[Dict[str, Any]] = []

        def ui_tool_logger(event: Dict[str, Any]) -> None:
            """Append an event and re-render the sidebar log."""
            tool_events.append(event)
            with tool_panel:
                st.markdown("**Recent tool calls**")
                for ev in tool_events[-60:]:  # last N entries
                    t = ev.get("tool", "unknown")
                    et = ev.get("type", "event")
                    if et == "call":
                        st.write(f"• **{t}** called with `{ev.get('args')}`")
                    elif et == "result":
                        st.write(f"• **{t}** result preview:\n\n> {ev.get('preview')}")
                    elif et == "error":
                        st.error(f"• **{t}** error: {ev.get('error')}")
                    elif et == "end":
                        st.write(f"• **{t}** finished")

        # Install the logger so tools can report to the sidebar
        set_tool_logger(ui_tool_logger)

        try:
            # Optional: clear sidebar panel on each run
            with tool_panel:
                st.empty()

            # Step 1: Planner
            with st.status("🧭 Planner Agent: generating itinerary…", expanded=True) as status:
                live_msg.markdown("🧭 Planner Agent is creating your itinerary…")
                plan_text = run_planner(user_input)
                progress.progress(40)
                status.update(label="🔎 Reviewer Agent: validating with live searches…", state="running")

            # Step 2: Reviewer (tool calls will appear live in sidebar)
            live_msg.markdown("🔎 Reviewer Agent is validating the plan with live searches…")
            review_text = run_reviewer(plan_text)
            progress.progress(90)

            # Completed
            live_msg.markdown("✅ Validation complete. Rendering results…")
            time.sleep(0.2)
            progress.progress(100)

            # Final render: show only the validated result, with the raw plan expandable
            st.info("🤖 **Reviewer Agent** (validated)")
            st.markdown(review_text)
            with st.expander("See raw plan from Planner Agent"):
                st.markdown(plan_text)

            # Save only the validated result to history
            st.session_state.messages.append({"role": "assistant", "content": review_text})
            st.session_state.meta.append({"trace": "Planner Agent → Reviewer Agent"})
            st.caption("Planner Agent → Reviewer Agent")

        except Exception as e:
            # Friendly error box
            live_msg.markdown("❌ Something went wrong.")
            err = f"⚠️ Error while processing your request:\n\n```\n{e}\n```"
            st.markdown(err)
            st.session_state.messages.append({"role": "assistant", "content": err})
            st.session_state.meta.append({"trace": "Runtime error."})

        finally:
            # Always remove the logger so it doesn't leak into the next request
            set_tool_logger(None)