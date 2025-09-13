# PyBenChatBot
![GitHub License](https://img.shields.io/github/license/DarkFlameBEN/pybenchatbot)
[![PyPI - Version](https://img.shields.io/pypi/v/pybenchatbot)](https://pypi.org/project/pybenchatbot/)
![python suggested version](https://img.shields.io/badge/python-3.13.7-red.svg)
![python minimum version](https://img.shields.io/badge/python(min)-3.9+-red.svg)
![platforms](https://img.shields.io/badge/Platforms-Linux%20|%20Windows%20|%20Mac%20-purple.svg)

## Introduction
PyBEN ChatBot enables anyone to run a custom chatbot on its own python module

## Table of contents
1. [Getting started](#getting-started)
2. [Usage](#usage)

## Getting started

### Installation
Win:
> python -m pip install pybenchatbot -U

macOS:
> python3 -m pip install pybenchatbot -U

## Usage
The package is intended to be run as a module from cli.

Running the command will create a local webserver on the requested port. 
The webserver can be accessed at http://127.0.0.1:8000/

Chatbot on your local repository (Run from workspace or specify the path): 
> python -m pybenchatbot
> python -m pybenchatbot --target ./myproject --port 8000
 
Chatbot on a specific module:
> python -m pybenchatbot -t pybenutils -p 8000

