from app.tools.executor import executor





#  vc Helper: build LLM with tools 
def _get_llm_with_tools():
    """
    Returns a LangChain chat model bound to our tool schemas.
    Supports OpenAI, Anthropic, and Ollama — controlled by config.
    """

    from app.config import settings
    tool_schemas = executor.tool_schemas() # get tool schemas from executor to bind to llm so that llm knows which tools are available and how to call them
    llm = None
    if settings.MODEL_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI  
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
    elif settings.MODEL_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=settings.LLM_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
        )
    elif settings.MODEL_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=settings.LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {settings.MODEL_PROVIDER}")

    # Bind tool schemas so the LLM knows what tools it can call
    return llm.bind_tools(tool_schemas)  # all tools with schemas for llm to know which tools what need and how to call them and work


'''
after bind with tools llm object looks like this when you print it in planner_node
ChatOpenAI(model='gpt-4', temperature=0, api_key='***', 
llm = {
    "model": "gpt-4",
    "can_chat": True,
    "tools": [
        {
            "name": "send_email",
            "description": "Send email"
        }
    ]
} 
'''