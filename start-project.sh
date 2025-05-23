#!/bin/sh
set -e
# Quart Starter installation script
#
# This script is intended as a convenient way to start a new project
# based on quart-starter.
#
# Source code is available at https://github.com/bmorgan21/quart-starter/start-project.sh
#
# Usage
# ==============================================================================
# 
# To get started there are two options.
# 
# 1. download and run in one step
#
#   $ curl -fsSL https://raw.githubusercontent.com/bmorgan21/quart-starter/main/start-project.sh | sh -s <project name>
#
# 2. download and run locally
#
#   $ curl -fsSL https://raw.githubusercontent.com/bmorgan21/quart-starter/main/start-project.sh -o start-project.sh
#   $ sh start-project.sh <project name>
#
PROJECT_NAME="$1"
PROJECT_NAME_LOWER=`echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]'`
FOLDER_NAME=`echo "$PROJECT_NAME_LOWER" | sed -e 's/ /-/'`
MODULE_NAME=`echo "$PROJECT_NAME_LOWER" | sed -e 's/ /_/'`
echo "Setting up $PROJECT_NAME..."

git clone --depth=1 https://github.com/bmorgan21/quart-starter.git quart-starter-tmp

# Detect OS and adjust sed command accordingly
if [ "$(uname)" = "Darwin" ]; then
    SED_CMD="sed -i .bk"
else
    SED_CMD="sed -i"
fi

# Use file mimetype to filter only text files
find quart-starter-tmp -type f -exec sh -c 'file --mime-type "$1" | grep -q "text/"' _ {} \; -exec $SED_CMD "s/Quart Starter/$PROJECT_NAME/g" {} +
find . -name "*.bk" | xargs rm
find quart-starter-tmp -type f -exec sh -c 'file --mime-type "$1" | grep -q "text/"' _ {} \; -exec $SED_CMD "s/quart_starter/$MODULE_NAME/g" {} +
find . -name "*.bk" | xargs rm
find quart-starter-tmp -type f -exec sh -c 'file --mime-type "$1" | grep -q "text/"' _ {} \; -exec $SED_CMD "s/quart-starter/$FOLDER_NAME/g" {} +
find . -name "*.bk" | xargs rm

rm -f quart-starter-tmp/start-project.sh
mv quart-starter-tmp/quart_starter "quart-starter-tmp/$MODULE_NAME"
rm -rf quart-starter-tmp/.git
mv quart-starter-tmp "$FOLDER_NAME"
