import operator, json, os
from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.tools.render import format_tool_to_openai_function
from langchain.tools.retriever import create_retriever_tool
from langchain.output_parsers import PydanticOutputParser
from langchain.output_parsers.openai_tools import PydanticToolsParser
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.graph import END, StateGraph
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain import hub
from typing import Annotated, Sequence, TypedDict
from vectorstore import get_vectorstoremanager_instance
from langchain_community.retrievers import TavilySearchAPIRetriever

guide_doc_idx = 'LangChain_6e4361e2362640ec9b1b772fa130bc20'
api_doc_idx   = 'LangChain_9405daf90a3a4b83b150e3a543fb2dde'

vectorstore = get_vectorstoremanager_instance()
# 가이드 문서 retriever
retriever_guide = vectorstore.load_retriever(guide_doc_idx, 5)
# API 문서 retriever
retriever_api = vectorstore.load_retriever(api_doc_idx, 5)

retriever_tool_guide = create_retriever_tool(
    retriever_guide,
    name="retriever_guide",
    description='''
    금융 분야 마이데이터 기술 가이드라인 입니다.
    마이데이터 서비스 주요절차와 참여자, 역할 등이 포함된 개요가 있으며,
    마이데이터서비스 등록, 전송 절차, 전송 내역 관리, 본인인증, 개별인증, 통합인증, 중계기관을 통한 본인인증 관련 가이드가 작성되어있습니다.
    관리적, 물리적, 기술적 보안사항이 있고 개인신용정보 전송, api, 본인인증 관련 질의응답도 있습니다.
    ''',
)
retriever_tool_api = create_retriever_tool(
    retriever_api,
    name="retriever_api",
    description='''
    금융 분야 마이데이터 표준 API 규격입니다.
    표준 API 목록과 API 명세가 적혀있으며, 각종 용어에 대한 정의도 있습니다.
    API의 각종 데이터 규격과 타입이 작성되어있고 네트워크, 통신 관련 내용이 많습니다.
    마이데이터를 사용하는 사람들이 api를 처리하고 특정 규격을 호출하고 수신 받을 수 있도록 규격이 정의되어있습니다.
    ''',
)

tools = [retriever_tool_guide, retriever_tool_api]
tool_executor = ToolExecutor(tools)

class AgentState(TypedDict):  # State 정의
    messages: Annotated[Sequence[BaseMessage], operator.add]
    tool_name: str

def should_retrieve(state):
    """
    함수 호출 확인. 함수 호출이 있으면 프로세스 지속. 그렇지 않으면 종료.
    Args:
        state (messages): 현재 상태
    Returns:
        str: 프로세스를 "계속"하거나 "종료"
    """
    messages = state["messages"]
    last_message = messages[-1]

    # 함수 추출 여부
    if "function_call" not in last_message.additional_kwargs:
        #print("---FALLBACK --> tavilysearch---")
        return "fallback"
    else:
        #print(f"---CONITNUE Retreive---")
        return "continue"

def grade_documents(state):
    """
    해당 tool_name에서 검색된 문서가 적절한지 판단
    Args:
        state (messages, tool_name): 현재 상태
    Returns:
        str: 문서가 관련이 있는지 여부에 대한 결정
    """

    #print("---CHECK RELEVANCE---")
    class grade(BaseModel):
        """검색된 문서들이 질문과 얼마나 관련이 있는지를 나타내는 이진 점수"""
        binary_score: str = Field(description="'yes' 또는 'no'로 판단")

    model = ChatOpenAI(
        temperature=0, model="gpt-3.5-turbo", streaming=True)
        #temperature=0, model="gpt-4o-mini", streaming=True)

    grade_tool_oai = convert_to_openai_tool(grade)

    llm_with_tool = model.bind(
        tools=[convert_to_openai_tool(grade_tool_oai)],
        tool_choice={"type": "function", "function": {"name": "grade"}},
    )

    parser_tool = PydanticToolsParser(tools=[grade])

    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
        Here is the retrieved document: \n\n {context} \n\n
        Here is the user question: {question} \n
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.""",
        input_variables=["context", "question"],
    )

    chain = prompt | llm_with_tool | parser_tool

    messages = state["messages"]
    last_message = messages[-1]

    question = messages[0].content
    docs = last_message.content

    score = chain.invoke({"question": question, "context": docs})

    grade = score[0].binary_score

    if grade == "yes":
        #print("---DECISION: 관련 문서 O---")
        return "yes"

    else:
        #print("---DECISION: 관련 문서 X---")
        return "no"

## Nodes
def multi_agent(state):
    """
    현재 상태를 기반으로 에이전트 모델을 호출하여 응답을 생성합니다. 질문에 따라 검색 도구를 사용하여 검색을 결정하거나 단순히 종료합니다.
    Args:
        state (messages, tool_name): 현재 상태
    Returns:
        dict: 메시지에 에이전트 응답이 추가 업데이트된 응답
    """
    #print("---CALL AGENT---")
    messages = state["messages"]

    human_message = messages[0]
    modified_content = '''
당신은 마이데이터의 전반적인 개념과 api 사용에 대한 광범위한 답변을 수행하는 챗봇입니다.
아래에 작성된 질문을 이해하고 반드시 function_call에 세팅되어있는 tool을 활용하여 답변을 생성해주세요.
답변하기 어렵다면 마이데이터 관련 질문이 아니라고 답변하면 됩니다.
질문:
''' + human_message.content

    modified_message = HumanMessage(content=modified_content, 
                                additional_kwargs=human_message.additional_kwargs, 
                                response_metadata=human_message.response_metadata)
    
    # tool 여부 확인    
    model = ChatOpenAI(temperature=0, streaming=True,
                        #model="gpt-4o-2024-08-06")
                        #model="gpt-4o-mini")
                       model="gpt-4-0125-preview")
                       #model="gpt-3.5-turbo")
    functions = [format_tool_to_openai_function(t) for t in tools]
    model = model.bind_functions(functions)
    response_with_tool = model.invoke([modified_message])
    return {"messages": [response_with_tool]}

def retrieve(state):
    """
    도구를 사용하여 검색을 실행합니다.
    Args:
        state (messages, tool_name): 현재 상태
    Returns:
        dict: 검색된 문서가 추가된 응답
    """
    #print("---FIRST RETRIEVAL---")
    messages = state["messages"]
    last_message = messages[-1]
    
    action = ToolInvocation(
        tool=last_message.additional_kwargs["function_call"]["name"],
        tool_input=json.loads(
            last_message.additional_kwargs["function_call"]["arguments"]
        ),
    )
    
    response = tool_executor.invoke(action)
    function_message = FunctionMessage(content=str(response), name=action.tool)

    return {"messages": [function_message], "tool_name":action.tool}

def retry_retrieve(state):
    """
    도구를 사용하여 검색을 실행합니다.
    Args:
        state (messages, tool_name): 현재 상태
    Returns:
        dict: 검색된 문서가 다시 추가된 응답
    """
    #print("---RETRY RETRIEVAL---")
    messages = state["messages"]
    tool_name = state["tool_name"]

    if tool_name == 'retriever_api':
        tool_name = 'retriever_guide'
    else:
        tool_name = 'retriever_api'
    
    last_message = messages[1] # AIMessage

    # tool_name만 변경. 질의구문은 유지
    action = ToolInvocation(
        tool=tool_name,
        tool_input=json.loads(
            last_message.additional_kwargs["function_call"]["arguments"]
        ),
    )
    
    response = tool_executor.invoke(action)
    function_message = FunctionMessage(content=str(response), name=action.tool)

    return {"messages": [function_message]}

def generate(state):
    """
    답변 생성
    Args:
        state (messages, tool_name): 현재 상태
    Returns:
         dict: 최종 LLM 답변이 추가된 응답
    """
    messages = state["messages"]
    question = messages[0].content
    last_message = messages[-1]

    question = messages[0].content
    docs = last_message.content

    prompt = hub.pull("rlm/rag-prompt")

    llm = ChatOpenAI(model_name="gpt-4o-2024-08-06",
                     temperature=0, streaming=True)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = prompt | llm | StrOutputParser()

    response = rag_chain.invoke({"context": docs, "question": question})
    return {"messages": [response]}

# Not used
def none_retrieve(state):
    """
    답변 생성
    Args:
        state (messages, tool_name): 현재 상태
    Returns:
         dict: 검색기를 태우지 않은 답변이 추가된 응답
    """
    messages = state["messages"]
    question = messages[0].content

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "사용자의 질의에 답변해주세요."),
            ("user", "{question}"),
        ]
    )

    llm = ChatOpenAI(model_name="gpt-3.5-turbo",
                     temperature=0, streaming=True)

    rag_chain = chat_prompt | llm | StrOutputParser()

    response = rag_chain.invoke({"question": question})
    return {"messages": [response]}

def generate_with_tavily(state):
    """
    답변 생성
    Args:
        state (messages, tool_name): 현재 상태
    Returns:
         dict: Tavily검색을 통한 답변 응답
    """
    messages = state["messages"]
    question = messages[0].content
    
    if len(question.split()) == 1:
        # 한 단어일 경우 '검색'을 추가
        question += ' 검색'
    
    template = """다음 문맥을 참고하여 자유롭게 사용자 질문에 답변해주세요. 
    당신은 웹 검색 도구도 같이 보유하고 있으므로 반드시 검색을 활용해야합니다.
    검색에서 나온 context를 필요 시 참고하여 답변해주세요.
    간단한 안부인사 질문은 context를 참고하지 말아주세요.
    당신의 이름은 카카오뱅크 마이데이터 봇입니다.
    한국어로 답변해야합니다. 문맥:

    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(model_name="gpt-4o-mini",
                     temperature=0, streaming=True)
    retriever = TavilySearchAPIRetriever(k=3)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    tavily_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    response = tavily_chain.invoke(question)
    return {"messages": [response]}

async def get_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("multi_agent", multi_agent) 
    workflow.add_node("retrieve", retrieve)  
    workflow.add_node("retry_retrieve", retry_retrieve)
    workflow.add_node("generate", generate)
    #workflow.add_node("none_retrieve", none_retrieve) # tavily로 대체
    workflow.add_node("generate_with_tavily", generate_with_tavily)

    # 루트 노드
    workflow.set_entry_point("multi_agent")

    # 검색기 판단
    workflow.add_conditional_edges(
        "multi_agent",
        # 에이전트 결정 평가
        should_retrieve,
        {
            # 도구 노드 호출
            "continue": "retrieve",
            "fallback": "generate_with_tavily",
        },
    )
    # 생성 or 재탐색 여부
    workflow.add_conditional_edges(
        "retrieve",
        grade_documents,
        {
            "yes": "generate",
            "no": "retry_retrieve",
        },
    )
    # 생성 or 웹서칭 여부
    workflow.add_conditional_edges(
        "retry_retrieve",
        grade_documents,
        {
            "yes": "generate",
            "no": "generate_with_tavily",
        },
    )
    workflow.add_edge("generate", END)
    #workflow.add_edge("none_retrieve", END)
    workflow.add_edge("generate_with_tavily", END)

    return workflow.compile()