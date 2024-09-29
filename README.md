# 마이데이터 문서 기반 멀티에이전트

마이데이터 기술 가이드라인 및 API 규격서 기반으로 답변하는 LLM 기반 봇입니다.<br>
마이데이터 범주를 벗어난 질의를 하더라도 자체 지식과 검색 도구를 활용하여 답변합니다.

#### **활용 DATA**

- (수정게시) 금융분야 마이데이터 표준 API 규격 v1.pdf
- (221115 수정배포) (2022.10) 금융분야 마이데이터 기술 가이드라인.pdf

#### Try it !!

💻 [[**마데 멀티 에이전트 사용해보기**](http://35.209.240.229:8501/)] 👈 Click

## 1. 프로젝트 시연 클립
![마데봇](https://github.com/user-attachments/assets/99af1abc-39f0-452f-9afa-ed5a8dd1770f)


## 2. 활용도구

- 사용 언어 : ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
- 구축 인프라 : ![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white) /  ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
- 프론트 엔드 : ![image](https://github.com/user-attachments/assets/a7a6c14c-906b-4b9d-8660-f4ea04f16f2b)
- 백엔드 : ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
- 생성형 AI : ![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white)
- Vector DB : [![GitHub Tutorials](https://img.shields.io/badge/Weaviate_Tutorials-green)](https://github.com/weaviate-tutorials/)
- 활용 도구 : ![image](https://github.com/user-attachments/assets/4c6bfd37-de2d-41f3-8964-bd703a23b47f)
 ![image](https://github.com/user-attachments/assets/a68e61aa-b5c6-4f04-a76f-c522e850f8f3) ![image](https://github.com/user-attachments/assets/4ac0853d-42f2-40d6-a1a4-4b60ab0fc86a)


## 3. 전체 아키텍처
#### 설계 요소
- 인프라 확장 가능 : 클라우드 및 도커 컨테이너 기반으로 구축
- 비동기 통신 처리 : FastAPI 기반으로 구축
- 처리 속도 & 메모리 관리 : 필요할 때만 객체를 생성하고, 이미 생성된 객체는 캐싱을 통해 빠르게 재사용
- 고성능 벡터스토어 사용 : Weaviate를 별도 컨테이너로 구축하여 수평적 확장 가능
- 멀티에이전트 구축 : 사용자의 질의 내용에 따라 에이전트가 판단하여 가장 적합한 답변 생성 (LangGraph)
- 텍스트/표/이미지 다양한 서식이 포함된 PDF 문서 답변 가능
  
![image](https://github.com/user-attachments/assets/5d525816-1237-41f3-9666-a5a7aa514d8f)

## 4. 정확도 향상에 들어간 스킬
#### SELF-RAG : Self-reflective Retrieval-Augmented Generation [link](https://arxiv.org/pdf/2310.11511)
![image](https://github.com/user-attachments/assets/9daee482-72e6-4429-8109-75eb86e151be)

#### 실제 구현 흐름

기존 논문은 관련성이 가장 높은 정보를 반복하여 찾고 최적의 응답을 생성

실제 구현은 관련된 문서가 하나라도 있다고 판단되면 전체 관련 문서를 참고하여 응답 생성

- LangGraph흐름
  1. 사용자 질의 유입 시 multi_agent노드 에서 마이데이터 문서 검색이 필요한지 판단 (Continue / Fallback)
     - 필요시 1차 Retriever 수행
     - 불필요 시 웹 검색 참고하여 답변 생성 후 종료 
  2. retreve 노드에서 검색된 문서가 사용자 질의에 적합한지 판단 (yes / no)
     - 적합 판정 시 답변 생성 후 종료
     - 부적합 판정 시 2차 Retriever 수행
  3. retry_retreve 노드에서 추가로 검색된 문서가 사용자 질의에 적합한지 판단 (yes / no)
     - 적합 판정 시 답변 생성 후 종료
     - 부적합 판정 시 웹 검색 참고하여 답변 생성 후 종료
       
![langgraph 흐름](https://github.com/user-attachments/assets/3edc6433-219f-495d-894d-051f9e3ae54f)

## 5. 질문 예시
- 가이드 문서 관련
  - 토큰이 중복 발급되었을 경우 어떻게 되나요?
  - 정보 전송 요구 연장은 언제 가능한가요?
  - 마이데이터서비스 등록 준비
  - 마이데이터 사업자의 개인정보 전송요구 철회 시나리오는?
- API 관련
  - 리볼빙 정보 조회 응답 body 알려줘
  - timestamp를 이용한 부하개선을 예시를 들어 설명해줘
  - 카드 목록 조회 API는 어떤것들이 있나요?
  - 만기일시상환 코드는? 
- 그 외
  - 안녕하세요?
  - 너 이름이 뭐야?
  - 오늘 서울 날씨는?
  - 2024년 상반기 삼성전자 매출은?

## 6. 결과 예시 (Question - Answer Set)
- 질의 유형 종류
  - TYPE1 : 마이데이터 가이드 문서 관련 질문
  - TYPE2 : 마이데이터 API 문서 관련 질문
  - TYPE3 : 마이데이터와 무관한 질문
  - TYPE4 : 마이데이터 유사 질문

#### **Type1**
멀티에이전트 -> 가이드 PDF문서 참조하여 답변<br>
![image](https://github.com/user-attachments/assets/e8efca6b-2e99-472d-ba27-282fe859832a)

#### **Type2**
멀티에이전트 -> API PDF문서 참조하여 답변<br>
![image](https://github.com/user-attachments/assets/5859ae4f-4845-4aac-bc0a-c4ede7f62f9f)

#### **Type3**
멀티에이전트 -> 검색도구 활용하여 답변<br>
![image](https://github.com/user-attachments/assets/c45e97b2-b1e1-49ad-be62-06f242598555)

#### **Type4**
멀티에이전트 -> 가이드 PDF문서 확인 -> API PDF문서 확인 -> 검색 도구 활용하여 최종 답변<br>
![image](https://github.com/user-attachments/assets/ad5de5d3-f25a-4361-8860-eac70dd18dbf)






