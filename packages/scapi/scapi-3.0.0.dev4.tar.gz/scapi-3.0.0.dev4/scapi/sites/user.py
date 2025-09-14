from __future__ import annotations

import datetime
from enum import Enum
import random
from typing import TYPE_CHECKING, AsyncGenerator, Final

import aiohttp
from ..utils.types import (
    UserPayload,
    UserMessageCountPayload,
    OldUserPayload
)
from ..utils.client import HTTPClient
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    UNKNOWN_TYPE,
    api_iterative,
    dt_from_isoformat,
    _AwaitableContextManager
)
from ..utils.error import ClientError
from ..utils.file import File,_read_file

from ..event.comment import CommentEvent

from .base import _BaseSiteAPI

from .project import (
    Project,
    ProjectFeatured,
)
from .studio import Studio
from .comment import (
    Comment,
    get_comment_from_old
)

if TYPE_CHECKING:
    from .session import Session

class User(_BaseSiteAPI[str]):
    def __repr__(self) -> str:
        return f"<User username:{self.username} id:{self.id} session:{self.session}>"

    def __init__(self,username:str,client_or_session:"HTTPClient|Session|None"=None):
        super().__init__(client_or_session)
        self.username:Final[str] = username
        self.id:MAYBE_UNKNOWN[int] = UNKNOWN

        self._joined_at:MAYBE_UNKNOWN[str] = UNKNOWN

        self.profile_id:MAYBE_UNKNOWN[int] = UNKNOWN
        self.bio:MAYBE_UNKNOWN[str] = UNKNOWN
        self.status:MAYBE_UNKNOWN[str] = UNKNOWN
        self.country:MAYBE_UNKNOWN[str] = UNKNOWN
        self.scratchteam:MAYBE_UNKNOWN[bool] = UNKNOWN

    async def update(self):
        response = await self.client.get(f"https://api.scratch.mit.edu/users/{self.username}")
        self._update_from_data(response.json())

    def _update_from_data(self, data:UserPayload):
        self._update_to_attributes(
            id=data.get("id"),
            scratchteam=data.get("scratchteam")
        )
        _history = data.get("history")
        if _history:
            self._update_to_attributes(_joined_at=_history.get("joined"))
        
        _profile = data.get("profile")
        if _profile:
            self._update_to_attributes(
                profile_id=_profile.get("id"),
                status=_profile.get("status"),
                bio=_profile.get("bio"),
                country=_profile.get("country")
            )

    def _update_from_old_data(self, data:OldUserPayload):
        self._update_to_attributes(
            id=data.get("pk"),
            scratchteam=data.get("admin")
        )
    
    @property
    def joined_at(self) -> datetime.datetime|UNKNOWN_TYPE:
        """
        ユーザーが参加した時間を返す。

        Returns:
            datetime.datetime|UNKNOWN_TYPE: データがある場合、その時間。
        """
        return dt_from_isoformat(self._joined_at)
    

    async def get_featured(self) -> "ProjectFeatured|None":
        """
        ユーザーの注目のプロジェクト欄を取得する。

        Returns:
            ProjectFeatured|None: ユーザーが設定している場合、そのデータ。
        """
        response = await self.client.get(f"https://scratch.mit.edu/site-api/users/all/{self.username}/")
        return ProjectFeatured(response.json(),self)
    
    async def get_followers(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["User", None]:
        """
        ユーザーのフォロワーを取得する。

        Args:
            limit (int|None, optional): 取得するユーザーの数。初期値は40です。
            offset (int|None, optional): 取得するユーザーの開始位置。初期値は0です。

        Yields:
            User: 取得したユーザー
        """
        async for _u in api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/followers/",
            limit=limit,offset=offset
        ):
            yield User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_followings(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["User", None]:
        """
        ユーザーがフォローしているユーザーを取得する。

        Args:
            limit (int|None, optional): 取得するユーザーの数。初期値は40です。
            offset (int|None, optional): 取得するユーザーの開始位置。初期値は0です。

        Yields:
            User: 取得したユーザー
        """
        async for _u in api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/following/",
            limit=limit,offset=offset
        ):
            yield User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_projects(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Project", None]:
        """
        ユーザーが共有しているプロジェクトを取得する。

        Args:
            limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
            offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。

        Yields:
            Project: 取得したプロジェクト
        """
        async for _p in api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/projects/",
            limit=limit,offset=offset
        ):
            yield Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_favorites(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Project", None]:
        """
        ユーザーのお気に入りのプロジェクトを取得する。

        Args:
            limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
            offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。

        Yields:
            Project: 取得したプロジェクト
        """
        async for _p in api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/favorites/",
            limit=limit,offset=offset
        ):
            yield Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_studios(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Studio", None]:
        """
        ユーザーが参加しているスタジオを取得する。

        Args:
            limit (int|None, optional): 取得するスタジオの数。初期値は40です。
            offset (int|None, optional): 取得するスタジオの開始位置。初期値は0です。

        Yields:
            Studio: 取得したスタジオ
        """
        async for _s in api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/studios/curate",
            limit=limit,offset=offset
        ):
            yield Studio._create_from_data(_s["id"],_s,self.client_or_session)

    async def get_message_count(self) -> int:
        """
        ユーザーのメッセージの未読数を取得する。

        Returns:
            int: 未読のメッセージの数
        """
        response = await self.client.get(
            f"https://api.scratch.mit.edu/users/{self.username}/messages/count/",
            params={"cachebust":str(random.randint(0,10000))}
        )
        data:UserMessageCountPayload = response.json()
        return data.get("count")

    def get_comments(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator["Comment", None]:
        """
        プロフィールに投稿されたコメントを取得する。

        Args:
            start_page (int|None, optional): 取得するコメントの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するコメントの終了ページ位置。初期値はstart_pageの値です。

        Returns:
            Comment: 取得したコメント
        """
        return get_comment_from_old(self,start_page,end_page)
    
    get_comments_from_old = get_comments

    def comment_event(self,interval:int=30,is_old:bool=False) -> CommentEvent:
        """
        コメントイベントを作成する。

        Args:
            interval (int, optional): コメントの更新間隔。デフォルトは30秒です。
            is_old (bool, optional): 古いAPIから取得するか。デフォルトはFalseです。

        Returns:
            CommentEvent:
        """
        return CommentEvent(self,interval,is_old)


    async def post_comment(
        self,content:str,
        parent:"Comment|int|None"=None,commentee:"User|int|None"=None,
        is_old:bool=True
    ) -> "Comment":
        """
        コメントを投稿します。

        Args:
            content (str): コメントの内容
            parent (Comment|int|None, optional): 返信する場合、返信元のコメントかID
            commentee (User|int|None, optional): メンションする場合、ユーザーかそのユーザーのID
            is_old (bool, optional): 古いAPIを使用して送信するか この値は使用されず、常に古いAPIが使用されます。

        Returns:
            Comment: 投稿されたコメント
        """
        return await Comment.post_comment(self,content,parent,commentee,is_old)
    
    async def follow(self):
        """
        ユーザーをフォローする
        """
        self.require_session()
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/followers/{self.username}/add/",
            params={"usernames":self._session.username}
        )

    async def unfollow(self):
        """
        ユーザーのフォローを解除する
        """
        self.require_session()
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/followers/{self.username}/remove/",
            params={"usernames":self._session.username}
        )


    async def edit(
            self,*,
            bio:str|None=None,
            status:str|None=None,
            featured_project_id:"int|Project|None"=None,
            featured_project_label:"ProjectFeaturedLabel|None"=None
        ) -> "None | ProjectFeatured":
        """
        プロフィール欄を編集する。

        Args:
            bio (str | None, optional): 私について欄の内容
            status (str | None, optional): 私が取り組んでいることの内容
            featured_project_id (int|Project|None, optional): 注目のプロジェクト欄に設定したいプロジェクトかそのID
            featured_project_label (ProjectFeaturedLabel|None, optional): 注目のプロジェクト欄に使用したいラベル

        Returns:
            None | ProjectFeatured: 変更された注目のプロジェクト欄
        """
        self.require_session()
        _data = {}
        if isinstance(featured_project_id,Project):
            featured_project_id = featured_project_id.id
        if bio is not None: _data["bio"] = bio
        if status is not None: _data["status"] = status
        if featured_project_id is not None: _data["featured_project"] = featured_project_id
        if featured_project_label is not None: _data["featured_project_label"] = featured_project_label.value

        response = await self.client.put(f"https://scratch.mit.edu/site-api/users/all/{self.username}/",json=_data)
        data = response.json()
        if data.get("errors"):
            raise ClientError(response,data.get("errors"))
        return ProjectFeatured(data,self)

    async def toggle_comment(self):
        """
        プロフィールのコメント欄を開閉する。
        """
        self.require_session()
        await self.client.post(f"https://scratch.mit.edu/site-api/comments/user/{self.username}/toggle-comments/")

    async def set_icon(self,icon:File|bytes):
        """
        アイコンを変更する。

        Args:
            icon (file.File | bytes): アイコンのデータ
        """
        self.require_session()
        async with _read_file(icon) as f:
            self.require_session()
            await self.client.post(
                f"https://scratch.mit.edu/site-api/users/all/{self.id}/",
                data=aiohttp.FormData({"file":f})
            )


class ProjectFeaturedLabel(Enum):
    """
    注目のプロジェクト欄のラベルを表す。
    """
    ProjectFeatured=""
    Tutorial="0"
    WorkInProgress="1"
    RemixThis="2"
    MyFavoriteThings="3"
    WhyIScratch="4"

    @classmethod
    def get_from_id(cls,id:int|None) -> "ProjectFeaturedLabel":
        if id is None:
            return cls.ProjectFeatured
        _id = str(id)
        for item in cls:
            if item.value == _id:
                return item
        raise ValueError()

def get_user(username:str,*,_client:HTTPClient|None=None) -> _AwaitableContextManager[User]:
    """
    ユーザーを取得する。

    Args:
        username (str): 取得したいユーザーのユーザー名

    Returns:
        _AwaitableContextManager[Studio]: await か async with で取得できるユーザー
    """
    return _AwaitableContextManager(User._create_from_api(username,_client))