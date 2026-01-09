import os
import asyncio
from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatGoogle

# Load environment variables
load_dotenv()

async def run_ui_automator(instruction: str):
    # Initialize LLM using ChatGoogle from browser-use package
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    # ChatGoogle is specifically for Gemini models within browser-use
    llm = ChatGoogle(
        model='gemini-2.0-flash',
    )

    # Initialize Browser
    browser = Browser()

    # Initialize Agent
    agent = Agent(
        task=instruction,
        llm=llm,
        browser=browser,
    )

    try:
        # Run the agent
        history = await agent.run()
        
        # Extract steps and summary
        steps = []
        for step in history.history:
            # Each step contains a thought and an action
            action_desc = "Processing..."
            if step.model_output and step.model_output.action:
                # model_output.action is often a list of actions
                action_names = [type(a).__name__ for a in step.model_output.action]
                action_desc = ", ".join(action_names)
            
            steps.append({
                "action": action_desc,
                "status": "done"
            })
        
        # Get the final result summary from the agent history
        final_result = history.final_result() or "Task completed successfully."
        
        return {
            "steps": steps,
            "summary": final_result
        }
    finally:
        await browser.close()

if __name__ == "__main__":
    # Test script
    async def test():
        result = await run_ui_automator("Search for the latest SpaceX launch on Google and tell me the date.")
        print(result)
    
    asyncio.run(test())
