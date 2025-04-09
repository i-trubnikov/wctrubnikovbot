#!/bin/bash
Xvfb :99 -ac &
export DISPLAY=:99
python3 telegram_bot.py
