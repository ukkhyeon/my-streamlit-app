
import json
import streamlit as st
from openai import OpenAI

# OpenAI 클라이언트
client = OpenAI()


def extract_tasks(meeting_text):
    sys_role = """
    당신은 김 대리의 AI 개인비서 에이블입니다.

    회의록에서 김 대리에게 배정된 업무만 추출합니다.
    다른 직원의 업무는 제외합니다.
    명확한 마감일이 없으면 null로 표시합니다.
    빠른 처리 요청과 같은 긴급성 표현은 보존합니다.
    확정된 업무와 제안된 업무를 구분합니다.
    회의록에 없는 정보는 만들어내지 않습니다.
    """

    prompt = f"""
    다음 회의록에서 김 대리의 업무를 추출해주세요.

    각 업무에 다음 정보를 포함해주세요.
    - task_name: 업무명
    - deadline: 마감일
    - urgency: 긴급성
    - assignment_status: 확정 / 제안 / 확인 필요
    - source: 회의록 원문 근거

    결과는 반드시 다음 형태의 JSON 객체로 반환하세요.
    {{"tasks": []}}

    [회의록]
    {meeting_text}
    """

    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=sys_role,
        input=prompt,
        text={"format": {"type": "json_object"}}
    )

    return json.loads(response.output_text)




# 페이지 설정
st.set_page_config(
    page_title="ABLE | AI 개인비서",
    page_icon="🤖",
    layout="wide"
)

st.title("ABLE | 김 대리의 AI 개인비서")
st.write("회의록을 분석하고 담당 업무를 정리해드립니다.")

# 역할 지정
sys_role = """
당신은 김 대리의 AI 개인비서 '에이블'입니다.
회의록을 바탕으로 질문에 답변하고,
김 대리가 업무를 효율적으로 수행하도록 돕습니다.
회의록에 없는 내용은 임의로 만들어내지 않습니다.
"""

# 상태 초기화
if "meeting_text" not in st.session_state:
    st.session_state.meeting_text = ""

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "answer" not in st.session_state:
    st.session_state.answer = ""

# 1. 회의록 업로드
st.subheader("📄 회의록 분석")

uploaded_file = st.file_uploader(
    "회의록 TXT 파일을 업로드하세요.",
    type=["txt"]
)

if uploaded_file is not None:
    meeting_text = uploaded_file.getvalue().decode("utf-8")

    # 이전 회의록과 다른 경우 분석
    if meeting_text != st.session_state.meeting_text:
        st.session_state.meeting_text = meeting_text

        with st.spinner("김 대리의 담당 업무를 분석하고 있습니다..."):
            result = extract_tasks(meeting_text)
            st.session_state.tasks = result.get("tasks", [])

# 2. 업무 목록 출력
if st.session_state.meeting_text:
    st.subheader("📋 김 대리의 업무 목록")

    tasks = st.session_state.tasks

    if tasks:
        for i, task in enumerate(tasks):
            with st.container(border=True):
                st.markdown(
                    f"### {i + 1}. {task.get('task_name', '업무명 없음')}"
                )
                st.write(
                    "마감일:",
                    task.get("deadline") or "미정"
                )
                st.write(
                    "긴급성:",
                    task.get("urgency") or "언급 없음"
                )
                st.write(
                    "업무 배정 상태:",
                    task.get("assignment_status") or "확인 필요"
                )
                st.caption(
                    "회의록 근거: " +
                    str(task.get("source") or "없음")
                )
    else:
        st.info("김 대리에게 배정된 업무가 없습니다.")

# 3. 음성 명령
st.subheader("🎤 에이블에게 질문하기")

audio_value = st.audio_input("무엇을 도와드릴까요?")

if st.button("음성 질문 실행"):

    if audio_value is None:
        st.warning("음성을 먼저 녹음해주세요.")

    else:
        # STT
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=(
                "audio.wav",
                audio_value.getvalue(),
                "audio/wav"
            )
        )

        st.write("인식된 질문:", transcript.text)

        # LLM 호출
        with st.spinner("답변을 생성하고 있습니다..."):
            response = client.responses.create(
                model="gpt-4o-mini",
                instructions=sys_role,
                input=f"""
                사용자 질문:
                {transcript.text}

                [회의록]
                {st.session_state.meeting_text}
                """
            )

            st.session_state.answer = response.output_text

# 4. 음성 질문 답변 출력
if st.session_state.answer:
    st.subheader("🤖 에이블의 답변")
    st.write(st.session_state.answer)


