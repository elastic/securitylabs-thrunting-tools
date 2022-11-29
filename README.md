# Elastic Security Labs thrunting-tools

Have you ever been threat hunting (hereafter known as "thrunting") in Kibana and thought
"Gee! I wish I could take these results and do some automation on the command line!".
Well look no further, fellow thrunter! This repo has just what you need to make your
automation adventures a bit easier.

thrunting-tools is a collection of command line utilities for working with data.

The current list of tools are:

- `eql-query`, a tool to let you perform EQL searches from your shell!
- `lucene-query`, a tool to let you perform Lucene searches against Elasticsearch in your
  comfort zone, the command line.
- `from-charcode`, a tool to convert a character code in a given base to the ASCII character
- `to-charcode`, a tool to convert an ASCII character to a given base
- `url-decode`, a tool to decode urlencoded strings
- `url-encode`, a tool to encode common character or all special characters to urlencoded strings
- `zlib-compress`, a tool to perform zlib compression/deflation on the command line
- `zlib-decompress`, a tool to perform zlib decompression/inflation on the command line
- `zlib-deflate`, an alias for zlib-compress
- `zlib-decompress`, an alias for zlib-decompress
- `unmap-pe`, processes a PE binary, removing the memory mapping. Useful for analyzing process memory dumps

## Installation

The easiest way to install thrunting-tools is with [pipx](https://pypa.github.io/pipx/). Once
you have pipx installed, to install these tools on your path, simply install the latest release
with:

```shell
pipx install thrunting-tools
```

Alternatively, if you'd like to install with pip and you have your own Python environment, you can
do that too.

```shell
pip3 install thrunting-tools
```

You can now check that each command was installed.

```shell
eql-query --version
lucene-query --version
```

### Docker Usage

Lastly, if you want to use a container runtime environment, you can use the latest release from
the repository GitHub Container Repository. Currently, we're publishing AMD64 and ARM64 images.

```shell
docker pull ghcr.io/elastic/securitylabs-thrunting-tools:main
```

Then, you can run the container and pass your local configuration in to the default
location used by the container, `/config.yml`. (NOTE: the `:z` part of the volume
specification is only needed if you use SELinux)

```shell
docker run -ti -v "${HOME}/.config/thrunting-tools/config.yml":/config.yml:ro,z \
    --rm ghcr.io/elastic/securitylabs-thrunting-tools:latest eql-query --help
```

## Usage

Each of the commands provide a usage when called with `--help`.

```shell
$ eql-query --help

 Usage: eql-query [OPTIONS] QUERY

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    query      TEXT  Query specified using EQL (See https://ela.st/eql) [required]         │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --index        -i      TEXT     Index pattern to search. Defaults to                        │
│                                 '.alerts-security.alerts-default,apm-*-transaction*,logs-*' │
│ --since        -s      TEXT     Earliest time filter using datemath or datetime             │
│                                 [default: now-30d/d]                                        │
│ --before       -b      TEXT     Latest time filter using datemath or datetime               │
│                                 [default: now]                                              │
│ --compact      -c               Output one event/sequence per line                          │
│ --fields       -f      TEXT     Comma separated list of fields to display [default: None]   │
│ --size         -s      INTEGER  Specify maximum size of result set [default: 100]           │
│ --config               PATH     Optional path to YAML configuration with settings for       │
│                                 Elasticsearch                                               │
│                                 [default:                                                   │
│                                 /home/user/.config/thrunting-tools/config.yml]           │
│ --environment  -e      TEXT     Environment name to use from config file (if present)       │
│                                 [default: default]                                          │
│ --help                          Show this message and exit.                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Configuration

There are two ways to pass configuration to the tools: environment variables and configuration files.

The tools default to looking for the YAML configuration file in the platform-specific
configuration directory (see the `--help` output). If present, configuration groups are
top-level keys (e.g. `elasticsearch`), which contain a list of environments. All scripts will
check for the first environment with the name attribute set to `default`  if none is specified
on the command line.

Example configuration file:

```yaml
elasticsearch:
  - name: default
    cloud_id: "security-cluster:dXMtd2VzdDEuZ2NwLmNsb3VkLmVzLmlvJGFiY2R="
    cloud_auth: "elastic:changeme"
```

## Examples

Run query using `devel` environment configuration

```shell
eql-query -e devel 'malware where event.kind: "alert"'
```

Using `jq` and `wc` to get the number of alert events where `EXCEL.EXE` was the parent process.

```shell
eql-query 'any where event.kind: "alert"' -c | \
    jq 'select(._source.process.parent.name == "EXCEL.EXE")' -c | wc -l
```

Find the unique event categories of all events in the last day that triggered based upon a
rule using the 'sandbox' environment

```shell
$ lucene-query --since 'now-1d' 'rule: *' -e sandbox -c | \
    jq '._source.event.category[]' -c -r | sort -u
network
```

Find the unique dynamic DNS subdomains of a particular domain resolved in our network in the
last month

```shell
lucene-query --since 'now-1M' 'dns.question.name: *.duckdns.org' -c \
    | jq '._source.dns.question.name' -r | sort -u
...
```

Find a list of all the unique agent IDs that resolved a known malware domain within the last 12 months.

```shell
$ lucene-query --since 'now-12M' 'dns.question.name: puerto2547.duckdns.org' -c \
    | jq '._source.agent.id' -r | sort -u
ec82f608-3d1b-4651-900e-b970c68bbeef
```

Extract a single binary using Elastic Defend integration with
[optional sample collection](https://www.elastic.co/security-labs/collecting-cobalt-strike-beacons-with-the-elastic-stack) enabled.
Note that additional shell scripting would be needed to loop over a set of results.

```shell
eql-query 'process where ?process.Ext.memory_region.bytes_compressed_present == true' \
    --size 1 \
    --fields 'process.Ext.memory_region.bytes_compressed' | \
    jq -r '.process.Ext.memory_region.bytes_compressed' | \
    base64 -d | zlib-decompress > captured_sample.bin
```
