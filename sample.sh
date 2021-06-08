#!/usr/bin/env bash
date=$(date +"%m-%d-%y")

cp data/sample/news-entries.csv data/daily/${date}-news-entries.csv
cp data/sample/wiki-entries.csv data/daily/${date}-wiki-entries.csv
