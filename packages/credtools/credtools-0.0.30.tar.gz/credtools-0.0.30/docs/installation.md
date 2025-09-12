# Installation

CREDTOOLS requires Python 3.9 or higher. The base installation includes all dependencies needed for fine-mapping analysis.

## Basic Installation

To install the base CREDTOOLS package, run this command in your terminal:

```bash
$ pip install credtools
```

This is the preferred method to install CREDTOOLS, as it will always install the most recent stable release.

## Web Visualization

To use the interactive web interface, install with web dependencies:

```bash
$ pip install credtools[web]
```

## Development Installation

For development, you may want to install CREDTOOLS in "editable" mode:

```bash
$ git clone https://github.com/Jianhua-Wang/credtools.git
$ cd credtools
$ pip install -e .
```

Check that CREDTOOLS is installed correctly:

```bash
$ credtools --help
```

For web visualization:

```bash
$ credtools web --help
```

## Conda Installation

You can also install CREDTOOLS using conda:

```bash
$ conda install -c conda-forge credtools
```

## Source

The source for CREDTOOLS can be downloaded from the [Github repo][].

You can either clone the public repository:

```bash
$ git clone git://github.com/Jianhua-Wang/credtools
```

Or download the [tarball][]:

```bash
$ curl -OJL https://github.com/Jianhua-Wang/credtools/tarball/master
```

Once you have a copy of the source, you can install it with:

```bash
$ cd credtools
$ pip install -e .
```

## Web Dependencies

The web visualization requires additional dependencies. You can install them with:

```bash
$ pip install credtools[web]
```

If you don't have root access, you can install for your user only:

```bash
$ pip install --user credtools[web]
```

## Troubleshooting

If you encounter any issues during installation, please check:

1. Python version (3.9+ required)
2. pip is up to date
3. You have write permissions for the installation directory

For web visualization issues, ensure all web dependencies are installed:

```bash
$ pip install credtools[web]
```

## Links

* [Github repo]: https://github.com/Jianhua-Wang/credtools
* [tarball]: https://github.com/Jianhua-Wang/credtools/tarball/master
