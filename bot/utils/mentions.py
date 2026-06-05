from typing import Optional


def format_mention(user_id: int, username: Optional[str]) -> str:
    if username:
        return f"@{username}"
    return f"<a href='tg://user?id={user_id}'>{user_id}</a>"


def format_mentions(users: list[tuple[int, Optional[str]]]) -> str:
    if not users:
        return "никто"
    return ", ".join(format_mention(uid, uname) for uid, uname in users)