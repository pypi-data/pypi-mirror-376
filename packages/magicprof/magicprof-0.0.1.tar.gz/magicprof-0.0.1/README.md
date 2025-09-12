Automatically instrumented python profiling.

### Usage

```shell
env MAGICPROF=cpu.prof python <app.py> # if MAGICPROF not set, profiling is not instrumented.

# other options:
# MAGICPROF_DISABLE_SUBCALLS # set to anything to disable subcalls. see cProfile.Profile.
# MAGICPROF_DISABLE_BUILTINS # set to anything to disable subcalls. see cProfile.Profile.
```

Use a tool like [`snakeviz`](https://jiffyclub.github.io/snakeviz/) to visualize the profile.

```shell
# e.g.
snakeviz cpu.prof
```

### Install

```shell
# create python virtual environment
uv venv
uv pip install 'git+https://github.com/aaraney/magicprof@v0.0.1'
```

