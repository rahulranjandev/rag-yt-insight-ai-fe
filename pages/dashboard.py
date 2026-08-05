from __future__ import annotations

import re
import time
import streamlit as st

from api_client import APIError
from auth import client, handle_api_error
from components.ui import metric_card, status_card

URL_RE = re.compile(
    r"^https?://(?:www\.)?(youtube\.com|youtu\.be|instagram\.com)/", re.I
)
TERMINAL = {"completed", "complete", "ready", "success", "processed", "failed", "error"}


def _job_id(data: dict) -> str | None:
    return data.get("jobId") or data.get("job_id") or data.get("id")


def _video(data: dict) -> dict:
    return data.get("video") or data.get("result") or data.get("job") or data


def _uid(video: dict) -> str | None:
    return (
        video.get("uid")
        or video.get("videoUid")
        or video.get("video_uid")
        or video.get("videoId")
        or video.get("id")
    )


def _job_status(payload: dict) -> dict:
    """Return the backend's nested job status, when it is present."""
    status = payload.get("jobStatus")
    return status if isinstance(status, dict) else {}


def _job_state(payload: dict, video: dict) -> str | None:
    """Read state from both legacy and current video-job response shapes."""
    job_status = _job_status(payload)
    progress = job_status.get("progress")
    progress = progress if isinstance(progress, dict) else {}
    return (
        job_status.get("state")
        or job_status.get("status")
        or progress.get("stage")
        or payload.get("status")
        or video.get("status")
    )


def _job_detail(payload: dict) -> str | None:
    job_status = _job_status(payload)
    return (
        job_status.get("failedReason")
        or job_status.get("message")
        or payload.get("message")
        or payload.get("error")
    )


def _select_video(video: dict, session_id: str | None = None) -> None:
    st.session_state.selected_video = video
    st.session_state.chat_session_id = session_id
    st.session_state.chat_history = []
    st.session_state.requested_page = "Video chat"


def _video_from_session(session: dict) -> dict:
    video = session.get("video") or session.get("analyzedVideo") or {}
    if not isinstance(video, dict):
        video = {}
    uid = session.get("videoUid") or session.get("video_uid") or session.get("videoId")
    fallback_title = session.get("videoTitle") or session.get("title")
    values = {**video, **({"uid": uid} if uid and not _uid(video) else {})}
    if fallback_title and not values.get("title"):
        values["title"] = fallback_title
    return values


def _matches_library_search(video: dict, query: str, title: str = "") -> bool:
    if not query:
        return True
    searchable = " ".join(
        [
            title,
            *(str(video.get(key, "")) for key in ("title", "name", "channel", "author", "status")),
        ]
    ).lower()
    return query in searchable


def _open_library_item(video: dict, session_id: str | None = None) -> None:
    video_uid = _uid(video)
    if not video_uid:
        st.warning("This item does not include a video identifier in its response.")
        return
    try:
        full_video = client().get_analyzed_video(str(video_uid))
        _select_video(_video(full_video), session_id)
        st.rerun()
    except APIError as error:
        st.error(f"Could not load this analyzed video: {error}")


def _render_video_row(video: dict, index: int) -> None:
    title = str(video.get("title") or video.get("name") or "Untitled video")
    col, metadata, action = st.columns([4, 2, 1])
    with col:
        st.markdown(f"**{title}**")
        st.caption("Analyzed video")
    with metadata:
        st.caption(video.get("channel") or video.get("author") or "Transcript ready")
        st.caption(f"Status: {video.get('status', 'ready')}")
    with action:
        if st.button("Open chat", key=f"open_video_{index}"):
            _open_library_item(video)


def _render_session_row(session: dict, index: int) -> None:
    video = _video_from_session(session)
    session_id = str(session.get("id") or session.get("sessionId") or "") or None
    title = str(session.get("title") or session.get("name") or "Untitled conversation")
    video_title = str(video.get("title") or video.get("name") or "Linked analyzed video")
    col, metadata, action = st.columns([4, 2, 1])
    with col:
        st.markdown(f"**{title}**")
        st.caption(f"Video: {video_title}")
    with metadata:
        st.caption("Saved conversation")
        created_at = session.get("updatedAt") or session.get("createdAt")
        if created_at:
            st.caption(f"Last updated: {created_at}")
    with action:
        if st.button("Open chat", key=f"open_session_{index}"):
            _open_library_item(video, session_id)


def _library() -> None:
    st.subheader("Your video library")
    try:
        videos = client().list_analyzed_videos()
    except APIError as error:
        # Some deployments intentionally expose videos only through sessions.
        videos = []
        st.caption(f"Video library unavailable: {error}")
    try:
        sessions = client().list_sessions()
    except APIError as error:
        sessions = []
        st.warning(f"Could not load chat sessions: {error}")

    if not videos and not sessions:
        st.info("Your analyzed videos and chat sessions will appear here.")
        return
    ready_count = sum(
        str(video.get("status", "")).lower()
        in {"ready", "completed", "processed", "success"}
        for video in videos
    )
    summary = st.columns(3)
    with summary[0]:
        metric_card("Videos", str(len(videos)), "Available to this account")
    with summary[1]:
        metric_card("Conversations", str(len(sessions)), "Saved chat sessions")
    with summary[2]:
        metric_card("Ready to ask", str(ready_count), "Processed transcripts")
    search = st.text_input("Search your library", placeholder="Filter by title, channel, or status")
    query = search.strip().lower()
    filtered_videos = [video for video in videos if _matches_library_search(video, query)]
    filtered_sessions = [
        session
        for session in sessions
        if _matches_library_search(
            _video_from_session(session),
            query,
            str(session.get("title") or session.get("name") or ""),
        )
    ]
    if query and not filtered_videos and not filtered_sessions:
        st.info("No videos match that search.")
        return

    st.markdown("### Analyzed videos")
    if filtered_videos:
        for index, video in enumerate(filtered_videos):
            _render_video_row(video, index)
    else:
        st.caption("No analyzed videos match this search.")

    st.divider()
    st.markdown("### Chat sessions")
    if filtered_sessions:
        for index, session in enumerate(filtered_sessions):
            _render_session_row(session, index)
    else:
        st.caption("No chat sessions match this search.")


def render() -> None:
    st.markdown(
        "<div class='eyebrow'>Workspace</div><h1>Turn any video into an answerable knowledge source.</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='muted'>Paste a public YouTube or Instagram link. We’ll extract context and prepare a grounded chat.</p>",
        unsafe_allow_html=True,
    )
    with st.form("analyze", clear_on_submit=True):
        url = st.text_input(
            "Video URL", placeholder="https://www.youtube.com/watch?v=…"
        )
        submitted = st.form_submit_button("Analyze video", use_container_width=True)
    if submitted:
        if not URL_RE.match(url.strip()):
            st.warning("Enter a valid public YouTube or Instagram URL.")
        else:
            try:
                result = client().analyze_video(url.strip())
                job_id = _job_id(result)
                video = _video(result)
                st.session_state.job_id = job_id
                st.session_state.selected_video = video
                st.session_state.pop("chat_session_id", None)
                st.session_state.chat_history = []
                if not job_id:
                    st.error(
                        "The API accepted the request but did not return a job ID."
                    )
                else:
                    st.success("Analysis started. This page will update automatically.")
            except APIError as error:
                handle_api_error(error)

    job_id = st.session_state.get("job_id")
    if not job_id:
        _library()
        return
    try:
        payload = client().video_status(job_id)
        video = _video(payload)
        # The current backend response stores job state under ``jobStatus``:
        # {jobId, videoId, jobStatus: {state, progress, ...}}.
        # Keep accepting the former top-level ``status`` shape as well.
        status = _job_state(payload, video)
        detail = _job_detail(payload)
        if status:
            video = {**video, "status": status}
        video_uid = _uid(video) or payload.get("videoId")
        if video_uid and not _uid(video):
            video = {**video, "uid": video_uid, "videoId": video_uid}
        st.session_state.selected_video = {
            **st.session_state.get("selected_video", {}),
            **video,
        }
        progress, copy = st.columns([1, 3])
        with progress:
            st.progress(100 if (status or "").lower() in TERMINAL else 45)
        with copy:
            st.caption("Automatic refresh is active while this analysis is running.")
        status_card(status, detail)
        if (status or "").lower() in {"failed", "error"}:
            if st.button("Retry analysis"):
                st.session_state.pop("job_id", None)
                st.rerun()
        elif (status or "").lower() not in TERMINAL:
            with st.spinner("Checking processing status…"):
                time.sleep(2)
            st.rerun()
        else:
            if st.button("Open video chat"):
                # The sidebar radio owns `current_page`; switch it before the next render.
                st.session_state.requested_page = "Video chat"
                st.rerun()
            _library()
    except APIError as error:
        handle_api_error(error)
        if st.button("Retry status check"):
            st.rerun()
