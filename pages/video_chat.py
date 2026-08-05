from __future__ import annotations

import json
from typing import Any

import streamlit as st

from api_client import APIError, event_text
from auth import client, handle_api_error
from components.ui import source_caption, status_card


def _uid(video: dict[str, Any]) -> str | None:
    return video.get("uid") or video.get("videoUid") or video.get("video_uid") or video.get("id")


def _session_id(session: dict[str, Any]) -> str | None:
    value = session.get("sessionId") or session.get("session_id") or session.get("id")
    return str(value) if value else None


def _message(item: dict[str, Any]) -> dict[str, Any]:
    role = item.get("role") or item.get("sender") or item.get("type") or "assistant"
    role = "user" if str(role).lower() in {"user", "human", "question"} else "assistant"
    content = item.get("content") or item.get("message") or item.get("text") or item.get("answer") or ""
    sources = item.get("sources") or item.get("citations") or item.get("timestamps") or []
    if isinstance(sources, str):
        sources = [sources]
    elif not isinstance(sources, list):
        sources = []
    formatted_sources = [
        str(source.get("timestamp") or source.get("startTime") or source.get("url") or source)
        if isinstance(source, dict)
        else str(source)
        for source in sources
    ]
    return {"role": role, "content": str(content), "sources": formatted_sources}


def _load_messages(session_id: str) -> None:
    try:
        st.session_state.chat_history = [_message(item) for item in client().list_chat_messages(session_id)]
        st.session_state.loaded_message_session = session_id
    except APIError as error:
        handle_api_error(error)


def _session_picker(video_uid: str) -> None:
    try:
        sessions = client().list_sessions()
    except APIError as error:
        st.caption(f"Unable to load other sessions: {error}")
        return
    matching = [s for s in sessions if str(s.get("videoUid") or s.get("video_uid") or s.get("videoId") or "") == video_uid]
    if not matching:
        return
    options = {_session_id(s): (s.get("title") or s.get("name") or f"Conversation {_session_id(s)}") for s in matching if _session_id(s)}
    current = st.session_state.get("chat_session_id")
    selected = st.selectbox("Conversation", list(options), index=list(options).index(current) if current in options else 0, format_func=lambda sid: str(options[sid]))
    if selected != current:
        st.session_state.chat_session_id = selected
        st.session_state.chat_history = []
        st.session_state.pop("loaded_message_session", None)
        st.rerun()


def _new_session(video_uid: str, title: str) -> None:
    try:
        result = client().create_session(video_uid, title=f"Chat: {title[:70]}")
        session_id = _session_id(result)
        if not session_id:
            st.error("The API did not return a chat session ID.")
            return
        st.session_state.chat_session_id = session_id
        st.session_state.chat_history = []
        st.session_state.loaded_message_session = session_id
        st.rerun()
    except APIError as error:
        handle_api_error(error)


def _delete_current_session(session_id: str) -> None:
    try:
        client().delete_chat_session(session_id)
        st.session_state.pop("chat_session_id", None)
        st.session_state.pop("loaded_message_session", None)
        st.session_state.chat_history = []
        st.success("Conversation deleted.")
        st.rerun()
    except APIError as error:
        handle_api_error(error)


def render() -> None:
    video = st.session_state.get("selected_video")
    if not video:
        st.info("Choose an analyzed video from the Dashboard to start a grounded conversation.")
        return
    title = str(video.get("title") or video.get("name") or "Selected video")
    st.markdown("<div class='eyebrow'>Video insight</div>", unsafe_allow_html=True)
    st.title(title)
    st.caption(video.get("channel") or video.get("author") or video.get("sourceUrl") or video.get("url") or "Video metadata will appear here.")
    status_card(video.get("status", "ready"), video.get("duration") or "Ask questions based on the processed transcript.")
    with st.expander("Video context", expanded=False):
        st.write(video.get("description") or "No description was supplied by the API.")
        transcript = video.get("transcript") or video.get("transcriptPreview")
        if transcript:
            st.caption("Transcript preview")
            st.text_area("Transcript", str(transcript), height=140, disabled=True, label_visibility="collapsed")
        else:
            st.caption("Transcript excerpts and timestamps will appear with grounded responses when available.")
    video_uid = _uid(video)
    if not video_uid:
        st.warning("This result does not include a video identifier. Refresh it from the Dashboard before starting a chat.")
        return
    video_uid = str(video_uid)
    session_id = st.session_state.get("chat_session_id")
    controls, create, manage = st.columns([4, 1, 1])
    with controls:
        if session_id:
            _session_picker(video_uid)
    with create:
        if st.button("New chat", use_container_width=True, type="primary"):
            _new_session(video_uid, title)
    with manage:
        if session_id:
            with st.popover("Manage", use_container_width=True):
                st.caption("Deleting removes this conversation, not the analyzed video.")
                if st.button("Delete conversation", type="secondary", use_container_width=True):
                    _delete_current_session(str(session_id))
    session_id = st.session_state.get("chat_session_id")
    if not session_id:
        st.info("Start a new chat to ask questions using this video’s transcript.")
        return
    if st.session_state.get("loaded_message_session") != session_id:
        _load_messages(str(session_id))
    st.caption("Answers are grounded in the processed transcript. Sources and timestamps appear when the API provides them.")
    for item in st.session_state.get("chat_history", []):
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("sources"):
                source_caption(item["sources"])
    prompt = st.chat_input("Ask about this video")
    if not prompt:
        return
    st.session_state.chat_history.append({"role": "user", "content": prompt, "sources": []})
    with st.chat_message("user"):
        st.markdown(prompt)
    answer, sources = "", []
    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            for event, payload in client().stream_chat(str(session_id), prompt):
                if event == "token":
                    answer += event_text(payload)
                    placeholder.markdown(answer + "▍")
                elif event == "error":
                    raise APIError(event_text(payload))
                elif event == "done":
                    try:
                        done = json.loads(payload)
                        raw_sources = (done.get("sources") or done.get("citations") or []) if isinstance(done, dict) else []
                        for source in raw_sources:
                            sources.append(str(source.get("timestamp") or source.get("url") or source) if isinstance(source, dict) else str(source))
                    except json.JSONDecodeError:
                        pass
            placeholder.markdown(answer or "I couldn't produce an answer for this video.")
        except APIError as error:
            handle_api_error(error)
            return
    st.session_state.chat_history.append({"role": "assistant", "content": answer, "sources": sources})
