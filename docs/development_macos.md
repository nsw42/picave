# Setting up your development environment on macOS

## Set up the python virtualenv

See [development_common.md](development_common.md)

## Install platform-specific dependencies

* Install pygobject: See <https://pygobject.readthedocs.io/en/latest/getting_started.html#macosx-getting-started>
    * Note that this didn't play nice with my virtualenv, and I ended up kludging it:

```sh
for d in /usr/local/Cellar/pygobject3/3.34.0/lib/python3.7/site-packages/*; do
  ln -s $d ~/.pyenv/versions/picave/lib/python3.7/site-packages/`basename $d`;
done
```

### Install common dependencies

See [development_common.md](development_common.md)
