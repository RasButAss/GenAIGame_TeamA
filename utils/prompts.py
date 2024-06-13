from langchain_core.prompts import PromptTemplate

agentPromptJson = {
    "_get_entity_from_observation": "What is the observed entity in the following observation? {observation}"
    + "\nEntity=",
    
    "_get_entity_action" : 
    "What is the {entity} doing in the following observation? {observation}"
    + "\nThe {entity} is",
    "summarize_related_memories":             
    """{q1}?
    Context from memory:
    {relevant_memories}
    Relevant context: 
    """,
    
    "_compute_agent_summary":
            "How would you summarize {name}'s core characteristics given the"
            + " following statements:\n"
            + "{relevant_memories}"
            + "Do not embellish."
            + "\n\nSummary: ",
    
    "_generate_reaction": "{agent_summary_description}"
            + "\nIt is {current_time}."
            + "\n{agent_name}'s occupation: {agent_status}"
            + "\nSummary of relevant context from {agent_name}'s memory:"
            + "\n{relevant_memories}"
            + "\nMost recent observations: {most_recent_memories}"
            + "\nObservation: {observation}"
            + "\n\n",
    
    "generate_reaction": 
            "What should {agent_name} say to the observation"
            + " what would be an appropriate reply? Respond in one line."
            + 'Write:\n{agent_name}: "what to say"',
    
    "generate_dialogue_response": 
        "What would {agent_name} say? To end the conversation, write:"
        ' GOODBYE: "what to say". Otherwise to continue the conversation,'
        ' write: SAY: "what to say next"\n\n'
}

agentMemoryPromptJson = {
    "_get_topics_of_reflection": 
            "{observations}\n\n"
            "Given only the information above, what are the 3 most salient "
            "high-level questions we can answer about the subjects in the statements?\n"
            "Provide each question on a new line.",
    
    "_get_insights_on_topic":
            "Statements relevant to: '{topic}'\n"
            "---\n"
            "{related_statements}\n"
            "---\n"
            "What 5 high-level novel insights can you infer from the above statements "
            "that are relevant for answering the following question?\n"
            "Do not include any insights that are not relevant to the question.\n"
            "Do not repeat any insights that have already been made.\n\n"
            "Question: {topic}\n\n"
            "(example format: insight (because of 1, 5, 3))\n",
    
    "_score_memory_importance": 
            "On the scale of 1 to 10, where 1 is purely mundane"
            + " (e.g., brushing teeth, making bed) and 10 is"
            + " extremely poignant (e.g., a break up, college"
            + " acceptance), rate the likely poignancy of the"
            + " following piece of memory. Respond with a single integer."
            + "\nMemory: {memory_content}"
            + "\nRating: "
}