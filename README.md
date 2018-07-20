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

## Adding a new language

1. First, ensure that `babel` is installed and that `submit50` is installed in development mode:

        pip install babel
        pip install -e .

2. Generate the translation template:

        python setup.py extract_messages

3. Generate the `.po` file for the desired language:

        python setup.py init_catalog -l <LANG>

    where `<LANG>` is the code of the language you want to translate (e.g., `es` for Spanish, `en` for English, etc.) 

4. Then, add the translations to the newly created `submit50/locale/<LANG>/LC_MESSAGES/submit50.po`

5. Finally, compile the new translations:

        python setup.py compile_catalog

    and test them:

        LANGUAGE=<LANG> submit50 <PROBLEM>

## Updating an existing language

Follow the steps described in the above section, but instead of running `python setup.py init_catalog -l <LANG>`, run `python setup.py update_catalog -l <LANG>`. 
