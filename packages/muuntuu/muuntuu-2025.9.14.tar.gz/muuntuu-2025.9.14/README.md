# Muuntuu

Transforms (Finnish: muuntuu) helper tool.

## Usage:

```erlang
❯ muuntuu
usage: muuntuu [-h] [--source FILE] [--target FILE] [--debug] [--policy-writer POLICY_WRITER]
               [--general-offset GEN_OFFSET] [--mapping-offset MAP_OFFSET] [--sequence-offset SEQ_OFFSET]
               [--width WIDTH] [--default-flow-style] [--sort-base] [--force] [--quiet] [--version]
               [SOURCE_FILE] [TARGET_FILE]

Transforms (Finish: muuntuu) helper tool.

positional arguments:
  SOURCE_FILE           JSON or YAML source as positional argument
  TARGET_FILE           JSON or YAML target as positional argument

options:
  -h, --help            show this help message and exit
  --source FILE, -s FILE
                        JSON or YAML source
  --target FILE, -t FILE
                        JSON or YAML target
  --debug, -d           work in debug mode (default: False), overwrites any environment variable MUUNTUU_DEBUG value
  --policy-writer POLICY_WRITER
                        [YAML only] select writer policy from (safe, r[ound-]t[rip], or "empty") (default: safe)
  --general-offset GEN_OFFSET
                        general offset (indent) on output (default: 2) - verify the amount yourself, please
  --mapping-offset MAP_OFFSET
                        [YAML only] mapping offset (indent) on output (default: 2) - verify the amount yourself, please
  --sequence-offset SEQ_OFFSET
                        [YAML only] sequence offset (indent) on output (default: 2) - verify the amount yourself, please
  --width WIDTH         [YAML only] constrain width on output (default: 150) - verify the amount yourself, please
  --default-flow-style  [YAML only] select default flow style on output (default: False)
  --sort-base           [YAML only] sort base mapping type on output (default: False)
  --force, -f           overwrite existing targets (default: False)
  --quiet, -q           work in quiet mode (default: False)
  --version, -V         display version and exit

```

> Note: some combinations of writer policy, offsets, and width may lead to
> invalid YAML as documented in `test/fixtures/offsets-width.yaml` where the
> options `--general-offset 3 --mapping-offset 1 --policy-writer rt --sequence-offset 2 --width 20`
> were used when deriving from `test/fixtures/offsets-width.yaml`:
> 
>```yaml
>foo:
> bar:
>    - baz
>    - quux1 asd asd
>   asd adssssssss
>    - quux2
>    - quux3
>```

## Version

```erlang
❯ muuntuu --vesion
2025.9.14
```

## Status

Prototype.
