# Marko: `fenced_divs`

This is an extension for [Marko](https://marko-py.readthedocs.io/) providing support
for [fenced divs as detailed by pandoc](https://pandoc.org/demo/example33/8.18-divs-and-spans.html).

It allows you to wrap parts of the Markdown text in a div or other html element without having
to resort to html directly.

Like this:

```markdown
Just plain Markdown here, followed by a `fenced div`.

:::wrapper
This _will_ be wrapped.
:::

And continue doing your thing down here.
```

You can use a many colons as you want. And yes, you can nest.

## Examples

### Simple
The text after the opening colons is used as the `class` attribute
for the div.

```markdown
# A title
Some text in a paragraph.

:::className
All of this will be wrapped in a `<div class="className">`.

Yes, even this list:

1. First
2. Second
:::

And this will just be another paragraph.
```

### With attributes
If you need more control, you can specify attributes explicitly by wrapping
them in curly braces.

```markdown
# A title
Some text in a paragraph.

::: { #my-id .something active="true" <section> }
All of this will be wrapped in a 
`<section id="my-id" class="className" active="true">`.

Yes, even this list:

1. First
2. Second
:::

And this will just be another paragraph.
```

## Usage

1. Install `roamkit-marko-fenced-divs` from Pypi.
2. Add `roamkit.marko.fenced_divs` as an extension.

```python
from marko import Markdown


def convert_to_html(md_text: str) -> str:
    # codehilite is just an example of another extension.
    engine = Markdown(
        extensions=["roamkit.marko.fenced_divs", "codehilite"],
    )
    return engine.convert(md_text)
```
