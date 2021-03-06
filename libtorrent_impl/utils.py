from utils import extract_name_from_announce


def format_libtorrent_endpoint(endpoint):
    key = 'listen_{}_{}'.format(*endpoint)

    if ':' in endpoint[0]:  # Looks like an IPv6 address
        readable_name = '[{}]:{}'.format(*endpoint)
    else:  # Probably an IPv4 address
        readable_name = '{}:{}'.format(*endpoint)

    return key, readable_name


def format_tracker_error(alert):
    error = alert.error
    msg = error.message().capitalize()
    if alert.msg:
        msg += ' - {}'.format(alert.msg)
    msg += ' ({}; {} {})'.format(
        extract_name_from_announce(alert.url),
        error.category().name().capitalize(),
        error.value(),
    )
    return msg


class LibtorrentClientException(Exception):
    pass
