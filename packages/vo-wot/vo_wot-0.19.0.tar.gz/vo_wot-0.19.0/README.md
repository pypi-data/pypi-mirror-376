# VO-WoT

> :warning: Starting from version 0.19.0, the core codebase has been moved to [WoTPy2](https://gitlab.eclipse.org/eclipse-research-labs/nephele-project/wot-py-2). In case of major bugs, feel free to keep using version 0.18.15 untils they are resolved.

This repository is based on the Web of Things Python implementation [WoTPy](https://github.com/agmangas/wot-py).

[![PyPI](https://img.shields.io/pypi/v/vo-wot)](https://pypi.org/project/vo-wot/)
[![coverage report](https://gitlab.eclipse.org/eclipse-research-labs/nephele-project/vo-wot/badges/main/coverage.svg)](https://gitlab.eclipse.org/eclipse-research-labs/nephele-project/vo-wot/-/commits/main)
## Introduction

This repository is a fork of the original [WoTPy](https://github.com/agmangas/wot-py) repository.

VO-WoT is an experimental implementation of a [W3C WoT Runtime](https://github.com/w3c/wot-architecture/blob/master/proposals/terminology.md#wot-runtime) and the [W3C WoT Scripting API](https://github.com/w3c/wot-architecture/blob/master/proposals/terminology.md#scripting-api) in Python.

Inspired by the exploratory implementations located in the [Eclipse thingweb GitHub page](https://github.com/eclipse-thingweb/).

## Features
- Supports Python 3 with versions >= 3.9
- Fully-implemented `WoT` interface.
- Asynchronous I/O programming model based on coroutines.
- Multiple client and server [Protocol Binding](https://github.com/w3c/wot-architecture/blob/master/proposals/terminology.md#protocol-binding) implementations.

### Feature support matrix

|            Feature |  Python 3           | Implementation based on                                                 |
| -----------------: |  ------------------ | ----------------------------------------------------------------------- |
|       HTTP binding |  :heavy_check_mark: | [tornadoweb/tornado](https://github.com/tornadoweb/tornado)             |
| WebSockets binding |  :heavy_check_mark: | [tornadoweb/tornado](https://github.com/tornadoweb/tornado)             |
|       CoAP binding |  :heavy_check_mark: | [chrysn/aiocoap](https://github.com/chrysn/aiocoap)                     |
|       MQTT binding |  :heavy_check_mark: | [Yakifo/amqtt](https://github.com/Yakifo/amqtt)             |
|       Zenoh binding |  :heavy_check_mark:  | [eclipse-zenoh/zenoh-python](https://github.com/eclipse-zenoh/zenoh-python)  |


## Installation
```
pip install vo-wot
```

### Development

To install in development mode with all the test dependencies:

```
pip install -U -e .[docs]
```

### Development in VSCode with devcontainers
We have also provided a convenient `devcontainer` configuration to better recreate your local development environment. VSCode should detect it if you have the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension installed.

## Docs
The documentation is currently hosted [here](https://netmode.gitlab.io/vo-wot/).

Alternatively to build the documentation, move to the `docs` folder and run:

```
make html
```
