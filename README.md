# webpage-categorizer


# How to run? 
```
cd /Users/snemeth/development/my-repos/webpage-categorizer/webpagecategorizer
python categorizer.py -i /Users/snemeth/Downloads/_personal/_webpages/unsorted -o /Users/snemeth/Downloads/_personal/_webpages/sorted -c categories.json


# Fully automatic, including removal
python categorizer.py -i /Users/snemeth/Downloads/_personal/_webpages/unsorted -o /Users/snemeth/Downloads/_personal/_webpages/sorted -c categories.json -y --remove-moved-lines 
```