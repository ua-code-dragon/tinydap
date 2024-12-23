#!/bin/bash

export FLASK_APP=app
export FLASK_ENV=development
export SCRIPT_NAME='/code/tinyapp'

echo \
"gunicorn \
    --reload \
    $(find app/template/ -name "*.html" |awk '{print "--reload-extra-file \""$1"\" \\";}')
    --bind 127.0.0.1:8086 \
    --worker-class gevent \
    --timeout 90 \
    --error-logfile - \
    --log-level debug app" \
|sh

