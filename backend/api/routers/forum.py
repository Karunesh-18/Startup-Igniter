"""
Forum router — community discussion board.

Endpoints:
  GET    /forum/posts               List posts (paginated, filterable)
  POST   /forum/posts               Create a post
  GET    /forum/posts/{post_id}     Get post with comments
  PATCH  /forum/posts/{post_id}     Edit post (author only)
  DELETE /forum/posts/{post_id}     Soft-delete post (author only)

  POST   /forum/posts/{post_id}/vote        Upvote or downvote a post
  POST   /forum/posts/{post_id}/comments    Add a comment
  DELETE /forum/comments/{comment_id}       Soft-delete a comment

Design notes:
- Soft deletes (is_deleted=True) — never hard-delete forum content.
- Vote toggling: voting the same way removes the vote (toggle off).
- Pagination: limit/offset for v1 (cursor pagination in v2).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import CurrentUser, DB
from db.models import ForumComment, ForumPost, ForumVote, User

router = APIRouter(prefix="/forum", tags=["Forum"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class PostCreate(BaseModel):
    title: str = Field(min_length=5, max_length=500)
    body: str = Field(min_length=10)
    tags: list[str] | None = None
    project_id: str | None = None

    model_config = {"json_schema_extra": {"example": {
        "title": "How do I get DPIIT recognition for my EdTech startup?",
        "body": "I've been trying to apply on the Startup India portal but keep getting errors...",
        "tags": ["legal", "dpiit", "edtech"],
    }}}


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=500)
    body: str | None = Field(default=None, min_length=10)
    tags: list[str] | None = None


class PostSummary(BaseModel):
    id: str
    title: str
    author_name: str
    author_id: str
    tags: list[str] | None
    upvotes: int
    downvotes: int
    comment_count: int
    created_at: str


class CommentResponse(BaseModel):
    id: str
    author_name: str
    author_id: str
    body: str
    parent_id: str | None
    upvotes: int
    created_at: str


class PostDetail(PostSummary):
    body: str
    project_id: str | None
    comments: list[CommentResponse]


class VoteRequest(BaseModel):
    vote_type: str = Field(pattern="^(up|down)$")


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)
    parent_id: str | None = None


class VoteResponse(BaseModel):
    post_id: str
    upvotes: int
    downvotes: int
    user_vote: str | None  # "up", "down", or None


# ── Posts ─────────────────────────────────────────────────────────────────────


@router.get(
    "/posts",
    response_model=list[PostSummary],
    summary="List forum posts",
)
async def list_posts(
    current_user: CurrentUser,
    db: DB,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tag: str | None = Query(default=None),
) -> list[PostSummary]:
    """
    Return paginated forum posts, newest first.

    Optionally filter by tag (exact match on JSON array element).
    """
    query = (
        select(ForumPost, User, func.count(ForumComment.id).label("comment_count"))
        .join(User, User.id == ForumPost.author_id)
        .outerjoin(ForumComment, ForumComment.post_id == ForumPost.id)
        .where(ForumPost.is_deleted == False)  # noqa: E712
        .group_by(ForumPost.id, User.id)
        .order_by(ForumPost.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    rows = result.all()

    summaries = []
    for post, author, comment_count in rows:
        tags = list(post.tags) if post.tags else None
        if tag and (not tags or tag not in tags):
            continue
        summaries.append(PostSummary(
            id=str(post.id),
            title=post.title,
            author_name=author.name,
            author_id=str(author.id),
            tags=tags,
            upvotes=post.upvotes,
            downvotes=post.downvotes,
            comment_count=comment_count or 0,
            created_at=post.created_at.isoformat(),
        ))

    return summaries


@router.post(
    "/posts",
    response_model=PostDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a forum post",
)
async def create_post(
    body: PostCreate,
    current_user: CurrentUser,
    db: DB,
) -> PostDetail:
    post = ForumPost(
        id=uuid.uuid4(),
        author_id=current_user.id,
        project_id=uuid.UUID(body.project_id) if body.project_id else None,
        title=body.title,
        body=body.body,
        tags=body.tags,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return PostDetail(
        id=str(post.id),
        title=post.title,
        body=post.body,
        author_name=current_user.name,
        author_id=str(current_user.id),
        tags=list(post.tags) if post.tags else None,
        upvotes=0,
        downvotes=0,
        comment_count=0,
        project_id=body.project_id,
        comments=[],
        created_at=post.created_at.isoformat(),
    )


@router.get(
    "/posts/{post_id}",
    response_model=PostDetail,
    summary="Get a post with comments",
)
async def get_post(
    post_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> PostDetail:
    result = await db.execute(
        select(ForumPost, User)
        .join(User, User.id == ForumPost.author_id)
        .where(ForumPost.id == post_id, ForumPost.is_deleted == False)  # noqa: E712
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found.")

    post, author = row

    # Load comments
    comments_result = await db.execute(
        select(ForumComment, User)
        .join(User, User.id == ForumComment.author_id)
        .where(ForumComment.post_id == post_id, ForumComment.is_deleted == False)  # noqa: E712
        .order_by(ForumComment.created_at.asc())
    )
    comment_rows = comments_result.all()

    comments = [
        CommentResponse(
            id=str(c.id),
            author_name=u.name,
            author_id=str(u.id),
            body=c.body,
            parent_id=str(c.parent_id) if c.parent_id else None,
            upvotes=c.upvotes,
            created_at=c.created_at.isoformat(),
        )
        for c, u in comment_rows
    ]

    return PostDetail(
        id=str(post.id),
        title=post.title,
        body=post.body,
        author_name=author.name,
        author_id=str(author.id),
        tags=list(post.tags) if post.tags else None,
        upvotes=post.upvotes,
        downvotes=post.downvotes,
        comment_count=len(comments),
        project_id=str(post.project_id) if post.project_id else None,
        comments=comments,
        created_at=post.created_at.isoformat(),
    )


@router.patch(
    "/posts/{post_id}",
    response_model=PostDetail,
    summary="Edit a forum post",
)
async def edit_post(
    post_id: uuid.UUID,
    body: PostUpdate,
    current_user: CurrentUser,
    db: DB,
) -> PostDetail:
    result = await db.execute(
        select(ForumPost).where(ForumPost.id == post_id, ForumPost.is_deleted == False)  # noqa: E712
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the author can edit this post.")

    if body.title:
        post.title = body.title  # type: ignore
    if body.body:
        post.body = body.body  # type: ignore
    if body.tags is not None:
        post.tags = body.tags  # type: ignore

    db.add(post)
    await db.commit()

    return await get_post(post_id, current_user, db)


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a forum post",
)
async def delete_post(
    post_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> None:
    result = await db.execute(select(ForumPost).where(ForumPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the author can delete this post.")

    post.is_deleted = True  # type: ignore[assignment]
    db.add(post)
    await db.commit()


# ── Votes ─────────────────────────────────────────────────────────────────────


@router.post(
    "/posts/{post_id}/vote",
    response_model=VoteResponse,
    summary="Vote on a forum post",
)
async def vote_post(
    post_id: uuid.UUID,
    body: VoteRequest,
    current_user: CurrentUser,
    db: DB,
) -> VoteResponse:
    """
    Toggle-vote on a post.

    - Voting the same type twice removes the vote.
    - Switching vote type updates it.
    - Post upvote/downvote counters are updated atomically.
    """
    # Load post
    post_result = await db.execute(select(ForumPost).where(ForumPost.id == post_id))
    post = post_result.scalar_one_or_none()
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="Post not found.")

    # Load existing vote
    vote_result = await db.execute(
        select(ForumVote).where(
            ForumVote.post_id == post_id, ForumVote.user_id == current_user.id
        )
    )
    existing_vote = vote_result.scalar_one_or_none()

    if existing_vote:
        if existing_vote.vote_type == body.vote_type:
            # Same vote — remove it (toggle off)
            if body.vote_type == "up":
                post.upvotes = max(0, post.upvotes - 1)  # type: ignore
            else:
                post.downvotes = max(0, post.downvotes - 1)  # type: ignore
            await db.delete(existing_vote)
            user_vote = None
        else:
            # Switch vote
            if existing_vote.vote_type == "up":
                post.upvotes = max(0, post.upvotes - 1)  # type: ignore
                post.downvotes += 1  # type: ignore
            else:
                post.downvotes = max(0, post.downvotes - 1)  # type: ignore
                post.upvotes += 1  # type: ignore
            existing_vote.vote_type = body.vote_type  # type: ignore[assignment]
            db.add(existing_vote)
            user_vote = body.vote_type
    else:
        # New vote
        new_vote = ForumVote(
            id=uuid.uuid4(),
            post_id=post_id,
            user_id=current_user.id,
            vote_type=body.vote_type,  # type: ignore[arg-type]
        )
        db.add(new_vote)
        if body.vote_type == "up":
            post.upvotes += 1  # type: ignore
        else:
            post.downvotes += 1  # type: ignore
        user_vote = body.vote_type

    db.add(post)
    await db.commit()

    return VoteResponse(
        post_id=str(post_id),
        upvotes=post.upvotes,
        downvotes=post.downvotes,
        user_vote=user_vote,
    )


# ── Comments ──────────────────────────────────────────────────────────────────


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a post",
)
async def add_comment(
    post_id: uuid.UUID,
    body: CommentCreate,
    current_user: CurrentUser,
    db: DB,
) -> CommentResponse:
    post_result = await db.execute(
        select(ForumPost).where(ForumPost.id == post_id, ForumPost.is_deleted == False)  # noqa: E712
    )
    post = post_result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    comment = ForumComment(
        id=uuid.uuid4(),
        post_id=post_id,
        author_id=current_user.id,
        parent_id=uuid.UUID(body.parent_id) if body.parent_id else None,
        body=body.body,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentResponse(
        id=str(comment.id),
        author_name=current_user.name,
        author_id=str(current_user.id),
        body=comment.body,
        parent_id=str(comment.parent_id) if comment.parent_id else None,
        upvotes=0,
        created_at=comment.created_at.isoformat(),
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a comment",
)
async def delete_comment(
    comment_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> None:
    result = await db.execute(
        select(ForumComment).where(ForumComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the author can delete this comment.")

    comment.is_deleted = True  # type: ignore[assignment]
    db.add(comment)
    await db.commit()
