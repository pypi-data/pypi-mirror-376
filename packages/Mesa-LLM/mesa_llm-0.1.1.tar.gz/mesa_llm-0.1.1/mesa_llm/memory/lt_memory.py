from typing import TYPE_CHECKING

from mesa_llm.memory.memory import Memory, MemoryEntry

if TYPE_CHECKING:
    from mesa_llm.llm_agent import LLMAgent


class LongTermMemory(Memory):
    """
    Purely long-term memory class that tries to store everything the agent experiences.

    Attributes:
        agent : the agent that the memory belongs to
        display : whether to display the memory
        llm_model : the model to use for the summarization

    """

    def __init__(
        self,
        agent: "LLMAgent",
        display: bool = True,
        llm_model: str = "openai/gpt-4o-mini",
    ):
        if not llm_model:
            raise ValueError(
                "llm_model must be provided for the usage of long term memory"
            )

        super().__init__(
            agent=agent,
            llm_model=llm_model,
            display=display,
        )

        self.long_term_memory = ""
        self.system_prompt = """
            You are a helpful assistant that summarizes all memory entries and stores it into long-term.
            The long term memory should be a summary of the individual memory entries such that it is concise and informative.
            """
        self.buffer = None
        if self.agent.step_prompt:
            self.system_prompt += f" This is the prompt of the problem you will be tackling:{self.agent.step_prompt}, ensure you summarize the memory entries into long-term a way that is relevant to the problem at hand."

        self.llm.system_prompt = self.system_prompt

    def _update_long_term_memory(self):
        """
        Update the long term memory by summarizing the short term memory with a LLM
        """

        prompt = f"""
            This is the current Long term memory:
                {self.long_term_memory}
            This is the new memory entry:
                {self.buffer}

            """

        self.long_term_memory = self.llm.generate(prompt)

    def process_step(self, pre_step: bool = False):
        """
        Process the step of the agent :
        - Merge the new entry into the long term memory
        - Display the new entry
        """

        if pre_step:
            new_entry = MemoryEntry(
                agent=self.agent,
                content=self.step_content,
                step=None,
            )
            self.buffer = new_entry
            self.step_content = {}
            return

        elif self.buffer and self.buffer.step is None:
            self.step_content.update(self.buffer.content)
            new_new_entry = MemoryEntry(
                agent=self.agent,
                content=self.step_content,
                step=self.agent.model.steps,
            )
            self.buffer = new_new_entry
            self._update_long_term_memory()
            self.step_content = {}

        # Display the new entry
        if self.display:
            self.buffer.display()

    def format_long_term(self) -> str:
        """
        Get the long term memory
        """
        return str(self.long_term_memory)

    def get_prompt_ready(self) -> str:
        return f"Long term memory: \n{self.format_long_term()}"

    def get_communication_history(self) -> str:
        """
        Get the communication history
        """
        return "communication history is in memory of the agent"
