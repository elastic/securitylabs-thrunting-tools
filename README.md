# securitylabs-tools

A collection of command line utilities for working on the command line.

- `eql-query`
- `lucene-query`

## Installation

TODO

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
│                                 /home/dcode/.config/securitylabs-tools/config.yml]          │
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
