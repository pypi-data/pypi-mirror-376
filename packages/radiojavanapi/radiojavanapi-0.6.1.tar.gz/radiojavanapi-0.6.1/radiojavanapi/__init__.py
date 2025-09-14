import json
from radiojavanapi.mixins.song import SongMixin
from radiojavanapi.mixins.album import AlbumMixin
from radiojavanapi.mixins.story import StoryMixin
from radiojavanapi.mixins.browse import BrowseMixin
from radiojavanapi.mixins.playlist import MusicPlayListMixin, VideoPlayListMixin
from radiojavanapi.mixins.podcast import PodcastMixin
from radiojavanapi.mixins.video import VideoMixin
from radiojavanapi.mixins.account import AccountMixin

class Client(
            AccountMixin,
            VideoMixin,
            SongMixin,
            PodcastMixin,
            BrowseMixin,
            VideoPlayListMixin,
            MusicPlayListMixin,
            StoryMixin,
            AlbumMixin
            ):
    """
    Class used to access all features, this is the only class that 
    needs to be imported (along with the exceptions)
    """
        
    def set_proxy(self, proxy:dict) -> None:
        assert isinstance(proxy, dict), f'Proxy must been Dict, but now "{proxy}" ({type(proxy)})'
        self.private.proxies = self.proxy = proxy

    def unset_proxy(self) -> None:
        self.private.proxies = self.proxy = None
        
    def save_session(self, path: str) -> bool:
        with open(path, 'w') as wf:
            json.dump({
                'cookie': self.cookie,
                'email': self.email
                }, wf, indent=4)
        return True
    
    def load_session(self, path: str) -> bool:
        with open(path, 'r') as rf:
            json_data = json.load(rf)
            self.initial()
            self.authorized = True
            self.cookie = json_data['cookie']
            self.email = json_data['email']
            self.private.headers.update({'Cookie': self.cookie})
        return True 