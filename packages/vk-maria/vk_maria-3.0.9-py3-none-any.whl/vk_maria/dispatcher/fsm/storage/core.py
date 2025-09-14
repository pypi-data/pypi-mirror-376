import typing
from abc import ABC, abstractmethod

from loguru import logger

from ....types import Chat
from ....mixins import Singleton


class BaseStorage(ABC):

    @abstractmethod
    def close(self):
        pass

    @classmethod
    def check_address(cls, *,
                      chat: typing.Union[str, int, None] = None,
                      user: typing.Union[str, int, None] = None
                      ) -> (typing.Union[str, int], typing.Union[str, int]):

        if chat is None and user is None:
            raise ValueError('`user` or `chat` parameter is required but no one is provided!')

        if user is None:
            user = chat

        elif chat is None:
            chat = user

        return chat, user

    @abstractmethod
    def get_state(self, *,
                  chat: typing.Union[str, int, None] = None,
                  user: typing.Union[str, int, None] = None,
                  default: typing.Optional[str] = None) -> typing.Optional[str]:
        pass

    @abstractmethod
    def get_data(self, *,
                 chat: typing.Union[str, int, None] = None,
                 user: typing.Union[str, int, None] = None,
                 default: typing.Optional[str] = None) -> typing.Dict:
        pass

    @abstractmethod
    def set_state(self, *,
                  chat: typing.Union[str, int, None] = None,
                  user: typing.Union[str, int, None] = None,
                  state: typing.Optional[typing.AnyStr] = None):
        pass

    @abstractmethod
    def set_data(self, *,
                 chat: typing.Union[str, int, None] = None,
                 user: typing.Union[str, int, None] = None,
                 data: typing.Dict = None):
        pass

    @abstractmethod
    def update_data(self, *,
                    chat: typing.Union[str, int, None] = None,
                    user: typing.Union[str, int, None] = None,
                    data: typing.Dict = None,
                    **kwargs):
        pass

    def reset_data(self, *,
                   chat: typing.Union[str, int, None] = None,
                   user: typing.Union[str, int, None] = None):
        self.set_data(chat=chat, user=user, data={})

    def reset_state(self, *,
                    chat: typing.Union[str, int, None] = None,
                    user: typing.Union[str, int, None] = None,
                    with_data: typing.Optional[bool] = True):
        chat, user = self.check_address(chat=chat, user=user)
        self.set_state(chat=chat, user=user, state=None)
        if with_data:
            self.set_data(chat=chat, user=user, data={})

    def finish(self, *,
               chat: typing.Union[str, int, None] = None,
               user: typing.Union[str, int, None] = None,
               with_data: bool = False):
        self.reset_state(chat=chat, user=user, with_data=with_data)


class FSMContext(Singleton):
    def __init__(self, storage: BaseStorage):
        self.storage: BaseStorage = storage

    def get_state(self, default: typing.Optional[str] = None) -> typing.Optional[str]:
        return self.storage.get_state(chat=Chat.get_chat_id(), user=Chat.get_user_id(), default=default)

    def get_data(self, default: typing.Optional[str] = None) -> typing.Dict:
        return self.storage.get_data(chat=Chat.get_chat_id(), user=Chat.get_user_id(), default=default)

    def update_data(self, data: typing.Dict = None, **kwargs):
        self.storage.update_data(chat=Chat.get_chat_id(), user=Chat.get_user_id(), data=data, **kwargs)

    def set_state(self, state: typing.Optional[typing.AnyStr] = None):
        self.storage.set_state(chat=Chat.get_chat_id(), user=Chat.get_user_id(), state=state)

    def set_data(self, data: typing.Dict = None):
        self.storage.set_data(chat=Chat.get_chat_id(), user=Chat.get_user_id(), data=data)

    def reset_state(self, with_data: typing.Optional[bool] = True):
        self.storage.reset_state(chat=Chat.get_chat_id(), user=Chat.get_user_id(), with_data=with_data)

    def reset_data(self):
        self.storage.reset_data(chat=Chat.get_chat_id(), user=Chat.get_user_id(), )

    def finish(self, with_data: bool = False):
        self.storage.finish(chat=Chat.get_chat_id(), user=Chat.get_user_id(), with_data=with_data)


class DisabledStorage(BaseStorage):

    def close(self):
        pass

    def get_state(self, *,
                  chat: typing.Union[str, int, None] = None,
                  user: typing.Union[str, int, None] = None,
                  default: typing.Optional[str] = None) -> typing.Optional[str]:
        return None

    def get_data(self, *,
                 chat: typing.Union[str, int, None] = None,
                 user: typing.Union[str, int, None] = None,
                 default: typing.Optional[str] = None) -> typing.Dict:
        self._warning()
        return {}

    def update_data(self, *,
                    chat: typing.Union[str, int, None] = None,
                    user: typing.Union[str, int, None] = None,
                    data: typing.Dict = None,
                    **kwargs):
        self._warning()

    def set_state(self, *,
                  chat: typing.Union[str, int, None] = None,
                  user: typing.Union[str, int, None] = None,
                  state: typing.Optional[typing.AnyStr] = None):
        self._warning()

    def set_data(self, *,
                 chat: typing.Union[str, int, None] = None,
                 user: typing.Union[str, int, None] = None,
                 data: typing.Dict = None):
        self._warning()

    def _warning(self):
        logger.warning('Вы не указали хранилище состояний')
