import base64
import json
import logging
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import httpx

from dhisana.schemas.common import (
    SendEmailContext,
    QueryEmailContext,
    ReplyEmailContext,
)
from dhisana.schemas.sales import MessageItem
from dhisana.utils.email_parse_helpers import (
    find_header,
    parse_single_address,
    find_all_recipients_in_headers,
    convert_date_to_iso,
    extract_email_body_in_plain_text,
)


def get_google_access_token(tool_config: Optional[List[Dict]] = None) -> str:
    """
    Retrieve a Google OAuth2 access token from the 'google' integration config.

    Expected tool_config shape:
        {
          "name": "google",
          "configuration": [
            {"name": "oauth_tokens", "value": {"access_token": "..."} }
            # or {"name": "access_token", "value": "..."}
          ]
        }

    If provided as a JSON string under oauth_tokens, it is parsed.
    """
    access_token: Optional[str] = None

    if tool_config:
        g_cfg = next((c for c in tool_config if c.get("name") == "google"), None)
        if g_cfg:
            cfg_map = {f["name"]: f.get("value") for f in g_cfg.get("configuration", []) if f}
            raw_oauth = cfg_map.get("oauth_tokens")
            # oauth_tokens might be a JSON string or a dict
            if isinstance(raw_oauth, str):
                try:
                    raw_oauth = json.loads(raw_oauth)
                except Exception:
                    raw_oauth = None
            if isinstance(raw_oauth, dict):
                access_token = raw_oauth.get("access_token") or raw_oauth.get("token")
            if not access_token:
                access_token = cfg_map.get("access_token")

    if not access_token:
        raise ValueError(
            "Google integration is not configured. Please connect Google and supply an OAuth access token."
        )
    return access_token


async def send_email_using_google_oauth_async(
    send_email_context: SendEmailContext,
    tool_config: Optional[List[Dict]] = None,
) -> str:
    """
    Send an email using Gmail API with a per-user OAuth2 token.

    Returns the Gmail message id of the sent message when available.
    """
    token = get_google_access_token(tool_config)

    message = MIMEText(send_email_context.body, _subtype="html")
    message["to"] = send_email_context.recipient
    message["from"] = f"{send_email_context.sender_name} <{send_email_context.sender_email}>"
    message["subject"] = send_email_context.subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    payload: Dict[str, Any] = {"raw": raw_message}
    if send_email_context.labels:
        payload["labelIds"] = send_email_context.labels

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json() or {}
        return data.get("id", "")


async def list_emails_in_time_range_google_oauth_async(
    context: QueryEmailContext,
    tool_config: Optional[List[Dict]] = None,
) -> List[MessageItem]:
    """
    List Gmail messages for the connected user in a time range using OAuth2.
    Returns a list of MessageItem.
    """
    if context.labels is None:
        context.labels = []

    token = get_google_access_token(tool_config)
    base_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
    headers = {"Authorization": f"Bearer {token}"}

    # Convert RFC3339 times to unix timestamps for Gmail search query
    # Expecting context.start_time and context.end_time as ISO 8601; Gmail q uses epoch seconds
    from datetime import datetime
    start_dt = datetime.fromisoformat(context.start_time.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(context.end_time.replace("Z", "+00:00"))
    after_ts = int(start_dt.timestamp())
    before_ts = int(end_dt.timestamp())

    q_parts: List[str] = [f"after:{after_ts}", f"before:{before_ts}"]
    if context.unread_only:
        q_parts.append("is:unread")
    if context.labels:
        q_parts.extend([f"label:{lbl}" for lbl in context.labels])
    query = " ".join(q_parts)

    params = {"q": query}

    items: List[MessageItem] = []
    async with httpx.AsyncClient(timeout=30) as client:
        list_resp = await client.get(base_url, headers=headers, params=params)
        list_resp.raise_for_status()
        list_data = list_resp.json() or {}
        for m in list_data.get("messages", []) or []:
            mid = m.get("id")
            tid = m.get("threadId")
            if not mid:
                continue
            get_url = f"{base_url}/{mid}"
            get_resp = await client.get(get_url, headers=headers)
            get_resp.raise_for_status()
            mdata = get_resp.json() or {}

            headers_list = (mdata.get("payload") or {}).get("headers", [])
            from_header = find_header(headers_list, "From") or ""
            subject_header = find_header(headers_list, "Subject") or ""
            date_header = find_header(headers_list, "Date") or ""

            iso_dt = convert_date_to_iso(date_header)
            s_name, s_email = parse_single_address(from_header)
            r_name, r_email = find_all_recipients_in_headers(headers_list)

            items.append(
                MessageItem(
                    message_id=mdata.get("id", ""),
                    thread_id=tid or "",
                    sender_name=s_name,
                    sender_email=s_email,
                    receiver_name=r_name,
                    receiver_email=r_email,
                    iso_datetime=iso_dt,
                    subject=subject_header,
                    body=extract_email_body_in_plain_text(mdata),
                )
            )

    return items


async def reply_to_email_google_oauth_async(
    reply_email_context: ReplyEmailContext,
    tool_config: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Reply-all to a Gmail message for the connected user using OAuth2.
    Returns a metadata dictionary similar to other providers.
    """
    if reply_email_context.add_labels is None:
        reply_email_context.add_labels = []

    token = get_google_access_token(tool_config)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base = "https://gmail.googleapis.com/gmail/v1/users/me"

    # 1) Fetch original message
    get_url = f"{base}/messages/{reply_email_context.message_id}"
    params = {"format": "full"}
    async with httpx.AsyncClient(timeout=30) as client:
        get_resp = await client.get(get_url, headers=headers, params=params)
        get_resp.raise_for_status()
        original = get_resp.json() or {}

    headers_list = (original.get("payload") or {}).get("headers", [])
    headers_map = {h.get("name"): h.get("value") for h in headers_list if isinstance(h, dict)}
    thread_id = original.get("threadId")

    subject = headers_map.get("Subject", "") or ""
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"
    to_addresses = headers_map.get("From", "") or ""
    cc_addresses = headers_map.get("Cc", "") or ""
    message_id_header = headers_map.get("Message-ID", "") or ""

    # 2) Build reply MIME
    msg = MIMEText(reply_email_context.reply_body, _subtype="html")
    msg["To"] = to_addresses
    if cc_addresses:
        msg["Cc"] = cc_addresses
    msg["From"] = f"{reply_email_context.sender_name} <{reply_email_context.sender_email}>"
    msg["Subject"] = subject
    if message_id_header:
        msg["In-Reply-To"] = message_id_header
        msg["References"] = message_id_header

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload = {"raw": raw_message}
    if thread_id:
        payload["threadId"] = thread_id

    # 3) Send the reply
    send_url = f"{base}/messages/send"
    async with httpx.AsyncClient(timeout=30) as client:
        send_resp = await client.post(send_url, headers=headers, json=payload)
        send_resp.raise_for_status()
        sent = send_resp.json() or {}

    # 4) Optional: mark as read
    if str(reply_email_context.mark_as_read).lower() == "true" and thread_id:
        modify_url = f"{base}/threads/{thread_id}/modify"
        modify_payload = {"removeLabelIds": ["UNREAD"]}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(modify_url, headers=headers, json=modify_payload)
        except Exception:
            logging.exception("Gmail: failed to mark thread as read (best-effort)")

    # 5) Optional: add labels
    if reply_email_context.add_labels and thread_id:
        modify_url = f"{base}/threads/{thread_id}/modify"
        modify_payload = {"addLabelIds": reply_email_context.add_labels}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(modify_url, headers=headers, json=modify_payload)
        except Exception:
            logging.exception("Gmail: failed to add labels to thread (best-effort)")

    return {
        "mailbox_email_id": sent.get("id"),
        "message_id": (sent.get("threadId") or thread_id or ""),
        "email_subject": subject,
        "email_sender": reply_email_context.sender_email,
        "email_recipients": [to_addresses] + ([cc_addresses] if cc_addresses else []),
        "read_email_status": "READ" if str(reply_email_context.mark_as_read).lower() == "true" else "UNREAD",
        "email_labels": sent.get("labelIds", []),
    }

