# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337

import concurrent.futures
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from quasarr.providers.log import info, debug


def get_by_download_links(shared_state, url, mirror, title): # signature must align with other download link functions!
    by = shared_state.values["config"]("Hostnames").get("by")
    headers = {
        'User-Agent': shared_state.values["user_agent"],
    }

    mirror_lower = mirror.lower() if mirror else None
    links = []

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        page_content = resp.text
        soup = BeautifulSoup(page_content, "html.parser")
        frames = [iframe.get("src") for iframe in soup.find_all("iframe") if iframe.get("src")]

        frame_urls = [src for src in frames if f'https://{by}' in src]
        if not frame_urls:
            debug(f"No iframe hosts found on {url} for {title}.")
            return []

        async_results = []

        def fetch(url):
            try:
                r = requests.get(url, headers=headers, timeout=10)
                return r.text, url
            except Exception:
                return None, url

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(fetch, url): url for url in frame_urls}
            for future in concurrent.futures.as_completed(future_to_url):
                content, source = future.result()
                if content:
                    async_results.append((content, source))

        url_hosters = []
        for content, source in async_results:
            host_soup = BeautifulSoup(content, "html.parser")
            link = host_soup.find("a", href=re.compile(r"/go\.php\?"))
            if not link:
                continue

            href = link["href"]
            hostname = link.text.strip().replace(" ", "")
            hostname_lower = hostname.lower()

            if mirror_lower and mirror_lower not in hostname_lower:
                debug(f'Skipping link from "{hostname}" (not the desired mirror "{mirror}")!')
                continue

            url_hosters.append((href, hostname))

        def resolve_redirect(href_hostname):
            href, hostname = href_hostname
            try:
                r = requests.get(href, headers=headers, timeout=10, allow_redirects=True)
                return r.url
            except Exception as e:
                debug(f"Error resolving link for {hostname}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_hostname = {executor.submit(resolve_redirect, pair): pair[1] for pair in url_hosters}
            for future in concurrent.futures.as_completed(future_to_hostname):
                resolved_url = future.result()
                hostname = future_to_hostname[future]
                if not hostname:
                    hostname = urlparse(resolved_url).hostname
                if resolved_url:
                    links.append([resolved_url, hostname])

    except Exception as e:
        info(f"Error loading BY download links: {e}")

    return links
