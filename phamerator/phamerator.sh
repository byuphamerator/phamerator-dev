#!/bin/bash

abspath="$(cd "${0%/*}" 2>/dev/null; echo "$PWD"/"${0##*/}")"
echo $abspath
phamerator_path=`dirname $abspath`
echo $phamerator_path

cd $phamerator_path
bzr pull
$phamerator_path/Phamerator
