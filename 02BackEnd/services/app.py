from preprocessing import preprocess_data_guide, preprocess_data_api_v1, preprocess_data_api_v2
from fastapi import FastAPI, HTTPException
from vectorstore import get_vectorstoremanager_instance
from workflow import get_workflow
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

app = FastAPI()

def preprocess_data():
    '''
    PDF 문서 파싱/전처리 후 벡터스토어 적재 함수
    '''
    preprocess_data_guide()
    preprocess_data_api_v1()
    print('Done')

@app.post("/api/workflow")
async def run_workflow(request: Request):
    app_workflow = await get_workflow()
    user_input = await request.json()
    inputs = {
        "messages": [
            HumanMessage(
                content=user_input['message']
            )
        ]
    }
    result = app_workflow.invoke(inputs)
    return StreamingResponse(result['messages'][-1], media_type="text/event-stream") 

if __name__ == "__main__":
    try:
        #preprocess_data()
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8001)
    except Exception as e:
        print('=== __main__ error ===')
        print(e)
        print('======================')
    finally:
        get_vectorstoremanager_instance().get_client().close()
        