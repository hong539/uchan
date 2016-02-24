from uchan import g
from uchan.lib.cache import CacheDict, LocalCache


class AllBoardsCacheProxy(CacheDict):
    """Object to be memcached, contains a list of all boards, where each board is s BaordCacheProxy, containing only board info"""

    def __init__(self, boards):
        super().__init__()
        self.boards = boards


class BoardCacheProxy(CacheDict):
    def __init__(self, board):
        super().__init__()
        self.name = board.name


class BoardConfigCacheProxy(CacheDict):
    def __init__(self, board_config):
        super().__init__()
        self.board_config = board_config


class BoardCache:
    """
    Cache for all things board related.
    Anything related to posts (so the board pages and catalog) are in the PostsCache
    """

    def __init__(self, cache):
        self.cache = cache
        self.local_cache = LocalCache()

    def find_board_config_cached(self, board_name):
        key = self.get_board_config_key(board_name)

        local_cached = self.local_cache.get(key)
        if local_cached is not None:
            return local_cached

        board_config_cache = self.cache.get(key, True)
        if board_config_cache is None:
            board = g.board_service.find_board(board_name)
            if not board:
                return None

            config = g.config_service.load_config_dict(board.config)
            board_config_cache = BoardConfigCacheProxy(config).convert()
            self.cache.set(key, board_config_cache)

        if board_config_cache is not None:
            self.local_cache.set(key, board_config_cache)

        return board_config_cache

    def get_board_config_key(self, board_name):
        return 'board_config_{}'.format(board_name)

    def invalidate_board_config(self, board_name):
        self.cache.delete(self.get_board_config_key(board_name))

    def all_boards(self):
        key = 'all_boards'

        local_cached = self.local_cache.get(key)
        if local_cached is not None:
            return local_cached

        all_boards_cache = self.cache.get(key, True)
        if not all_boards_cache:
            all_boards = g.board_service.get_all_boards()
            all_boards_cache = AllBoardsCacheProxy([BoardCacheProxy(i).convert() for i in all_boards]).convert()
            self.cache.set(key, all_boards_cache, timeout=3600)

        if all_boards_cache is not None:
            self.local_cache.set(key, all_boards_cache)

        return all_boards_cache

    def invalidate_all_boards(self):
        key = 'all_boards'
        self.cache.delete(key)
