import asyncio
import base64
import logging
import time
from concurrent.futures import ThreadPoolExecutor

import transmissionrpc

from alcazar_logging import BraceAdapter
from transmission.params import TRANSMISSION_FETCH_ARGS
from utils import timezone_now

logger = BraceAdapter(logging.getLogger(__name__))


class TransmissionAsyncExecutor:
    def __init__(self, host, port, username, password):
        self._host = host
        self._port = port
        self._username = username
        self._password = password

        self._thread_pool = ThreadPoolExecutor(2, 'transmission@{}:{}'.format(host, port))
        self._client = None

    def _obtain_client(self):
        logger.debug('Trying to obtain client for {}:{}', self._host, self._port)
        self._client = transmissionrpc.Client(
            address=self._host,
            port=self._port,
            user=self._username,
            password=self._password,
            timeout=60,
        )
        logger.debug('Obtained client for {}:{}', self._host, self._port)

    def _ensure_client(self, datetime_deadline):
        if self._client:
            return

        while True:
            try:
                self._obtain_client()
                break
            except transmissionrpc.TransmissionError:
                if timezone_now() > datetime_deadline:
                    raise
                time.sleep(1)

    async def ensure_client(self, deadline):
        return await asyncio.wrap_future(self._thread_pool.submit(self._ensure_client, deadline))

    def _fetch_torrents(self, ids):
        logger.debug('Fetching torrents from {}:{}', self._host, self._port)
        return self._client.get_torrents(ids=ids, arguments=TRANSMISSION_FETCH_ARGS)

    async def fetch_torrents(self, ids):
        return await asyncio.wrap_future(self._thread_pool.submit(self._fetch_torrents, ids))

    def _add_torrent(self, torrent_file, download_path, name):
        logger.debug('Adding torrent to {}:{}', self._host, self._port)
        base64_torrent = base64.b64encode(torrent_file).decode()
        if name is not None:
            # Need to rename the torrent as specified in the request
            bootstrap_t_torrent = self._client.add_torrent(
                base64_torrent,
                download_dir=download_path,
                paused=True,
            )
            self._client.rename_torrent_path(
                bootstrap_t_torrent.id,
                bootstrap_t_torrent.name,
                name,
            )
            self._client.start_torrent([bootstrap_t_torrent.id])
        else:
            # Single-file torrent or one that already, so just add it to download path. The file will be created inside.
            bootstrap_t_torrent = self._client.add_torrent(
                base64_torrent,
                download_dir=download_path,
                paused=False,
            )
        # Get the full object with all fields by the torrent id
        return self._client.get_torrent(bootstrap_t_torrent.id, arguments=TRANSMISSION_FETCH_ARGS)

    async def add_torrent(self, torrent, download_path, name):
        return await asyncio.wrap_future(self._thread_pool.submit(
            self._add_torrent, torrent, download_path, name))

    def _remove_torrent(self, t_id):
        logger.debug('Deleting torrent {} from {}:{}', t_id, self._host, self._port)
        self._client.remove_torrent(t_id, delete_data=True)

    async def remove_torrent(self, t_id):
        return await asyncio.wrap_future(self._thread_pool.submit(self._remove_torrent, t_id))

    def _get_session_stats(self):
        logger.debug('Get session stats')
        return self._client.session_stats()

    def _force_recheck(self, t_id):
        return self._client.verify_torrent(t_id)

    def _force_reannounce(self, t_id):
        return self._client.reannounce_torrent(t_id)

    def _move_data(self, t_id, download_path):
        logger.debug('Moving torrent {} to {} from {}:{}', t_id, download_path, self._host, self._port)
        self._client.move_torrent_data(t_id, download_path)
        return self._client.get_torrent(t_id, arguments=TRANSMISSION_FETCH_ARGS)
    
    def _pause_torrent(self, t_id):
        logger.debug('Pausing torrent {} from {}:{}', t_id, self._host, self._port)
        return self._client.stop_torrent(t_id)

    def _resume_torrent(self, t_id):
        logger.debug('Resuming torrent {} from {}:{}', t_id, self._host, self._port)
        return self._client.start_torrent(t_id)

    def _rename_torrent(self, t_id, name):
        logger.debug('Renaming torrent {} to {} from {}:{}', t_id, name, self._host, self._port)
        torrent = self._client.get_torrent(t_id, arguments=TRANSMISSION_FETCH_ARGS)
        self._client.rename_torrent_path(
            t_id,
            torrent.name,
            name
        )
        return self._client.get_torrent(t_id, arguments=TRANSMISSION_FETCH_ARGS)

    async def pause_torrent(self, t_id):
        return await asyncio.wrap_future(self._thread_pool.submit(self._pause_torrent, t_id))

    async def resume_torrent(self, t_id):
        return await asyncio.wrap_future(self._thread_pool.submit(self._resume_torrent, t_id))
    
    async def rename_torrent(self, t_id, name):
        return await asyncio.wrap_future(self._thread_pool.submit(self._rename_torrent, t_id, name))

    async def force_reannounce(self, t_id):
        return await asyncio.wrap_future(self._thread_pool.submit(self._force_reannounce, t_id))

    async def force_recheck(self, t_id):
        return await asyncio.wrap_future(self._thread_pool.submit(self._force_recheck, t_id))

    async def move_data(self, t_id, download_path):
        return await asyncio.wrap_future(self._thread_pool.submit(self._move_data, t_id, download_path))

    async def get_session_stats(self):
        return await asyncio.wrap_future(self._thread_pool.submit(self._get_session_stats))
