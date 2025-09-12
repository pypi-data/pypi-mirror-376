# VO-WoT

This repository is an updated version of [WoTPy](https://github.com/agmangas/wot-py).

[![PyPI](https://img.shields.io/pypi/v/wotpy2)](https://pypi.org/project/wotpy2/)

## Introduction

This repository is a fork of the original [WoTPy](https://github.com/agmangas/wot-py) repository.

WoTPy is an experimental implementation of a [W3C WoT Runtime](https://github.com/w3c/wot-architecture/blob/master/proposals/terminology.md#wot-runtime) and the [W3C WoT Scripting API](https://github.com/w3c/wot-architecture/blob/master/proposals/terminology.md#scripting-api) in Python.

Inspired by the exploratory implementations located in the [thingweb GitHub page](https://github.com/thingweb).

## Features
- Supports Python 3 with versions >= 3.9
- Fully-implemented `WoT` interface.
- Asynchronous I/O programming model based on coroutines.
- Multiple client and server [Protocol Binding](https://github.com/w3c/wot-architecture/blob/master/proposals/terminology.md#protocol-binding) implementations.

### Feature support matrix

|            Feature  |  Python 3            | Implementation based on                                                      |
| -----------------:  |  ------------------  | ---------------------------------------------------------------------------- |
|       HTTP binding  |  :heavy_check_mark:  | [tornadoweb/tornado](https://github.com/tornadoweb/tornado)                  |
| WebSockets binding  |  :heavy_check_mark:  | [tornadoweb/tornado](https://github.com/tornadoweb/tornado)                  |
|       CoAP binding  |  :heavy_check_mark:  | [chrysn/aiocoap](https://github.com/chrysn/aiocoap)                          |
|       MQTT binding  |  :heavy_check_mark:  | [Yakifo/amqtt](https://github.com/Yakifo/amqtt)                              |
|       Zenoh binding |  :heavy_check_mark:  | [eclipse-zenoh/zenoh-python](https://github.com/eclipse-zenoh/zenoh-python)  |


## Installation
```
pip install wotpy2
```

### Development

To install in development mode with all the test dependencies:

```
pip install -U -e .[tests,docs]
```

Some WoTPy features (e.g. CoAP binding) are not available outside of Linux. If you have Docker available in your system, and want to easily run the tests in a Linux environment (whether you're on macOS or Windows) you can use the Docker-based test script:

```
$ WOTPY_TESTS_MQTT_BROKER_URL=mqtt://192.168.1.141 ./pytest-docker-all.sh
...
+ docker run --rm -it -v /var/folders/zd/02pk7r3954s_t03lktjmvbdc0000gn/T/wotpy-547bed6bacf34ddc95b41eceb46553dd:/app -e WOTPY_TESTS_MQTT_BROKER_URL=mqtt://192.168.1.141 python:3.9 /bin/bash -c 'cd /app && pip install -U .[tests] && pytest -v --disable-warnings'
...
Python 3.9 :: OK
Python 3.10 :: OK
Python 3.11 :: OK
Python 3.12 :: OK
Python 3.13 :: OK
```
`WOTPY_TESTS_MQTT_BROKER_URL` defines the url of the MQTT broker. It will listen to port `1883` by default. If your broker is set up in a different way, you can provide the port in the url as well.

`WOTPY_TESTS_ZENOH_ROUTER_URL` defines the url of the Zenoh router. An example router url value is `tcp/192.168.1.1:7447` assuming the router is bound on the interface with the IP `192.168.1.1` and listens to port `7447`. Check the Zenoh router's output (`zenohd` command) for more info.

You can also test only for a specific Python version with the `PYTHON_TAG` variable and the `pytest-docker.sh` script like this:

```
$ WOTPY_TESTS_MQTT_BROKER_URL=mqtt://192.168.1.141 PYTHON_TAG=3.9 ./pytest-docker.sh
```
### Development in VSCode with devcontainers
We have also provided a convenient `devcontainer` configuration to better recreate your local development environment. VSCode should detect it if you have the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension installed.

## Docs
Move to the `docs` folder and run:

```
make html
```
