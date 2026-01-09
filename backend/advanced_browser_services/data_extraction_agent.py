"""
Data Extraction Agent Service

Specialized agent for extracting structured data from web pages.
Supports various output formats and data validation.
"""

import json
from typing import Optional, Dict, Any, List, Type
from pydantic import BaseModel
from browser_use import Agent, Tools
from browser_use.agent.views import AgentHistoryList

from .base_service import BaseAgentService, BrowserConfig, DEFAULT_MODEL


class DataExtractionAgent(BaseAgentService):
    """
    Agent specialized for extracting structured data from websites.

    Use cases:
    - Scrape product information from e-commerce sites
    - Extract contact details from directories
    - Gather research data from multiple sources
    - Monitor prices and availability
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,  # Lower temperature for consistent extraction
        browser_config: Optional[BrowserConfig] = None,
    ):
        """
        Initialize the data extraction agent.

        Args:
            model: Gemini model to use
            temperature: LLM temperature (lower for more consistent extraction)
            browser_config: Browser configuration options
        """
        super().__init__(model, temperature, browser_config)
        self.tools = Tools()
        self._extracted_data: List[Dict[str, Any]] = []
        self._setup_extraction_tools()

    def _setup_extraction_tools(self):
        """Set up tools for data extraction."""

        class ExtractedItem(BaseModel):
            # Use JSON string instead of Dict to avoid Gemini schema issues
            data_json: str  # JSON string containing the extracted data

        @self.tools.action(
            "Store extracted data item as JSON string for later retrieval",
            param_model=ExtractedItem
        )
        def store_extracted_item(params: ExtractedItem) -> str:
            try:
                data = json.loads(params.data_json)
                self._extracted_data.append(data)
            except json.JSONDecodeError:
                # If not valid JSON, store as raw string
                self._extracted_data.append({"raw": params.data_json})
            return f"Stored item #{len(self._extracted_data)}"

        class ExtractionComplete(BaseModel):
            total_items: int
            notes: str = ""

        @self.tools.action(
            "Signal that data extraction is complete",
            param_model=ExtractionComplete
        )
        def extraction_complete(params: ExtractionComplete) -> str:
            return f"Extraction complete. Total items: {params.total_items}. Notes: {params.notes}"

    async def extract(
        self,
        url: str,
        data_schema: Dict[str, str],
        max_items: Optional[int] = None,
        max_steps: int = 40,
    ) -> Dict[str, Any]:
        """
        Extract structured data from a URL.

        Args:
            url: The URL to extract data from
            data_schema: Dictionary describing the data to extract
                        e.g., {"name": "Product name", "price": "Product price in USD"}
            max_items: Maximum number of items to extract (None for all)
            max_steps: Maximum agent steps

        Returns:
            Dictionary containing extracted data and metadata
        """
        self._extracted_data = []
        browser = await self._ensure_browser()

        schema_desc = "\n".join([f"- {k}: {v}" for k, v in data_schema.items()])
        item_limit = f"Extract at most {max_items} items." if max_items else "Extract all available items."

        task = f"""
        Navigate to: {url}

        Extract data from this page with the following structure:
        {schema_desc}

        {item_limit}

        For each item found:
        1. Extract all the specified fields
        2. Use the 'store_extracted_item' tool to save each item
        3. When done, use 'extraction_complete' to signal completion

        Be thorough and accurate in your extraction.
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
                "url": url,
                "items_extracted": len(self._extracted_data),
                "data": self._extracted_data,
                "steps": steps,
                "summary": history.final_result() or "Extraction completed",
            }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "items_extracted": len(self._extracted_data),
                "data": self._extracted_data,
                "error": str(e),
            }
        finally:
            await self.close()

    async def extract_to_file(
        self,
        url: str,
        data_schema: Dict[str, str],
        output_file: str,
        max_items: Optional[int] = None,
        max_steps: int = 40,
    ) -> Dict[str, Any]:
        """
        Extract data and save to a JSON file.

        Args:
            url: The URL to extract data from
            data_schema: Data structure to extract
            output_file: Path to save the JSON output
            max_items: Maximum items to extract
            max_steps: Maximum agent steps

        Returns:
            Extraction results with file path
        """
        result = await self.extract(url, data_schema, max_items, max_steps)

        if result["success"] and result["data"]:
            with open(output_file, "w") as f:
                json.dump(result["data"], f, indent=2)
            result["output_file"] = output_file

        return result

    async def extract_from_multiple_urls(
        self,
        urls: List[str],
        data_schema: Dict[str, str],
        max_items_per_url: Optional[int] = None,
        max_steps_per_url: int = 30,
    ) -> Dict[str, Any]:
        """
        Extract data from multiple URLs sequentially.

        Args:
            urls: List of URLs to extract from
            data_schema: Data structure to extract
            max_items_per_url: Maximum items per URL
            max_steps_per_url: Maximum steps per URL

        Returns:
            Combined extraction results
        """
        all_results = []
        all_data = []

        for url in urls:
            result = await self.extract(
                url=url,
                data_schema=data_schema,
                max_items=max_items_per_url,
                max_steps=max_steps_per_url,
            )
            all_results.append(result)
            if result["success"]:
                all_data.extend(result["data"])

        return {
            "total_urls": len(urls),
            "successful_extractions": sum(1 for r in all_results if r["success"]),
            "total_items": len(all_data),
            "data": all_data,
            "per_url_results": all_results,
        }
