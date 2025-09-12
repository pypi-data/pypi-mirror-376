"""Unit tests for natural language query handling - verifies correct tool selection.

NOTE: Tool names must match those in tools.py as the system prompt relies on these names.

IMPORTANT: These tests verify that the LLM selects the correct tool for each query type.
They do NOT test the actual execution or response of the tools themselves.

TODO: Several tests may need redefining because the NaturalLanguageHandler now
injects paper collection context on the first query, which means the LLM may
answer questions directly without calling tools. Tests that may need adjustment:
- test_basic_list_query: LLM might not call list_papers if context is injected
- test_tool_call_verification: Tool calls may differ with injected context
- Tests expecting specific tool calls when info is already available

The only modifications for testing are:
- Wrapping command handlers to track which tools get called
- Disabling tool approval for automated testing
- Using GPT-5-nano model for cost efficiency

This test module validates:
1. The LLM correctly maps natural language queries to appropriate tools
2. Tool selection logic works for various query types
3. Edge cases are handled appropriately

Test Structure:
--------------
Fixtures:
- temp_dir: Creates isolated temporary directory for test data
- config: Sets up Config with GPT-5-nano model configuration
- db: Creates Database instance for test papers
- sample_papers: Populates database with 3 AI/NLP papers for testing
- nl_handler_with_tracking: Creates NaturalLanguageHandler with wrapped command
  handlers that track which tools are called during query processing

Test Classes:
------------
1. TestRealNaturalLanguageQueries: Core functionality tests
   - Basic queries (list, find, tag operations)
   - Specific paper lookups and comparisons
   - Context-aware follow-up questions
   - Tool call verification

Requirements:
------------
- OPENAI_API_KEY environment variable must be set
- Tests are skipped if API key is unavailable
- Uses GPT-5-nano model for fast, cost-effective testing

Note: These are integration tests that make real API calls.
They validate end-to-end behavior rather than individual components.
"""

import asyncio
import os
import tempfile
from pathlib import Path

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
    # Set to use gpt-5-mini model
    config.update_config("llm.provider", "openai")
    config.update_config("llm.model", "gpt-5-nano")
    return config


@pytest.fixture
def db(config):
    """Create a real database."""
    return Database(config)


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
        """Forward to the wrapped handler to trigger tool selection."""
        return await self.handler.handle_query(query)

    async def close(self) -> None:
        """Forward to the wrapped handler."""
        return await self.handler.close()


@pytest_asyncio.fixture
async def nl_handler_with_tracking(db, config, sample_papers):
    """Create NL handler that tracks which tools are selected by the LLM.

    This fixture wraps the real command handlers with tracking functions to verify
    that the NaturalLanguageHandler correctly maps user queries to the appropriate
    tools. We need this wrapper approach because:

    1. The NaturalLanguageHandler expects a dictionary of command handlers that it
       calls dynamically based on LLM responses
    2. We want to test that the LLM correctly identifies which tools to use for
       different natural language queries
    3. We need to track which handlers the LLM selects to verify the tool
       selection logic is working correctly
    
    The tracking wrappers record which tools were selected by the LLM, allowing
    tests to assert that the correct tools were chosen for each query type.
    Tool execution/response is not the focus of these unit tests.
    
    We patch the LLM client's complete method to skip the second LLM call after
    tool execution, making tests faster and focused only on tool selection.
    """
    # No need to import real command handlers since we're only tracking tool selection
    # Track which tools get called
    tool_calls = []

    # Wrap handlers to track tool selection only - no execution needed for unit tests
    # Note: Tool names should match those in tools.py since the system prompt relies on these names
    async def tracked_find_papers(*args, **kwargs):
        tool_calls.append("find_papers")
        return "Tool selected: find_papers"

    def tracked_add_paper(*args, **kwargs):
        tool_calls.append("add_paper")
        return "Tool selected: add_paper"

    def tracked_papers_command(*args, **kwargs):
        tool_calls.append("papers_command")
        return "Tool selected: papers_command"

    def tracked_manage_paper_tags(*args, **kwargs):
        tool_calls.append("manage_paper_tags")
        return "Tool selected: manage_paper_tags"

    def tracked_list_tags(*args, **kwargs):
        tool_calls.append("list_tags")
        return "Tool selected: list_tags"

    def tracked_show_results(*args, **kwargs):
        tool_calls.append("show_search_results")
        return "Tool selected: show_search_results"

    async def tracked_synthesize(*args, **kwargs):
        tool_calls.append("synthesize")
        return "Tool selected: synthesize"

    def tracked_context_show(*args, **kwargs):
        tool_calls.append("context_show")
        return "Tool selected: context_show"

    async def tracked_note(*args, **kwargs):
        tool_calls.append("note")
        return "Tool selected: note"

    async def tracked_prompt(*args, **kwargs):
        tool_calls.append("prompt")
        return "Tool selected: prompt"

    def tracked_remove_paper(*args, **kwargs):
        tool_calls.append("remove_paper")
        return "Tool selected: remove_paper"

    # Map command handlers using the same names as in nl_handler.py
    # These names match what the LLM will call based on tools.py definitions
    command_handlers = {
        "find_papers": tracked_find_papers,
        "add_paper": tracked_add_paper,
        "list_papers": tracked_papers_command,  # papers_command maps to list_papers
        "handle_tag_command": tracked_manage_paper_tags,  # manage_paper_tags maps to handle_tag_command
        "list_tags": tracked_list_tags,
        "show_search_results": tracked_show_results,
        "remove_paper": tracked_remove_paper,
        "handle_synthesize": tracked_synthesize,
        "handle_context_show": tracked_context_show,  # context_show maps to handle_context_show
        "handle_note": tracked_note,  # note maps to handle_note
        "handle_user_prompt": tracked_prompt,  # prompt maps to handle_user_prompt
    }

    search_results = []
    from litai.context_manager import SessionContext

    session_context = SessionContext()
    nl_handler = NaturalLanguageHandler(
        db, command_handlers, search_results, config, session_context,
    )

    # Set tool approval to false (auto-approve all tools)
    nl_handler.approval_manager.enabled = False
    
    # Patch the LLM client's complete method to prevent the second LLM call
    # For each query, we want to allow the first call (tool selection) but skip the second (final response)
    original_complete = nl_handler.llm_client.complete
    
    async def patched_complete(*args, **kwargs):
        # Check if this is likely the second call (final response) by looking for "tool" in messages
        messages = args[0] if args else kwargs.get('messages', [])
        
        # If there are tool results in the messages, this is the second call - skip it
        has_tool_results = any(msg.get('role') == 'tool' for msg in messages)
        
        if has_tool_results:
            # This is the final response call after tool execution - skip it
            return {"content": ""}
        else:
            # This is the initial tool selection call - let it through
            return await original_complete(*args, **kwargs)
    
    # Apply the patch
    nl_handler.llm_client.complete = patched_complete

    # Return a wrapper that includes both the handler and the tool_calls list
    tracked_handler = TrackedNLHandler(nl_handler, tool_calls)

    yield tracked_handler

    # Cleanup
    await nl_handler.close()


#=======================================================================
# Find/Search command tests
#=======================================================================

class TestFindPapersQueries:
    """Test natural language queries related to finding/searching papers."""

    @pytest.mark.asyncio
    async def test_find_papers_query(self, nl_handler_with_tracking, capsys):
        """Test that search queries trigger find command."""
        await nl_handler_with_tracking.handle_query("Find papers about transformers")

        # Verify that find_papers tool was selected by the LLM
        assert "find_papers" in nl_handler_with_tracking.tool_calls
        # Output verification is secondary - main focus is tool selection
        captured = capsys.readouterr()


#=======================================================================
# Add paper command tests
#=======================================================================

#@TODO: Need to patch the find resutls for this to work
class TestAddPaperQueries:
    """Test natural language queries related to adding papers."""

##  @pytest.mark.asyncio
##  async def test_add_paper_basic_query(self, nl_handler_with_tracking, capsys):
##      """Test basic add paper request."""
##      await nl_handler_with_tracking.handle_query(
##          "Add a paper titled 'Deep Learning' by Goodfellow from 2016",
##      )
##      assert "add_paper" in nl_handler_with_tracking.tool_calls
##      captured = capsys.readouterr()
##      assert "add" in captured.out.lower() or "paper" in captured.out.lower()
##
##  #@TODO: Change to meet the papers
##  @pytest.mark.asyncio
##  async def test_batch_add_papers(self, nl_handler_with_tracking, capsys):
##      """Test adding multiple papers at once."""
##      await nl_handler_with_tracking.handle_query(
##          "Add these papers: arxiv:2103.14030, arxiv:2104.09125, and arxiv:2105.01601",
##      )
##      # Should call add_paper multiple times or handle batch addition
##      assert "add_paper" in nl_handler_with_tracking.tool_calls


#=======================================================================
# Collection/List command tests  
#=======================================================================

class TestCollectionQueries:
    """Test natural language queries related to listing/viewing collection."""

#   @pytest.mark.asyncio
#   async def test_basic_list_query(self, nl_handler_with_tracking, capsys):
#       """Test that asking about papers triggers list command."""
#       await nl_handler_with_tracking.handle_query(
#           "What papers do I have in my collection?",
#       )
#
#       # TODO: This test may need redefining - LLM might not call list_papers
#       # if paper info is already injected in context (which happens on first query)
#       # Verify that list_papers tool was selected
#       assert "list_papers" in nl_handler_with_tracking.tool_calls
#
#       captured = capsys.readouterr()
#       # Should see papers listed
#       assert (
#           "Attention Is All You Need" in captured.out
#           or "papers" in captured.out.lower()
#       )

    @pytest.mark.asyncio
    async def test_specific_paper_query(self, nl_handler_with_tracking, capsys):
        """Test asking about a specific paper."""
        await nl_handler_with_tracking.handle_query(
            "What can you tell me about the Attention Is All You Need paper?",
        )

        captured = capsys.readouterr()
        # Should provide information about the paper

    @pytest.mark.asyncio
    async def test_citation_count_query(self, nl_handler_with_tracking, capsys):
        """Test asking about citation counts."""
        await nl_handler_with_tracking.handle_query(
            "Which of my papers has the most citations?",
        )

        captured = capsys.readouterr()
        # Should mention the highest cited paper

    @pytest.mark.asyncio
    async def test_year_based_query(self, nl_handler_with_tracking, capsys):
        """Test queries about papers from specific years."""
        await nl_handler_with_tracking.handle_query(
            "What papers do I have from 2018?",
        )

        captured = capsys.readouterr()
        # Should mention BERT which is from 2018

    @pytest.mark.asyncio
    async def test_author_query(self, nl_handler_with_tracking, capsys):
        """Test asking about papers by specific authors."""
        await nl_handler_with_tracking.handle_query(
            "Do I have any papers by Vaswani?",
        )

        captured = capsys.readouterr()
        # Should mention the Attention paper

    @pytest.mark.asyncio
    async def test_comparison_query(self, nl_handler_with_tracking, capsys):
        """Test comparison queries between papers."""
        await nl_handler_with_tracking.handle_query(
            "Compare the BERT and GPT-3 papers in my collection",
        )

        captured = capsys.readouterr()
        # Should mention both papers

    @pytest.mark.asyncio
    async def test_tool_call_verification(self, nl_handler_with_tracking, capsys):
        """Verify that the LLM selects the correct tools for different query types."""
        # TODO: These assertions may need adjustment since paper info is injected
        # Clear previous calls
        nl_handler_with_tracking.tool_calls.clear()

        # Test that "Show me all my papers" triggers papers_command tool
        await nl_handler_with_tracking.handle_query("Show me all my papers")
        assert "papers_command" in nl_handler_with_tracking.tool_calls

        # Clear and test another query type
        nl_handler_with_tracking.tool_calls.clear()
        await nl_handler_with_tracking.handle_query(
            "What tags do I have in my collection?",
        )
        # Verify that some tool was selected (list_tags or list_papers)
        assert len(nl_handler_with_tracking.tool_calls) > 0


#=======================================================================
# Remove paper command tests
#=======================================================================

class TestRemovePaperQueries:
    """Test natural language queries related to removing papers."""

    @pytest.mark.asyncio
    async def test_remove_paper_by_title(self, nl_handler_with_tracking, capsys):
        """Test removing paper by title."""
        await nl_handler_with_tracking.handle_query(
            "Remove the BERT from my collection",
        )
        assert "remove_paper" in nl_handler_with_tracking.tool_calls
        captured = capsys.readouterr()

    @pytest.mark.asyncio
    async def test_remove_multiple_papers(self, nl_handler_with_tracking, capsys):
        """Test removing multiple papers."""
        await nl_handler_with_tracking.handle_query(
            "Remove all papers from 2017",
        )
        assert "remove_paper" in nl_handler_with_tracking.tool_calls

    #@TODO: Figure out what to do
#   @pytest.mark.asyncio
#   async def test_remove_nonexistent_paper(self, nl_handler_with_tracking, capsys):
#       """Test removing a paper that doesn't exist."""
#       await nl_handler_with_tracking.handle_query(
#           "Remove the paper about quantum computing",
#       )
#       captured = capsys.readouterr()
#       assert any(term in captured.out.lower() 
#                  for term in ["not found", "doesn't exist", "no paper", "quantum"])
#

#=======================================================================
# Tag command tests
#=======================================================================

class TestTagQueries:
    """Test natural language queries related to tags."""

    @pytest.mark.asyncio
    async def test_tag_query(self, nl_handler_with_tracking, db, capsys):
        """Test natural language tag queries."""
        # Ask about papers with specific tag
        await nl_handler_with_tracking.handle_query("Show me papers tagged with NLP")

        captured = capsys.readouterr()
        # Should show papers with NLP tag


#=======================================================================
# Note command tests
#=======================================================================

class TestNoteQueries:
    """Test natural language queries related to notes."""
    # No existing tests for note queries

    @pytest.mark.asyncio
    async def test_add_note_to_paper(self, nl_handler_with_tracking, capsys):
        """Test adding a note to a specific paper."""
        await nl_handler_with_tracking.handle_query(
            "Add a note to the BERT paper: 'Important for my research on language models'",
        )
        assert "note" in nl_handler_with_tracking.tool_calls
        captured = capsys.readouterr()

    @pytest.mark.asyncio
    async def test_view_paper_notes(self, nl_handler_with_tracking, capsys):
        """Test viewing notes for a paper."""
        await nl_handler_with_tracking.handle_query(
            "Show me the notes for the Attention paper",
        )
        assert "note" in nl_handler_with_tracking.tool_calls

    #@TODO: Idk how this will beahve; wait this is kind of good tbh
    @pytest.mark.asyncio
    async def test_add_note_without_paper_specified(self, nl_handler_with_tracking, capsys):
        """Test adding note without specifying paper."""
        await nl_handler_with_tracking.handle_query(
            "Add a note: 'This is relevant to my thesis'",
        )
        captured = capsys.readouterr()
        # Should ask which paper

    @pytest.mark.asyncio
    async def test_delete_note(self, nl_handler_with_tracking, capsys):
        """Test deleting a note from a paper."""
        await nl_handler_with_tracking.handle_query(
            "Remove the note from the GPT-3 paper",
        )
        assert "note" in nl_handler_with_tracking.tool_calls

    @pytest.mark.asyncio
    async def test_list_all_notes(self, nl_handler_with_tracking, capsys):
        """Test listing all notes across papers."""
        await nl_handler_with_tracking.handle_query(
            "Show me all my notes",
        )
        assert "note" in nl_handler_with_tracking.tool_calls



#=======================================================================
# Synthesize command tests
#=======================================================================

#@TODO: Come back, it's calling cshow, understandbly
class TestSynthesizeQueries:
    """Test natural language queries related to synthesis."""
    # No existing tests for synthesize queries
    @pytest.mark.asyncio
    async def test_basic_synthesize_query(self, nl_handler_with_tracking, capsys, db, sample_papers):
        """Test basic synthesis request."""
        # Add papers directly to session context (simulating /cadd command)
        # This is what would happen if user ran: /cadd all abstract
        for paper in sample_papers:
            nl_handler_with_tracking.handler.session_context.add_paper(
                paper.paper_id,
                paper.title,
                "abstract",  # Use abstract for faster testing
            )
        
        await nl_handler_with_tracking.handle_query(
            "Use synthesize to compare and constrast the papers.",
        )
        assert "synthesize" in nl_handler_with_tracking.tool_calls
        captured = capsys.readouterr()

    @pytest.mark.asyncio
    async def test_synthesize_with_topic(self, nl_handler_with_tracking, capsys, sample_papers):
        """Test synthesis with specific topic focus."""
        # Add papers directly to session context (simulating /cadd command)
        for paper in sample_papers:
            nl_handler_with_tracking.handler.session_context.add_paper(
                paper.paper_id,
                paper.title,
                "abstract",
            )
        
        await nl_handler_with_tracking.handle_query(
            "Use synthesize to compare my papers.",
        )
        assert "synthesize" in nl_handler_with_tracking.tool_calls

    @pytest.mark.asyncio
    async def test_synthesize_subset_of_papers(self, nl_handler_with_tracking, capsys, sample_papers):
        """Test synthesizing specific papers."""
        # Add only BERT and GPT-3 papers to context
        for paper in sample_papers:
            if "bert" in paper.paper_id.lower() or "gpt" in paper.paper_id.lower():
                nl_handler_with_tracking.handler.session_context.add_paper(
                    paper.paper_id,
                    paper.title,
                    "abstract",
                )
        
##await nl_handler_with_tracking.handle_query(
##    "Synthesize the BERT and GPT-3 papers",
##)
##assert "synthesize" in nl_handler_with_tracking.tool_calls

    @pytest.mark.asyncio
    async def test_synthesize_by_year(self, nl_handler_with_tracking, capsys, sample_papers):
        """Test synthesizing papers from specific time period."""
        # Add papers from 2018-2020 to context
        for paper in sample_papers:
            if 2018 <= paper.year <= 2020:
                nl_handler_with_tracking.handler.session_context.add_paper(
                    paper.paper_id,
                    paper.title,
                    "abstract",
                )
        
        await nl_handler_with_tracking.handle_query(
            "Create a literature review of papers from 2018-2020",
        )
        assert "synthesize" in nl_handler_with_tracking.tool_calls

    @pytest.mark.asyncio
    async def test_synthesize_with_format(self, nl_handler_with_tracking, capsys, sample_papers):
        """Test synthesis with specific format request."""
        # Add all papers to context
        for paper in sample_papers:
            nl_handler_with_tracking.handler.session_context.add_paper(
                paper.paper_id,
                paper.title,
                "abstract",
            )
        
        await nl_handler_with_tracking.handle_query(
            "Generate a synthesis in bullet points",
        )
        assert "synthesize" in nl_handler_with_tracking.tool_calls

    @pytest.mark.asyncio
    async def test_synthesize_empty_collection(self, nl_handler_with_tracking, capsys):
        """Test synthesizing when no papers match criteria."""
        await nl_handler_with_tracking.handle_query(
            "Synthesize papers about quantum computing",
        )
        captured = capsys.readouterr()



#=======================================================================
# Context command tests (cshow, cclear)
#=======================================================================

class TestContextQueries:
    """Test natural language queries related to context management."""
    # No existing tests for context queries


#=======================================================================
# User research profile command tests
#=======================================================================

class TestUserPromptQueries:
    """Test natural language queries related to user prompts."""
    @pytest.mark.asyncio
    async def test_set_user_prompt(self, nl_handler_with_tracking, capsys):
        """Test setting a custom user prompt."""
        await nl_handler_with_tracking.handle_query(
            "Set my prompt to focus on methodology critique",
        )
        assert "prompt" in nl_handler_with_tracking.tool_calls

    @pytest.mark.asyncio
    async def test_view_current_prompt(self, nl_handler_with_tracking, capsys):
        """Test viewing current user prompt."""
        await nl_handler_with_tracking.handle_query(
            "Show me my current prompt settings",
        )
        assert "prompt" in nl_handler_with_tracking.tool_calls

    @pytest.mark.asyncio
    async def test_reset_prompt(self, nl_handler_with_tracking, capsys):
        """Test resetting to default prompt."""
        await nl_handler_with_tracking.handle_query(
            "Reset my prompt to default",
        )
        assert "prompt" in nl_handler_with_tracking.tool_calls

    @pytest.mark.asyncio
    async def test_prompt_with_template(self, nl_handler_with_tracking, capsys):
        """Test using prompt templates."""
        await nl_handler_with_tracking.handle_query(
            "Use the academic review prompt template",
        )
        assert "prompt" in nl_handler_with_tracking.tool_calls

#=======================================================================
# Clear command tests; unclear whether this exists
#=======================================================================

class TestClearQueries:
    """Test natural language queries related to clearing."""
    # No existing tests for clear queries

#=======================================================================
# Error handling and edge cases
#=======================================================================

class TestErrorHandlingIntegration:
    """Test error handling with real LLM."""

##  @pytest.mark.asyncio
##  async def test_empty_collection_query(self, config, capsys):
##      """Test querying an empty collection."""
##      # Create fresh database with no papers
##      empty_db = Database(config)
##      command_handlers = {"list_papers": lambda db, page=1: "No papers in collection"}
##      search_results = []
##      from litai.context_manager import SessionContext
##
##      session_context = SessionContext()
##
##      nl_handler = NaturalLanguageHandler(
##          empty_db, command_handlers, search_results, config, session_context,
##      )
##      nl_handler.approval_manager.enabled = False
##
##      try:
##          await nl_handler.handle_query("Show me my papers")
##          captured = capsys.readouterr()
##          assert (
##              "no papers" in captured.out.lower() or "empty" in captured.out.lower()
##          )
##      finally:
##          await nl_handler.close()

    @pytest.mark.asyncio
    async def test_ambiguous_reference(self, nl_handler_with_tracking, capsys):
        """Test handling ambiguous references."""
        await nl_handler_with_tracking.handle_query(
            "Tell me about the paper",  # Ambiguous - which paper?
        )

        captured = capsys.readouterr()
        # Should either ask for clarification or list options

#=======================================================================
# Helper functions
#=======================================================================

# Helper function to run async tests synchronously if needed
def run_async_test(coro):
    """Helper to run async tests."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


if __name__ == "__main__":
    # Can run specific tests directly
    import sys

    pytest.main([__file__] + sys.argv[1:])
