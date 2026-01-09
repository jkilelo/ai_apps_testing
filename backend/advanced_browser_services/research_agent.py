"""
Research Agent Service

Agent specialized for conducting web research, gathering information,
and synthesizing findings from multiple sources.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from browser_use import Agent, Tools
from browser_use.agent.views import AgentHistoryList

from .base_service import BaseAgentService, BrowserConfig, DEFAULT_MODEL


class ResearchAgent(BaseAgentService):
    """
    Agent specialized for web research and information gathering.

    Use cases:
    - Market research
    - Competitor analysis
    - Topic deep-dives
    - Fact-checking
    - News monitoring
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.5,
        browser_config: Optional[BrowserConfig] = None,
    ):
        """
        Initialize the research agent.

        Args:
            model: Gemini model to use
            temperature: LLM temperature setting
            browser_config: Browser configuration options
        """
        super().__init__(model, temperature, browser_config)
        self.tools = Tools()
        self._research_notes: List[Dict[str, Any]] = []
        self._sources: List[str] = []
        self._setup_research_tools()

    def _setup_research_tools(self):
        """Set up research-specific tools."""

        class ResearchNote(BaseModel):
            topic: str
            finding: str
            source_url: str
            confidence: str = "medium"  # low, medium, high

        @self.tools.action(
            "Record a research finding with source",
            param_model=ResearchNote
        )
        def add_research_note(params: ResearchNote) -> str:
            self._research_notes.append({
                "topic": params.topic,
                "finding": params.finding,
                "source": params.source_url,
                "confidence": params.confidence,
            })
            if params.source_url not in self._sources:
                self._sources.append(params.source_url)
            return f"Noted: {params.finding[:50]}..."

        class ResearchSummary(BaseModel):
            main_findings: str
            key_insights: List[str]
            areas_needing_more_research: List[str] = []

        @self.tools.action(
            "Summarize research findings",
            param_model=ResearchSummary
        )
        def summarize_research(params: ResearchSummary) -> str:
            return f"Summary recorded with {len(params.key_insights)} key insights"

    async def research_topic(
        self,
        topic: str,
        depth: str = "moderate",  # shallow, moderate, deep
        max_sources: int = 5,
        max_steps: int = 50,
    ) -> Dict[str, Any]:
        """
        Research a topic and gather information.

        Args:
            topic: The topic to research
            depth: Research depth (shallow, moderate, deep)
            max_sources: Maximum number of sources to consult
            max_steps: Maximum agent steps

        Returns:
            Research results with findings and sources
        """
        self._research_notes = []
        self._sources = []
        browser = await self._ensure_browser()

        depth_instructions = {
            "shallow": "Focus on key facts and main points. Quick overview.",
            "moderate": "Gather comprehensive information. Include details and examples.",
            "deep": "Conduct thorough research. Explore multiple perspectives, find statistics, and verify information across sources.",
        }

        task = f"""
        Research Topic: {topic}

        Research Depth: {depth}
        {depth_instructions.get(depth, depth_instructions["moderate"])}

        Instructions:
        1. Search for information about the topic
        2. Visit up to {max_sources} different sources
        3. For each useful finding, use 'add_research_note' to record it
        4. Include the source URL and your confidence level
        5. After gathering information, use 'summarize_research' to provide a summary

        Be thorough and critical of sources. Prefer authoritative sources.
        """

        agent = Agent(
            task=task,
            llm=self.llm,
            browser=browser,
            tools=self.tools,
        )

        try:
            history: AgentHistoryList = await agent.run(max_steps=max_steps)

            steps = []
            for step in history.history:
                action_desc = "Processing..."
                if step.model_output and step.model_output.action:
                    action_names = [type(a).__name__ for a in step.model_output.action]
                    action_desc = ", ".join(action_names)
                steps.append({"action": action_desc, "status": "done"})

            return {
                "success": True,
                "topic": topic,
                "depth": depth,
                "findings": self._research_notes,
                "sources": self._sources,
                "num_findings": len(self._research_notes),
                "num_sources": len(self._sources),
                "steps": steps,
                "summary": history.final_result() or "Research completed",
            }
        except Exception as e:
            return {
                "success": False,
                "topic": topic,
                "findings": self._research_notes,
                "sources": self._sources,
                "error": str(e),
            }
        finally:
            await self.close()

    async def compare_products(
        self,
        products: List[str],
        comparison_aspects: List[str],
        max_steps: int = 60,
    ) -> Dict[str, Any]:
        """
        Compare multiple products based on specified aspects.

        Args:
            products: List of product names to compare
            comparison_aspects: Aspects to compare (price, features, reviews, etc.)
            max_steps: Maximum agent steps

        Returns:
            Product comparison results
        """
        self._research_notes = []
        self._sources = []
        browser = await self._ensure_browser()

        aspects_list = ", ".join(comparison_aspects)
        products_list = "\n".join(f"- {p}" for p in products)

        task = f"""
        Compare the following products:
        {products_list}

        Comparison aspects: {aspects_list}

        Instructions:
        1. Search for each product
        2. Gather information about each aspect for every product
        3. Use 'add_research_note' for each piece of information found
        4. Include the product name in the topic field
        5. After gathering all information, use 'summarize_research' to provide a comparison summary

        Be objective and use reliable sources like official product pages and trusted review sites.
        """

        agent = Agent(
            task=task,
            llm=self.llm,
            browser=browser,
            tools=self.tools,
        )

        try:
            history: AgentHistoryList = await agent.run(max_steps=max_steps)

            steps = []
            for step in history.history:
                action_desc = "Processing..."
                if step.model_output and step.model_output.action:
                    action_names = [type(a).__name__ for a in step.model_output.action]
                    action_desc = ", ".join(action_names)
                steps.append({"action": action_desc, "status": "done"})

            # Organize findings by product
            by_product = {}
            for note in self._research_notes:
                topic = note["topic"]
                if topic not in by_product:
                    by_product[topic] = []
                by_product[topic].append(note)

            return {
                "success": True,
                "products": products,
                "aspects": comparison_aspects,
                "findings_by_product": by_product,
                "all_findings": self._research_notes,
                "sources": self._sources,
                "steps": steps,
                "summary": history.final_result() or "Comparison completed",
            }
        except Exception as e:
            return {
                "success": False,
                "products": products,
                "findings": self._research_notes,
                "error": str(e),
            }
        finally:
            await self.close()

    async def fact_check(
        self,
        claim: str,
        num_sources: int = 3,
        max_steps: int = 40,
    ) -> Dict[str, Any]:
        """
        Fact-check a claim using multiple sources.

        Args:
            claim: The claim to verify
            num_sources: Number of sources to consult
            max_steps: Maximum agent steps

        Returns:
            Fact-checking results with verdict
        """
        self._research_notes = []
        self._sources = []
        browser = await self._ensure_browser()

        task = f"""
        Fact Check this claim: "{claim}"

        Instructions:
        1. Search for information to verify or refute this claim
        2. Consult at least {num_sources} different sources
        3. For each piece of evidence, use 'add_research_note' with:
           - topic: "evidence_for" or "evidence_against"
           - finding: The specific evidence
           - confidence: Your confidence in this evidence
        4. Use 'summarize_research' to provide your verdict:
           - State whether the claim is TRUE, FALSE, PARTIALLY TRUE, or UNVERIFIED
           - List the key evidence supporting your verdict

        Use authoritative sources. Be objective and thorough.
        """

        agent = Agent(
            task=task,
            llm=self.llm,
            browser=browser,
            tools=self.tools,
        )

        try:
            history: AgentHistoryList = await agent.run(max_steps=max_steps)

            steps = []
            for step in history.history:
                action_desc = "Processing..."
                if step.model_output and step.model_output.action:
                    action_names = [type(a).__name__ for a in step.model_output.action]
                    action_desc = ", ".join(action_names)
                steps.append({"action": action_desc, "status": "done"})

            # Categorize evidence
            evidence_for = [n for n in self._research_notes if "for" in n.get("topic", "").lower()]
            evidence_against = [n for n in self._research_notes if "against" in n.get("topic", "").lower()]

            return {
                "success": True,
                "claim": claim,
                "evidence_for": evidence_for,
                "evidence_against": evidence_against,
                "sources": self._sources,
                "steps": steps,
                "verdict": history.final_result() or "Fact check completed",
            }
        except Exception as e:
            return {
                "success": False,
                "claim": claim,
                "error": str(e),
            }
        finally:
            await self.close()
