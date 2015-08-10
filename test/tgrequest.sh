#!/bin/bash

URIR=$1
URIG=$2
dt=$3

curl -v -I -L -H "Accept-Datetime: $dt" ${URIG}${URIR}
