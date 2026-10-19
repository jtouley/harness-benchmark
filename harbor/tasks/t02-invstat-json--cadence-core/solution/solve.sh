#!/bin/bash
set -e
cd /app
git apply --whitespace=nowarn /solution/reference.patch
