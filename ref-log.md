# Assignment 2 Reflection
#

## What I Learned from Multi-Agent Workflow

This assignment taught me the importance of separating concerns when it comes to AI systems. By splitting the tasks between a planner agent and fact checking agent, I was able to have my outputs be more reliable and credible than using just a single agent could produce. I had the planner agent focus on the creativity and details and the fact checking agent help to verify through internet searches.

I also learned that this sort of work required careful prompt engineering; each agent needed clear specific instructions for their respective roles: the planner didn’t use the internet while the fact checker had to use the internet. In addition for the fact checking agent to know what it needed to verify, I needed to have the planning agent output its content in a detailed, structured, and systematic manner.

It was an interesting assignment to see in real time how I was able to incorporate real-time data lookup of a knowledge base and turn it into a research assistant. With the fact checking agent, the internet searches were able to convert my vague itineraries into an actual plan with factually correct information such as when the venues closed, prices, etc.

And then lastly, I discovered that certain characters like currencies triggered special rendering issues that made the output of my results look visually awkward during the agent’s output.

## Challenges and Solutions

**Challenge 1: Prompt Design for Tool Usage**
Initially I had issues with my fact checking agent/reviewer not utilizing the internet_search tool. I solved this by giving clear explicit instructions with the words of “MANDATORY” and “MUST” and examples of search queries to run. Lastly, I prompted it to have a minimum amount of searches to run for thoroughness.

**Challenge 2: Structured Output from Reviewer**
The Reviewer's feedback was initially too vague ("this might not work"). I restructured the prompt to require a "Delta List" format with specific fields: Issue, Evidence, Fix, and Priority. This forced the agent to be concrete and actionable.

**Challenge 3: LaTeX/Markdown Rendering Issues**
I encountered a significant formatting problem where dollar signs ($) in the Reviewer's output were being interpreted as LaTeX math expressions by Streamlit's markdown renderer. This caused:
- Inconsistent fonts (switching to math font mid-sentence)
- Weird spacing issues
- Text like "$10" rendering oddly as mathematical notation

I solved this through a two-pronged approach:
1. **Agent-level prevention**: Added explicit formatting rules to the REVIEWER_INSTRUCTIONS telling the agent to NEVER use the $ symbol and instead write "10 USD" or "10 US dollars"
2. **Code-level safety net**: Implemented a `escape_dollar_signs()` function using regex to catch and escape any dollar signs that might slip through: `re.sub(r'\$(\d)', r'\\\$\1', text)`

This taught me that when working with LLM outputs in specific UI frameworks, you need to consider both prompt engineering AND post-processing to handle edge cases.

**Challenge 4: Output Format Consistency**
Getting the Planner to consistently format itineraries with times, costs, and locations required very explicit instructions about structure. I added a sample format in the prompt showing exactly what each day should look like.

**Challenge 5: Debugging Tool Calls**
The sidebar tool logging was invaluable for debugging. I could see exactly when and what the Reviewer was searching for, which helped me refine prompts to encourage better search strategies.

## Creative Design Choices

I adopted a **validation-focused** rather than rewriting approach for the Reviewer. Instead of having the Reviewer rewrite the entire itinerary, it produces a Delta List of specific changes. This preserves the Planner's creative choices while ensuring factual accuracy.

I added **priority levels** (High/Medium/Low) using emoji indicators (🔴🟡🔵) to the Delta List so users can quickly identify critical issues versus nice-to-have improvements. High priority means the itinerary is broken, Medium means significant impact, Low means minor enhancement.

I included a **Budget Verification** section because budget constraints appeared in most test queries, and cost overruns would significantly impact user satisfaction. This section breaks down accuracy by category (accommodation, activities, food, transportation).

The **persona design** was important—the Planner is an "expert travel planner" focused on creativity and detail, while the Reviewer is a "validation specialist" focused on facts and evidence. This separation helped each agent stay in their lane.

I added **formatting guidelines** directly in the agent instructions after discovering the dollar sign rendering issue. This proactive approach prevents display problems before they occur, rather than only relying on post-processing fixes.

## External Tools and GenAI Assistance

- **GitHub Copilot**: Used extensively for:
 - Understanding the assignment structure and requirements
 - Learning best practices for multi-agent prompting and prompt engineering
 - Debugging agent coordination patterns and workflow issues
 - Troubleshooting the LaTeX/markdown rendering issue with dollar signs
 - Understanding how to structure prompts for consistent tool usage
 - Creating effective Delta List formats for structured feedback
 - Implementing regex-based post-processing solutions
 - Generating boilerplate code and suggesting improvements
 - **GitHub/Git Documentation**: For understanding branch management, forking workflows, and syncing upstream repositories.
 - Helped to write my ref-log.md

- **Streamlit Documentation**: For understanding the UI framework, markdown rendering behavior, and how the sidebar logging system worked.

- **Regular Expressions (regex) documentation**: Used to implement the dollar sign escape function for post-processing agent outputs.

The assignment template provided excellent scaffolding with the tool logging infrastructure and agent runner, which made it easy to focus on the core challenge of prompt engineering for multi-agent coordination. The real-time tool call visualization in the sidebar was particularly helpful for debugging and understanding agent behavior.

