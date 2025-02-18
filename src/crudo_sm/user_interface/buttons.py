#!/usr/bin/env python
# -*- coding: utf-8 -*-
import webbrowser
# import os
# import sys; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class WebButton:
    """This is Class create web button"""
    def __init__(self, url):
        self.url = url

    def button(self):
        """ This is function parse urls from config json and return """
        return self.url

    def web_button(self):
        webbrowser.open(self.button())
