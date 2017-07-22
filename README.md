[![Build Status](https://travis-ci.org/cs50/submit50.svg?branch=master)](https://travis-ci.org/cs50/submit50)

# Usage

## English

```
submit50 problem
```

### Spanish

```
LANGUAGE=es submit50 problem
```

# Internationalizing

## Creating PO for language XX

```
xgettext submit50.py
sed -i -e '1,6d' messages.po
sed -i -e '3,10d' messages.po
sed -i 's/CHARSET/UTF-8/' messages.po
vim messages.po # translate strings to XX
msgfmt messages.po
mkdir -p locale/XX/LC_MESSAGES
mv messages.mo messages.po locale/XX/LC_MESSAGES/
```

## Updating PO for language XX

Source: https://stackoverflow.com/a/7497395

```
echo "" > messages.po
find . -type f -iname "*.py" | xgettext -j -f -
msgmerge -N locale/XX/LC_MESSAGES/messages.po messages.po > new.po
mv new.po messages.po
msgfmt messages.po
mv -f messages.mo messages.po locale/XX/LC_MESSAGES/
```

# Contributing

```
pip install -e .
```

TODO
