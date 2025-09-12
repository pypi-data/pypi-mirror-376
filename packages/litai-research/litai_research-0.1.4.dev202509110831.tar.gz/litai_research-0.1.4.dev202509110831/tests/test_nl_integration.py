"""Extended integration tests for natural language query handling with improved workflows.

This module provides comprehensive integration testing for the natural language handler,
focusing on multi-turn conversations, real user workflows, and context management flows.

Architecture Overview:
----------------------
1. **Mocking Strategy**:
   - SemanticScholarClient: Mocked to return predefined Paper objects, avoiding external API calls
     and ensuring deterministic test results. The mock returns context-appropriate papers based
     on query keywords (e.g., "transformer" returns transformer-related papers).
   - Console.input: Patched via mock_console_input fixture to simulate user interactions during
     approval loops and context management flows.
   - Command handlers: Wrapped with tracking decorators to monitor which tools are invoked
     during natural language processing.

2. **Test Infrastructure**:
   - ConversationTest: A stateful test harness that maintains conversation history and tracks
     tool invocations across multiple query-response turns. Enables verification of complete
     conversation flows and tool call sequences.
   - TrackedNLHandler: Wrapper around NaturalLanguageHandler that intercepts and records all
     tool invocations for assertion and debugging purposes.
   - Predefined test data: Consistent set of Paper objects with realistic metadata (citation
     counts, abstracts, tags) representing common literature review scenarios.

3. **Testing Approach**:
   - Integration-level testing with real command handlers (not mocked), ensuring actual
     business logic is exercised.
   - Tool approval disabled (approval_manager.enabled = False) for automated testing.
   - Database operations use real SQLite in-memory database via temp_dir fixture.
   - LLM calls use actual OpenAI API (gpt-5-nano model) when OPENAI_API_KEY is set.

4. **Test Coverage**:
   - Multi-turn conversation flows simulating real research workflows
   - Context management with user feedback loops
   - Paper discovery, collection management, and synthesis operations
   - Edge cases including cancellation flows and contextual references

Key Fixtures:
-------------
- predefined_search_papers: Returns list of Paper objects for mocking search results
- mock_console_input: Patches rich.console.Console.input for automated approval
- nl_handler_with_mocked_input: Fully configured NL handler with mocked dependencies
- sample_papers: Papers pre-loaded into database for testing existing collection queries

Technical Notes:
----------------
- Tests require OPENAI_API_KEY environment variable (skipped otherwise via pytestmark)
- Mock search function uses keyword matching to return contextually appropriate papers
- Tool tracking occurs at the command handler level, not the NL processing level
- Context management operations don't use standard tracked tools (by design)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from litai.config import Config
from litai.database import Database
from litai.models import Paper
from litai.nl_handler import NaturalLanguageHandler

#=======================================================================
# Setup
#=======================================================================

# Skip these tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config(temp_dir):
    """Create a real config with API key."""
    config = Config(base_dir=temp_dir)
    # Set to use gpt-5-nano model
    config.update_config("llm.provider", "openai")
    config.update_config("llm.model", "gpt-5-nano")
    return config


@pytest.fixture
def db(config):
    """Create a real database."""
    return Database(config)


@pytest.fixture
def predefined_search_papers():
    """Predefined papers to return from mocked SemanticScholar searches."""
    return [
        Paper(
            paper_id="attention2017",
            title="Attention Is All You Need",
            authors=["Vaswani", "Shazeer", "Parmar"],
            year=2017,
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
            citation_count=50000,
            tags=["transformers", "attention", "NLP"],
        ),
        Paper(
            paper_id="bert2018",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            authors=["Devlin", "Chang", "Lee", "Toutanova"],
            year=2018,
            abstract="We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
            citation_count=40000,
            tags=["BERT", "NLP", "pretraining"],
        ),
        Paper(
            paper_id="gpt3_2020",
            title="Language Models are Few-Shot Learners",
            authors=["Brown", "Mann", "Ryder", "Subbiah"],
            year=2020,
            abstract="Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task.",
            citation_count=10000,
            tags=["GPT", "few-shot", "language-models"],
        ),
        Paper(
            paper_id="gnn_survey_2021",
            title="Graph Neural Networks: A Review of Methods and Applications",
            authors=["Zhou", "Cui", "Hu", "Zhang"],
            year=2021,
            abstract="Graph neural networks (GNNs) are gaining increasing popularity in various domains. This survey provides a comprehensive overview of graph neural networks.",
            citation_count=5000,
            tags=["GNN", "survey", "graph-neural-networks"],
        ),
        Paper(
            paper_id="efficient_transformers_2020",
            title="Efficient Transformers: A Survey",
            authors=["Tay", "Dehghani", "Bahri", "Metzler"],
            year=2020,
            abstract="Transformers have a quadratic time and memory complexity with respect to sequence length. We survey recent efficiency-focused transformer models.",
            citation_count=3000,
            tags=["transformers", "efficiency", "survey"],
        ),
    ]


@pytest.fixture
def sample_papers(db):
    """Add sample papers to the database."""
    papers = [
        Paper(
            paper_id="attention2017",
            title="Attention Is All You Need",
            authors=["Vaswani", "Shazeer", "Parmar"],
            year=2017,
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
            citation_count=50000,
            tags=["transformers", "attention", "NLP"],
        ),
        Paper(
            paper_id="bert2018",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            authors=["Devlin", "Chang", "Lee", "Toutanova"],
            year=2018,
            abstract="We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
            citation_count=40000,
            tags=["BERT", "NLP", "pretraining"],
        ),
        Paper(
            paper_id="gpt3_2020",
            title="Language Models are Few-Shot Learners",
            authors=["Brown", "Mann", "Ryder", "Subbiah"],
            year=2020,
            abstract="Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task.",
            citation_count=10000,
            tags=["GPT", "few-shot", "language-models"],
        ),
    ]

    # Add papers to database
    for paper in papers:
        db.add_paper(paper)

    return papers


class TrackedNLHandler:
    """Wrapper for NaturalLanguageHandler that tracks tool calls."""

    def __init__(self, nl_handler, tool_calls):
        self.handler = nl_handler
        self.tool_calls = tool_calls

    async def handle_query(self, query: str) -> None:
        """Forward to the wrapped handler."""
        return await self.handler.handle_query(query)

    async def close(self) -> None:
        """Forward to the wrapped handler."""
        return await self.handler.close()


class ConversationTest:
    """Base class for multi-turn conversation testing."""
    
    def __init__(self, tracked_handler):
        """Initialize with a TrackedNLHandler instance."""
        self.handler = tracked_handler  # This is a TrackedNLHandler
        self.conversation_history = []
        self.tool_calls_per_turn = []
    
    async def send_query(self, query: str) -> None:
        """Send a query and track the response."""
        # Clear tool calls for this turn
        self.handler.tool_calls.clear()
        
        # Send query
        await self.handler.handle_query(query)
        
        # Record this turn
        self.conversation_history.append(query)
        self.tool_calls_per_turn.append(list(self.handler.tool_calls))
    
    def verify_tool_sequence(self, expected_tools: list[list[str]]) -> None:
        """Verify the sequence of tool calls across turns."""
        for turn_idx, (actual, expected) in enumerate(
            zip(self.tool_calls_per_turn, expected_tools, strict=False),
        ):
            assert set(actual) == set(expected), (
                f"Turn {turn_idx + 1}: Expected {expected}, got {actual}"
            )
    
    def verify_last_tools(self, expected_tools: list[str]) -> None:
        """Verify tools called in the last turn."""
        assert set(self.tool_calls_per_turn[-1]) == set(expected_tools)


@pytest.fixture
def mock_console_input():
    """Mock console.input for automated testing."""
    with patch('rich.console.Console.input') as mock:
        mock.return_value = ""  # Auto-accept by default
        yield mock


@pytest_asyncio.fixture
async def nl_handler_with_mocked_input(db, config, sample_papers, mock_console_input, predefined_search_papers):
    """NL handler with patched interactive components for automated testing."""
    # Import real command handlers
    from litai.cli import (
        add_paper,
        find_papers,
        handle_tag_command,
        list_papers,
        list_tags,
        remove_paper,
        show_search_results,
    )
    from litai.cli import (
        handle_note_tool as handle_note,
    )
    from litai.cli import (
        handle_user_prompt_tool as handle_user_prompt,
    )
    from litai.commands.context_commands import (
        handle_context_show,
    )
    from litai.commands.synthesize import handle_synthesize_command

    # Track which tools get called
    tool_calls = []
    
    # Create mock for SemanticScholarClient
    mock_ss_client = AsyncMock()
    mock_ss_client.__aenter__ = AsyncMock(return_value=mock_ss_client)
    mock_ss_client.__aexit__ = AsyncMock(return_value=None)
    
    # Configure the mock to return predefined papers based on query
    async def mock_search(query, limit=10):
        query_lower = query.lower()
        if "transformer" in query_lower:
            return predefined_search_papers[:3]  # Return transformer-related papers
        elif "graph neural" in query_lower or "gnn" in query_lower:
            return [predefined_search_papers[3]]  # Return GNN survey
        elif "survey" in query_lower:
            return predefined_search_papers[3:5]  # Return survey papers
        elif "memory efficiency" in query_lower or "efficient" in query_lower:
            return [predefined_search_papers[4], predefined_search_papers[0]]  # Efficient transformers
        else:
            # Default: return first few papers
            return predefined_search_papers[:min(limit, 3)]
    
    mock_ss_client.search = mock_search

    # Wrap real handlers to track calls - use patched version for find_papers
    async def tracked_find_papers(*args, **kwargs):
        tool_calls.append("find_papers")
        # Patch SemanticScholarClient during the call
        with patch('litai.cli.SemanticScholarClient', return_value=mock_ss_client):
            return await find_papers(*args, **kwargs)

    def tracked_add_paper(*args, **kwargs):
        tool_calls.append("add_paper")
        return add_paper(*args, **kwargs)

    def tracked_papers_command(*args, **kwargs):
        tool_calls.append("papers_command")
        return list_papers(*args, **kwargs)

    def tracked_manage_paper_tags(*args, **kwargs):
        tool_calls.append("manage_paper_tags")
        return handle_tag_command(*args, **kwargs)

    def tracked_list_tags(*args, **kwargs):
        tool_calls.append("list_tags")
        return list_tags(*args, **kwargs)

    def tracked_show_results(*args, **kwargs):
        tool_calls.append("show_search_results")
        return show_search_results(*args, **kwargs)

    async def tracked_synthesize(*args, **kwargs):
        tool_calls.append("synthesize")
        return await handle_synthesize_command(*args, **kwargs)

    def tracked_context_show(*args, **kwargs):
        tool_calls.append("context_show")
        return handle_context_show(*args, **kwargs)

    async def tracked_note(*args, **kwargs):
        tool_calls.append("note")
        return await handle_note(*args, **kwargs)

    async def tracked_prompt(*args, **kwargs):
        tool_calls.append("prompt")
        return await handle_user_prompt(*args, **kwargs)

    def tracked_remove_paper(*args, **kwargs):
        tool_calls.append("remove_paper")
        return remove_paper(*args, **kwargs)

    # Map command handlers using the same names as in nl_handler.py
    command_handlers = {
        "find_papers": tracked_find_papers,
        "add_paper": tracked_add_paper,
        "list_papers": tracked_papers_command,
        "handle_tag_command": tracked_manage_paper_tags,
        "list_tags": tracked_list_tags,
        "show_search_results": tracked_show_results,
        "remove_paper": tracked_remove_paper,
        "handle_synthesize": tracked_synthesize,
        "handle_context_show": tracked_context_show,
        "handle_note": tracked_note,
        "handle_user_prompt": tracked_prompt,
    }

    search_results = []
    from litai.context_manager import SessionContext

    session_context = SessionContext()
    nl_handler = NaturalLanguageHandler(
        db, command_handlers, search_results, config, session_context,
    )

    # Disable tool approval for automated testing
    nl_handler.approval_manager.enabled = False

    # Return a wrapper that includes both the handler and the tool_calls list
    tracked_handler = TrackedNLHandler(nl_handler, tool_calls)

    yield tracked_handler

    # Cleanup
    await nl_handler.close()


#=======================================================================
# Real workflow tests based on README examples
#=======================================================================

class TestRealWorkflows:
    """Test actual user workflows from documentation."""
    
    @pytest.mark.asyncio
    async def test_exploring_new_field_workflow(self, nl_handler_with_mocked_input, capsys):
        """Test the 'Exploring a new field' workflow from README."""
        conv = ConversationTest(nl_handler_with_mocked_input)
        
        # Step 1: Find papers
        await conv.send_query("Find recent papers on transformers")
        conv.verify_last_tools(["find_papers"])
        
        # Step 2: Add papers to collection 
        await conv.send_query("Add the first 2 papers to my collection")
        conv.verify_last_tools(["add_paper"])
        
        # Step 3: Add to context (needs input patching - already done via mock_console_input fixture)
        await conv.send_query("Add BERT and attention papers to context with abstracts")
        # Context management doesn't use standard tracked tools
        
        # Step 4: Synthesis question
        await conv.send_query("What are the main architectural innovations?")
        conv.verify_last_tools(["synthesize"])
        
        # Verify overall tool sequence
        expected_sequence = [
            ["find_papers"],
            ["add_paper"],
            [],  # Context management doesn't use standard tools
            ["synthesize"],
        ]
        conv.verify_tool_sequence(expected_sequence)
    
    # Only test that I've verified works
    @pytest.mark.asyncio
    async def test_debugging_implementation_workflow(self, nl_handler_with_mocked_input, capsys):
        """Test the 'Debugging your implementation' workflow from README."""
        conv = ConversationTest(nl_handler_with_mocked_input)
        
        # Full conversation flow
        await conv.send_query("Find papers about transformer memory efficiency")
        conv.verify_last_tools(["find_papers"])
        
        await conv.send_query("Add papers 1,2,3 to my collection")
        conv.verify_last_tools(["add_paper"])
        
        await conv.send_query("Add them to context with full text")
        # Context management doesn't use standard tools
        
        await conv.send_query("Use synthesize to compare and contrast how these papers handle the quadratic complexity problem")
        conv.verify_last_tools(["synthesize"])
        
        # Verify the complete tool sequence
        expected_sequence = [
            ["find_papers"],
            ["add_paper"],
            [],  # Context management doesn't use standard tools
            ["synthesize"],
        ]
        conv.verify_tool_sequence(expected_sequence)
    
    @pytest.mark.asyncio
    async def test_finding_research_gaps_workflow(self, nl_handler_with_mocked_input, capsys):
        """Test the 'Finding research gaps' workflow from README."""
        conv = ConversationTest(nl_handler_with_mocked_input)
        
        # Step 1: Search for survey papers
        await conv.send_query("Search for graph neural network survey papers")
        conv.verify_last_tools(["find_papers"])
        
        # Step 2: Save surveys
        await conv.send_query("Save all the recent surveys")
        conv.verify_last_tools(["add_paper"])
        
        # Step 3: Add to context
        await conv.send_query("Add top 3 surveys to context")
        # Context management doesn't use standard tools
        
        # Step 4: Gap analysis
        await conv.send_query("What problems do they identify as unsolved?")
        conv.verify_last_tools(["synthesize"])
        
        # Verify the complete tool sequence
        expected_sequence = [
            ["find_papers"],
            ["add_paper"],
            [],  # Context management
            ["synthesize"],
        ]
        conv.verify_tool_sequence(expected_sequence)


#=======================================================================
# Context management conversation tests
#=======================================================================

# All of these pass
class TestContextManagementConversations:
    """Test context management with approval loops."""
    
    @pytest.mark.asyncio
    async def test_context_with_feedback(self, nl_handler_with_mocked_input, capsys):
        """Test context management with user feedback."""
        # Configure mock to simulate feedback loop
        with patch('rich.console.Console.input') as mock_input:
            # First: provide feedback, Second: accept
            mock_input.side_effect = ["change first to abstract", ""]
            
            await nl_handler_with_mocked_input.handle_query(
                "Add all papers to context as full text",
            )
            
            # Verify feedback was processed
            assert mock_input.call_count == 2
    
    @pytest.mark.asyncio
    async def test_context_modification_flow(self, nl_handler_with_mocked_input, capsys):
        """Test complex context modification flows."""
        conv = ConversationTest(nl_handler_with_mocked_input)
        
        # First add some papers to context
        await conv.send_query("Add BERT paper to context with abstract")
        
        # Then modify the context type
        await conv.send_query("Change it to full text")
        
        # Then add more papers
        await conv.send_query("Also add the transformer paper with notes")
        
        # All context operations don't use standard tracked tools
        # But we can verify the conversation flows work without errors
        assert len(conv.conversation_history) == 3

    @pytest.mark.asyncio
    async def test_context_cancellation_flow(self, nl_handler_with_mocked_input, capsys):
        """Test context management cancellation."""
        # Configure mock to simulate cancellation
        with patch('rich.console.Console.input') as mock_input:
            mock_input.return_value = "q"
            
            await nl_handler_with_mocked_input.handle_query(
                "Add all papers to context as abstracts",
            )
            
            # Verify cancellation was processed
            assert mock_input.call_count == 1


#=======================================================================
# Enhanced conversation flow tests
#=======================================================================

class TestEnhancedConversationFlow:
    """Test enhanced multi-turn conversation flows."""

    @pytest.mark.asyncio
    async def test_contextual_paper_references(self, nl_handler_with_mocked_input, capsys):
        """Test that the system can handle contextual paper references."""
        conv = ConversationTest(nl_handler_with_mocked_input)
        
        # First mention a specific paper
        await conv.send_query("Show me the BERT paper details")
        
        # Then refer to it indirectly
        await conv.send_query("Add that paper to my collection")
        conv.verify_last_tools(["add_paper"])
        
        # Then refer contextually again
        await conv.send_query("What year was it published?")
        
        # Should maintain context throughout
        assert len(conv.conversation_history) == 3

    @pytest.mark.asyncio
    async def test_research_methodology_conversation(self, nl_handler_with_mocked_input, capsys):
        """Test a realistic research methodology conversation."""
        conv = ConversationTest(nl_handler_with_mocked_input)
        
        # Start with broad search
        await conv.send_query("Find papers on attention mechanisms")
        conv.verify_last_tools(["find_papers"])
        
        # Narrow down based on results
        await conv.send_query("Add the papers from 2017 onwards")
        conv.verify_last_tools(["add_paper"])
        
        # Ask for overview of collection
        await conv.send_query("What papers do I have now?")
        conv.verify_last_tools(["papers_command"])
        
        # Add specific papers to context for analysis
        await conv.send_query("Add the transformer and BERT papers to context")
        
        # Perform synthesis
        await conv.send_query("Compare their approaches to attention")
        conv.verify_last_tools(["synthesize"])
        
        # Verify complete workflow
        expected_sequence = [
            ["find_papers"],
            ["add_paper"], 
            ["papers_command"],
            [],  # Context management
            ["synthesize"],
        ]
        conv.verify_tool_sequence(expected_sequence)


if __name__ == "__main__":
    # Can run specific tests directly
    import sys
    pytest.main([__file__] + sys.argv[1:])
