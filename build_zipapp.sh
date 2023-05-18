#!/usr/bin/sh

shiv --site-packages src --compressed -p '/usr/bin/env python3' -o app.pyz -e app:run_app -r src/requirements.txt