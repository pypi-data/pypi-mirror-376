<h1 align="center">sgn-inspect</h1>

<p align="center">Discover and inspect SGN elements and plugins</p>

<p align="center">
  <a href="https://git.ligo.org/greg/sgn-inspect/-/pipelines/latest">
    <img alt="ci" src="https://git.ligo.org/greg/sgn-inspect/badges/main/pipeline.svg" />
  </a>
  <a href="https://git.ligo.org/greg/sgn-inspect/-/pipelines/latest">
    <img alt="ci" src="https://git.ligo.org/greg/sgn-inspect/badges/main/coverage.svg" />
  </a>
  <a href="https://docs.ligo.org/greg/sgn-inspect/">
    <img alt="documentation" src="https://img.shields.io/badge/docs-mkdocs%20material-blue.svg?style=flat" />
  </a>
</p>

---

## Resources

* [Documentation](https://docs.ligo.org/greg/sgn-inspect)
* [Source Code](https://git.ligo.org/greg/sgn-inspect)
* [Issue Tracker](https://git.ligo.org/greg/sgn-inspect/-/issues)

## Installation

With `pip`:

```
pip install git+https://git.ligo.org/greg/sgn-inspect.git
```

## Quickstart

Display information about all installed elements:

```
➜ sgn-inspect
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Element           ┃ Plugin  ┃ Type      ┃ Module             ┃ Description                                                                      ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ DequeSource       │ base    │ source    │ sgn                │ A source element that has one double-ended-queue (deque) per source pad.         │
│ IterSource        │ base    │ source    │ sgn                │ A source element that has one iterable per source pad.                           │
│ NullSource        │ base    │ source    │ sgn                │ A source that does precisely nothing.                                            │
│ CallableTransform │ base    │ transform │ sgn                │ A transform element that takes a mapping of {(input, combinations) -> callable}, │
│ CollectSink       │ base    │ sink      │ sgn                │ A sink element that has one collection per sink pad.                             │
│ DequeSink         │ base    │ sink      │ sgn                │ A sink element that has one double-ended-queue (deque) per sink pad.             │
│ NullSink          │ base    │ sink      │ sgn                │ A sink that does precisely nothing.                                              │
│ ArrakisSource     │ arrakis │ source    │ sgn_arrakis        │ Source element that streams channel data from Arrakis.                           │
│ ArrakisSink       │ arrakis │ sink      │ sgn_arrakis        │ Sink element that streams channel data to Arrakis.                               │
└───────────────────┴─────────┴───────────┴────────────────────┴──────────────────────────────────────────────────────────────────────────────────┘
```

Display information about a particular plugin:

```
➜ sgn-inspect base
┌─────────────┬──────────────────────────────────────────────────────────────────────────────┐
│ Plugin      │ base                                                                         │
│ Description │ A framework to help navigate buffers through a graph. The buffers must flow. │
│ Version     │ 0.1.dev211+gd9a88a1.d20250423                                                │
│ License     │ MPL-2.0                                                                      │
│ Project URL │ https://git.ligo.org/greg/sgn                                                │
└─────────────┴──────────────────────────────────────────────────────────────────────────────┘
                                                       Plugin Elements                                                       
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Element           ┃ Type      ┃ Module ┃ Description                                                                      ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ DequeSource       │ source    │ sgn    │ A source element that has one double-ended-queue (deque) per source pad.         │
│ IterSource        │ source    │ sgn    │ A source element that has one iterable per source pad.                           │
│ NullSource        │ source    │ sgn    │ A source that does precisely nothing.                                            │
│ CallableTransform │ transform │ sgn    │ A transform element that takes a mapping of {(input, combinations) -> callable}, │
│ CollectSink       │ sink      │ sgn    │ A sink element that has one collection per sink pad.                             │
│ DequeSink         │ sink      │ sgn    │ A sink element that has one double-ended-queue (deque) per sink pad.             │
│ NullSink          │ sink      │ sgn    │ A sink that does precisely nothing.                                              │
└───────────────────┴───────────┴────────┴──────────────────────────────────────────────────────────────────────────────────┘
```

Display information about a particular element:

```
➜ sgn-inspect DequeSource
┌─────────┬─────────────┐
│ Element │ DequeSource │
│ Plugin  │ base        │
│ Type    │ source      │
│ Module  │ sgn         │
└─────────┴─────────────┘

A source element that has one double-ended-queue (deque) per source pad.

    The end of stream is controlled by setting an optional limit on the number
    of times a deque can be empty before EOS is signaled.

    Args:
        iters:
            dict, a mapping of source pads to deque s, where the
            key is the pad name and the value is the deque
        eos_on_empty:
            Union[dict, bool], default True, a mapping of source
            pads to boolean values, where the key is the pad name and the value
            is the boolean. If a bool is given, the value is applied to all
            pads. If True, EOS is signaled when the deque is empty.

```
