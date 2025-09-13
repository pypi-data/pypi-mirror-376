# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337
#
# Special note: The signatures of all handlers must stay the same so we can neatly call them in download()
# Same is true for every get_xx_download_links() function in sources/xx.py

import json

from quasarr.downloads.linkcrypters.hide import decrypt_links_if_hide
from quasarr.downloads.sources.al import get_al_download_links
from quasarr.downloads.sources.by import get_by_download_links
from quasarr.downloads.sources.dd import get_dd_download_links
from quasarr.downloads.sources.dt import get_dt_download_links
from quasarr.downloads.sources.dw import get_dw_download_links
from quasarr.downloads.sources.mb import get_mb_download_links
from quasarr.downloads.sources.nx import get_nx_download_links
from quasarr.downloads.sources.sf import get_sf_download_links, resolve_sf_redirect
from quasarr.downloads.sources.sl import get_sl_download_links
from quasarr.downloads.sources.wd import get_wd_download_links
from quasarr.providers.log import info
from quasarr.providers.notifications import send_discord_message
from quasarr.providers.statistics import StatsHelper


def handle_unprotected(shared_state, title, password, package_id, imdb_id, url,
                       mirror=None, size_mb=None, links=None, func=None, label=""):
    if func:
        links = func(shared_state, url, mirror, title)

    if links:
        info(f"Decrypted {len(links)} download links for {title}")
        send_discord_message(shared_state, title=title, case="unprotected", imdb_id=imdb_id, source=url)
        added = shared_state.download_package(links, title, password, package_id)
        if not added:
            fail(title, package_id, shared_state,
                 reason=f'Failed to add {len(links)} links for "{title}" to linkgrabber')
            return {"success": False, "title": title}
    else:
        fail(title, package_id, shared_state,
             reason=f'Offline / no links found for "{title}" on {label} - "{url}"')
        return {"success": False, "title": title}

    StatsHelper(shared_state).increment_package_with_links(links)
    return {"success": True, "title": title}


def handle_protected(shared_state, title, password, package_id, imdb_id, url,
                     mirror=None, size_mb=None, func=None, label=""):
    links = func(shared_state, url, mirror, title)
    if links:
        info(f'CAPTCHA-Solution required for "{title}" at: "{shared_state.values['external_address']}/captcha"')
        send_discord_message(shared_state, title=title, case="captcha", imdb_id=imdb_id, source=url)
        blob = json.dumps({"title": title, "links": links, "size_mb": size_mb, "password": password})
        shared_state.values["database"]("protected").update_store(package_id, blob)
    else:
        fail(title, package_id, shared_state,
             reason=f'No protected links found for "{title}" on {label} - "{url}"')
        return {"success": False, "title": title}
    return {"success": True, "title": title}


def handle_al(shared_state, title, password, package_id, imdb_id, url, mirror, size_mb):
    data = get_al_download_links(shared_state, url, mirror, title, password)
    links = data.get("links", [])
    title = data.get("title", title)
    password = data.get("password", "")
    return handle_unprotected(
        shared_state, title, password, package_id, imdb_id, url,
        links=links,
        label='AL'
    )


def handle_sf(shared_state, title, password, package_id, imdb_id, url, mirror, size_mb):
    if url.startswith(f"https://{shared_state.values['config']('Hostnames').get('sf')}/external"):
        url = resolve_sf_redirect(url, shared_state.values["user_agent"])
    elif url.startswith(f"https://{shared_state.values['config']('Hostnames').get('sf')}/"):
        data = get_sf_download_links(shared_state, url, mirror, title)
        url = data.get("real_url")
        if not imdb_id:
            imdb_id = data.get("imdb_id")

    if not url:
        fail(title, package_id, shared_state,
             reason=f'Failed to get download link from SF for "{title}" - "{url}"')
        return {"success": False, "title": title}

    return handle_protected(
        shared_state, title, password, package_id, imdb_id, url,
        mirror=mirror,
        size_mb=size_mb,
        func=lambda ss, u, m, t: [[url, "filecrypt"]],
        label='SF'
    )


def handle_sl(shared_state, title, password, package_id, imdb_id, url, mirror, size_mb):
    data = get_sl_download_links(shared_state, url, mirror, title)
    links = data.get("links")
    if not imdb_id:
        imdb_id = data.get("imdb_id")
    return handle_unprotected(
        shared_state, title, password, package_id, imdb_id, url,
        links=links,
        label='SL'
    )


def handle_wd(shared_state, title, password, package_id, imdb_id, url, mirror, size_mb):
    data = get_wd_download_links(shared_state, url, mirror, title)
    links = data.get("links")
    if not links:
        fail(title, package_id, shared_state,
             reason=f'Offline / no links found for "{title}" on WD - "{url}"')
        return {"success": False, "title": title}

    decrypted = decrypt_links_if_hide(shared_state, links)
    if decrypted and decrypted.get("status") != "none":
        status = decrypted.get("status", "error")
        links = decrypted.get("results", [])
        if status == "success":
            return handle_unprotected(
                shared_state, title, password, package_id, imdb_id, url,
                links=links, label='WD'
            )
        else:
            fail(title, package_id, shared_state,
                 reason=f'Error decrypting hide.cx links for "{title}" on WD - "{url}"')
            return {"success": False, "title": title}

    return handle_protected(
        shared_state, title, password, package_id, imdb_id, url,
        mirror=mirror,
        size_mb=size_mb,
        func=lambda ss, u, m, t: links,
        label='WD'
    )


def download(shared_state, request_from, title, url, mirror, size_mb, password, imdb_id=None):
    if "lazylibrarian" in request_from.lower():
        category = "docs"
    elif "radarr" in request_from.lower():
        category = "movies"
    else:
        category = "tv"

    package_id = f"Quasarr_{category}_{str(hash(title + url)).replace('-', '')}"

    if imdb_id is not None and imdb_id.lower() == "none":
        imdb_id = None

    config = shared_state.values["config"]("Hostnames")
    flags = {
        'AL': config.get("al"),
        'BY': config.get("by"),
        'DD': config.get("dd"),
        'DT': config.get("dt"),
        'DW': config.get("dw"),
        'MB': config.get("mb"),
        'NX': config.get("nx"),
        'SF': config.get("sf"),
        'SL': config.get("sl"),
        'WD': config.get("wd")
    }

    handlers = [
        (flags['AL'], handle_al),
        (flags['BY'], lambda *a: handle_protected(*a, func=get_by_download_links, label='BY')),
        (flags['DD'], lambda *a: handle_unprotected(*a, func=get_dd_download_links, label='DD')),
        (flags['DT'], lambda *a: handle_unprotected(*a, func=get_dt_download_links, label='DT')),
        (flags['DW'], lambda *a: handle_protected(*a, func=get_dw_download_links, label='DW')),
        (flags['MB'], lambda *a: handle_protected(*a, func=get_mb_download_links, label='MB')),
        (flags['NX'], lambda *a: handle_unprotected(*a, func=get_nx_download_links, label='NX')),
        (flags['SF'], handle_sf),
        (flags['SL'], handle_sl),
        (flags['WD'], handle_wd),
    ]

    for flag, fn in handlers:
        if flag and flag.lower() in url.lower():
            return {"package_id": package_id,
                    **fn(shared_state, title, password, package_id, imdb_id, url, mirror, size_mb)}

    if "filecrypt" in url.lower():
        return {"package_id": package_id, **handle_protected(
            shared_state, title, password, package_id, imdb_id, url, mirror, size_mb,
            func=lambda ss, u, m, t: [[u, "filecrypt"]],
            label='filecrypt'
        )}

    info(f'Could not parse URL for "{title}" - "{url}"')
    StatsHelper(shared_state).increment_failed_downloads()
    return {"success": False, "package_id": package_id, "title": title}


def fail(title, package_id, shared_state, reason="Offline / no links found"):
    try:
        info(f"Reason for failure: {reason}")
        StatsHelper(shared_state).increment_failed_downloads()
        blob = json.dumps({"title": title, "error": reason})
        stored = shared_state.get_db("failed").store(package_id, json.dumps(blob))
        if stored:
            info(f'Package "{title}" marked as failed!"')
            return True
        else:
            info(f'Failed to mark package "{title}" as failed!"')
            return False
    except Exception as e:
        info(f'Error marking package "{package_id}" as failed: {e}')
        return False
