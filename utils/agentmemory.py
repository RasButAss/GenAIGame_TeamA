import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from utils.track_tokens import token_tracker
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain.schema import BaseMemory, Document
from langchain.utils import mock_now
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import json
from utils.prompts import agentMemoryPromptJson

class AgentMemory(BaseMemory):

    llm : BaseLanguageModel
    memory_retriever : TimeWeightedVectorStoreRetriever
    reflection_threshold : Optional[float] = None
    current_plan : List[str] = []
    importance_weight : float = 0.15
    aggregate_importance: float = 0.0

    # meta data
    # input keys

    queries_key: str = "queries"
    most_recent_memories_token_key: str = "recent_memories_token"
    add_memory_key: str = "add_memory"

    # output keys

    relevant_memories_key: str = "relevant_memories"
    relevant_memories_simple_key: str = "relevant_memories_simple"
    most_recent_memories_key: str = "most_recent_memories"
    now_key: str = "now"
    reflecting: bool = False

    def chain(self, prompt : PromptTemplate):
        return prompt | self.llm
    
    def token_tracked_chain(self, prompt, variables):
        @token_tracker
        def invoke(prompt, variables):
            response = self.chain(prompt).invoke(variables)
            return response
        
        return invoke(prompt, variables)
    
    def _parse_list(self, text: str) -> List[str]:
        """Parse a newline-separated string into a list of strings."""
        lines = re.split(r"\n", text.strip())
        lines = [line for line in lines if line.strip()]  # remove empty lines
        return [re.sub(r"^\s*\d+\.\s*", "", line).strip() for line in lines]
    
    # add memories function
    def pause_to_reflect(self, now: Optional[datetime] = None,agent_name: str = "agent") -> List[str]:
        """Reflect on recent observations and generate 'insights'."""
        # if self.verbose:
        #     logger.info("Character is reflecting")
        new_insights = []
        topics = self._get_topics_of_reflection()
        with ThreadPoolExecutor as executor:
            insights_threads = [executor.submit(self._get_insights_on_topic, topic, now=now) for topic in topics]
            for insights in concurrent.futures.as_completed(insights_threads):
                for insight in insights:
                    self.add_memory(insight, now=now,agent_name=agent_name)
                new_insights.extend(insights)
        return new_insights

    def _score_memory_importance(self, memory_content: str) -> float:
        """Score the absolute importance of the given memory."""
        prompt = PromptTemplate.from_template(agentMemoryPromptJson["_score_memory_importance"])
        variables = {"memory_content":memory_content}
        score = self.token_tracked_chain(prompt, variables)
        match = re.search(r"^\D*(\d+)", score)
        # if self.verbose:
        #     logger.info(f"Importance score: {score}")
        if match:
            return (float(match.group(1)) / 10) * self.importance_weight
        else:
            return 0.0
    
    def add_memory(
        self, memory_content: str, now: Optional[datetime] = None,agent_name: str = "agent"
    ) -> List[str]:
        """Add an observation or memory to the agent's memory."""
        with open(f"memories/{agent_name}_memories.json", 'r+') as file:
                # print(f"saving memory of{agent_name}")
                memories = json.load(file)
                memories.append({'memory': memory_content, 'timestamp': datetime.now().isoformat()})
                file.seek(0)
                json.dump(memories, file, indent=4)
        
        importance_score = self._score_memory_importance(memory_content)
        self.aggregate_importance += importance_score
        document = Document(
            page_content=memory_content, metadata={"importance": importance_score}
        )
        result = self.memory_retriever.add_documents([document], current_time=now)

        if (
            self.reflection_threshold is not None
            and self.aggregate_importance > self.reflection_threshold
            and not self.reflecting
        ):
            self.reflecting = True
            self.pause_to_reflect(now=now,agent_name=agent_name)
            # Hack to clear the importance from reflection
            self.aggregate_importance = 0.0
            self.reflecting = False
        return result
    
    def _format_memory_detail(self, memory: Document, prefix: str = "") -> str:
        created_time = memory.metadata["created_at"].strftime("%B %d, %Y, %I:%M %p")
        return f"{prefix}[{created_time}] {memory.page_content.strip()}"
    
    def _get_topics_of_reflection(self, last_k: int = 50) -> List[str]:
        """Return the 3 most salient high-level questions about recent observations."""
        prompt = PromptTemplate.from_template(agentMemoryPromptJson["_get_topics_of_reflection"])
        observations = self.memory_retriever.memory_stream[-last_k:]
        observation_str = "\n".join(
            [self._format_memory_detail(o) for o in observations]
        )
        variables = {"observations" : observation_str}
        result = self.token_tracked_chain(prompt, variables)
        return self._parse_list(result.content)
    
    # working with warning
    def fetch_memories(
        self, observation: str, now: Optional[datetime] = None
    ) -> List[Document]:
        """Fetch related memories."""
        # remove mock now, uneccessarily complicating
        if now is not None:
            with mock_now(now):
                return self.memory_retriever.invoke(observation)
        else:
            return self.memory_retriever.invoke(observation)
    
    def _get_insights_on_topic(
        self, topic: str, now: Optional[datetime] = None
    ) -> List[str]:
        """Generate 'insights' on a topic of reflection, based on pertinent memories."""
        prompt = PromptTemplate.from_template(agentMemoryPromptJson["_get_insights_on_topic"])

        related_memories = self.fetch_memories(topic, now=now)
        related_statements = "\n".join(
            [
                self._format_memory_detail(memory, prefix=f"{i+1}. ")
                for i, memory in enumerate(related_memories)
            ]
        )
        variables = {
            "topic":topic, 
            "related_statements":related_statements
        }

        result = self.token_tracked_chain(prompt, variables)
        # TODO: Parse the connections between memories and insights
        return self._parse_list(result.content)
    
    def clear(self) -> None:
        return

    def load_memory_variables(self):
        return {}

    def memory_variables(self):
        return []


    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any],agent_name: str):
        mem = outputs.get(self.add_memory_key)
        now = outputs.get(self.now_key)
        
        if mem:
            self.add_memory(mem, now=now,agent_name=agent_name)
    