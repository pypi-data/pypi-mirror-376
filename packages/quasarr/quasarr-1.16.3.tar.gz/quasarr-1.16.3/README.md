#   

<img src="https://raw.githubusercontent.com/rix1337/Quasarr/main/Quasarr.png" data-canonical-src="https://raw.githubusercontent.com/rix1337/Quasarr/main/Quasarr.png" width="64" height="64" />

Quasarr connects JDownloader with Radarr, Sonarr and LazyLibrarian. It also decrypts links protected by CAPTCHAs.

[![PyPI version](https://badge.fury.io/py/quasarr.svg)](https://badge.fury.io/py/quasarr)
[![Discord](https://img.shields.io/discord/1075348594225315891)](https://discord.gg/eM4zA2wWQb)
[![GitHub Sponsorship](https://img.shields.io/badge/support-me-red.svg)](https://github.com/users/rix1337/sponsorship)

Quasarr pretends to be both `Newznab Indexer` and `SABnzbd client`. Therefore, do not try to use it with real usenet
indexers or download clients. It simply does not know what NZB or torrent files are.

Quasarr includes a solution to quickly and easily decrypt protected links.
[Active Sponsors get access to SponsorsHelper to do so automatically.](https://github.com/rix1337/Quasarr?tab=readme-ov-file#sponsorshelper)
Alternatively, follow the link from the console output (or discord notification) to solve CAPTCHAs manually.
Quasarr will confidently handle the rest.

# Instructions

---

## Quasarr

Tell Quasarr which sites to search for releases. It requires at least one valid source to start up.

> - By default, Quasarr does **not** know which sites to scrape for download links.  
> - The setup will guide you through the process of providing valid hostnames for Quasarr to scrape.  
> - Do **not** ask for help here if you do not know which hostnames to use. Picking them is solely your responsibility.  
> - You may check sites like [Pastebin](https://pastebin.com/search?q=hostnames+quasarr) for user‑submitted suggestions.

---

## JDownloader

1. Run JDownloader and connect it to the My JDownloader service.  
2. Provide your [My‑JDownloader‑Credentials](https://my.jdownloader.org) to Quasarr during the setup process.

> - Consider setting up a fresh JDownloader before you begin.  
> - JDownloader must be running and available to Quasarr.  
> - Quasarr will modify JDownloader’s settings so downloads can be handled by Radarr/Sonarr/LazyLibrarian.  
> - If using Docker, ensure that JDownloader’s download path is available to Radarr/Sonarr/LazyLibrarian with **exactly the same** internal and external path mapping (matching only the external path is not enough).

---

## Radarr / Sonarr

Set up Quasarr as a **Newznab Indexer** and **SABnzbd Download Client**:

1. **URL**: Use the `URL` from the **API Information** section of the console output (or copy it from the Quasarr web UI).  
2. **API Key**: Use the `API Key` from the **API Information** section of the console output (or copy it from the Quasarr web UI).  
3. Leave all other settings at their defaults.

> **Important notice for Sonarr**  
> - Ensure all shows (including anime) are set to the **Standard** series type.  
> - Quasarr will never find releases for shows set to **Anime / Absolute**.

---

## LazyLibrarian

> **Important notice**
> - This feature is experimental and may not work as expected.
> - Quasarr cannot help you with metadata issues, missing covers, or other LazyLibrarian problems.
> - Please report issues when one of your hostnames yields results through their website, but not in LazyLibrarian.

Set up Quasarr as a **SABnzbd+ Downloader**

1. **SABnzbd URL/Port**: Use port and host parts from `URL` found in the **API Information** section of the console output (or copy it from the Quasarr web UI).  
2. **SABnzbd API Key**: Use the `API Key` from the **API Information** section of the console output (or copy it from the Quasarr web UI).  
3. **SABnzbd Category**: Use `docs` to ensure LazyLibrarian does not interfere with Radarr/Sonarr.  
4. Press `Test SABnzbd` to verify the connection, then `Save changes`.

Set up Quasarr as a **Newznab Provider**:
1. **Newznab URL**: Use the `URL` from the **API Information** section of the console output (or copy it from the Quasarr web UI).
2. **Newznab API** Use the `API Key` from the **API Information** section of the console output (or copy it from the Quasarr web UI).
3. Press `Test` to verify the connection, then `Save changes`.

Fix the `Importing` settings:
1. Check `Enable OpenLibrary api for book/author information`
2. Select `OpenLibrary` below `Primary Information Source`
2. Under `Import languages` add `, Unknown` (and for German users: `, de, ger, de-DE`).

Fix the `Processing` settings:
1. Under `Folders` add the full Quasarr download path, typically `/downloads/Quasarr/`
2. If you do not do this,  processing after the download will fail.



---

## Advanced Settings

To restrict results to a specific mirror, add the mirror name to the Newznab/indexer URL.  
> **Example:** Appending `/api/dropbox/` will only return releases where `dropbox` is explicitly mentioned in a link.  
> **Caution:** If a mirror is not available at a hostname, the release will be ignored or the download will fail. Use this option carefully.

To see download status information in Radarr/Sonarr
1. Open `Activity` → `Queue` → `Options`
2. Enable `Release Title`

# Docker

It is highly recommended to run the latest docker image with all optional variables set.

```
docker run -d \
  --name="Quasarr" \
  -p port:8080 \
  -v /path/to/config/:/config:rw \
  -e 'INTERNAL_ADDRESS'='http://192.168.0.1:8080' \
  -e 'EXTERNAL_ADDRESS'='https://foo.bar/' \
  -e 'DISCORD'='https://discord.com/api/webhooks/1234567890/ABCDEFGHIJKLMN' \
  -e 'HOSTNAMES'='https://pastebin.com/raw/eX4Mpl3'
  -e 'SILENT'='True' \
  -e 'DEBUG'='' \
  ghcr.io/rix1337/quasarr:latest
  ```

* `INTERNAL_ADDRESS` is required so Radarr/Sonarr/LazyLibrarian can reach Quasarr. **Must** include port!
* `EXTERNAL_ADDRESS` is optional and helpful if using a reverse proxy. Always protect external access with basic auth!
* `DISCORD` is optional and must be a valid Discord webhook URL.
* `HOSTNAMES` is optional and allows skipping the manual hostname step during setup.
    * Must be a publicly available `HTTP` or `HTTPs` link
    * Must be a raw `.ini` / text file (not HTML or JSON)
    * Must contain at least one valid Hostname per line `ab = xyz`
* `SILENT` is optional and silences all discord notifications except for error messages from SponsorsHelper if `True`.
* `DEBUG` is optional and enables debug logging if `True`.

# Manual setup

Use this only in case you can't run the docker image.

`pip install quasarr`

* Requires Python 3.12 or later

```
  --port=8080
  --discord=https://discord.com/api/webhooks/1234567890/ABCDEFGHIJKLMN
  --external_address=https://foo.bar/
  --hostnames=https://pastebin.com/raw/eX4Mpl3
  ```

* `--discord` see `DISCORD`docker variable
* `--external_address` see `EXTERNAL_ADDRESS`docker variable
* `--hostnames` see `HOSTNAMES`docker variable

# Philosophy

Complexity is the killer of small projects like this one. It must be fought at all cost!

We will not waste precious time on features that will slow future development cycles down.
Most feature requests can be satisfied by:

- Existing settings in Radarr/Sonarr/LazyLibrarian
- Existing settings in JDownloader
- Existing tools from the *arr ecosystem that integrate directly with Radarr/Sonarr/LazyLibrarian

# Roadmap

- Assume there are zero known
  issues [unless you find one or more open issues in this repository](https://github.com/rix1337/Quasarr/issues).
- Still having an issue? Provide a detailed report [here](https://github.com/rix1337/Quasarr/issues/new/choose)!
- There are no hostname integrations in active development unless you see an open pull request
  [here](https://github.com/rix1337/Quasarr/pulls).
- Pull requests are welcome. Especially for popular hostnames.
    - Always reach out on Discord before starting work on a new feature to prevent waste of time.
    - Please follow the existing code style and project structure.
    - Anti-bot measures must be circumvented fully by Quasarr. Thus you will need to provide a working solution for new
      CAPTCHA types by integrating it in the Quasarr Web UI.
    - Please provide proof of functionality (screenshots/examples) when submitting your pull request.

# SponsorsHelper

<img src="https://imgur.com/iHBqLwT.png" data-canonical-src="https://imgur.com/iHBqLwT.png" width="64" height="64" />

The SponsorsHelper is a Docker image that automatically solves CAPTCHAs and decrypts links for Quasarr.

[The process strictly requires an account token with credit at DeathByCaptcha](https://deathbycaptcha.com/register?refid=6184288242b).

The image is only available to active [sponsors](https://github.com/users/rix1337/sponsorship) (hence the name).

Access is automatically granted via GitHub:

[![Github Sponsorship](https://img.shields.io/badge/support-me-red.svg)](https://github.com/users/rix1337/sponsorship)

## Docker Login

### Generate GitHub Token

1. Open the [GitHub token settings](https://github.com/settings/tokens/new).
2. Select `New personal access token (classic)`.
3. Fill in the note, e.g., `SponsorsHelper`.
4. Enable the "read:packages" scope.
5. Create and use the token for login as `GITHUB_TOKEN` below:

### Login

`docker login https://ghcr.io  -u USERNAME -p GITHUB_TOKEN`

`USERNAME` is your GitHub username.
`GITHUB_TOKEN` is the token you created above.

## Starting SponsorsHelper

Without logging in, it is not possible to download the image!

```
docker run -d \
    --name='SponsorsHelper' \
    -e 'QUASARR_URL'='http://192.168.0.1:8080' \
    -e 'DEATHBYCAPTCHA_TOKEN'='2FMum5zuDBxMmbXDIsADnllEFl73bomydIpzo7...' \
    'ghcr.io/rix1337-sponsors/docker/helper:latest'
```

### Required Parameters

- `-e 'QUASARR_URL'` The local URL of Quasarr - e.g., `http://192.168.0.1:8080`
  (should match the `INTERNAL_ADDRESS` parameter from above)
- `-e 'DEATHBYCAPTCHA_TOKEN'` The account token
  from [DeathByCaptcha](https://deathbycaptcha.com/register?refid=6184288242b) - e.g.,
  `2FMum5zuDBxMmbXDIsADnllEFl73bomydIpzo7...aBc`

# Development Setup for Pull Requests

To test your changes before submitting a pull request:

**Run Quasarr with the `--internal_address` parameter:**

```bash
python Quasarr.py --internal_address=http://<host-ip>:<port>
```

Replace `<host-ip>` and `<port>` with the scheme, IP, and port of your host machine.
The `--internal_address` parameter is **mandatory**.

**Start the required services using the `dev-services-compose.yml` file:**

```bash
CONFIG_VOLUMES=/path/to/config docker-compose -f docker/dev-services-compose.yml up
```

Replace `/path/to/config` with your desired configuration location.
The `CONFIG_VOLUMES` environment variable is **mandatory**.
