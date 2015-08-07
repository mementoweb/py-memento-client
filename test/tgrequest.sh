#!/bin/bash

URIR=$1
URIG=$2
dt=$3

curl -I -H "Accept-Datetime: $dt" ${URIG}${URIR}
