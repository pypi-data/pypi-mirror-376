# Word2Vec + Matryoshka

Rust + PyO3 backed Python library implementing Word2Vec (Skip‑gram/CBOW) with Negative Sampling (NS) and Hierarchical Softmax (HS), extended with Matryoshka multi‑level representations (prefix vectors). The public API mirrors gensim where sensible (`Word2Vec`, `KeyedVectors`, `wv[...]`, `wv.most_similar`), and all vectors are returned as `numpy.ndarray`.

## Quickstart (uv + maturin)

```bash
uv sync
uv add --dev ruff pytest maturin
uvx maturin develop
uv run -m pytest -q
```

To enable optional performance features at build time:

```bash
# AVX/SSE accelerated dot/AXPY (runtime‑detected)
uvx maturin develop --features simd

# Fast sigmoid approximation (minor accuracy trade‑off)
uvx maturin develop --features fast_sigmoid

# Combine multiple features
uvx maturin develop --features "simd,fast_sigmoid"
```

## Usage

```python
from word2vec_matryoshka import Word2Vec, KeyedVectors, set_seed

set_seed(42)
texts = [["hello", "world"], ["computer", "science"]]
model = Word2Vec(
    sentences=texts,
    vector_size=100, window=5, min_count=1, workers=4,
    negative=5, sg=1, hs=0, levels=[25, 50, 100],
    alpha=0.025, min_alpha=0.0001,
    verbose=True, progress_interval=1.0,
)
"""
Word2Vec.save/load writes and reads a base path, producing:
  <base>.vocab.json  # vocabulary in ivocab order
  <base>.npy         # float32 matrix (rows=len(vocab), cols=vector_size)
The base can be any string (e.g., "word2vec.model"); the two files will be created next to it.
"""
model.save("word2vec.model")

model = Word2Vec.load("word2vec.model")
model.train([["hello", "world"]], total_examples=1, epochs=1)

vec = model.wv["computer"]                    # numpy.ndarray (full dimension)
sims = model.wv.most_similar("computer", topn=10, level=50)  # prefix level

model.wv.save("word2vec.wordvectors")
wv = KeyedVectors.load("word2vec.wordvectors", mmap="r")   # zero‑copy memmap
vec50 = wv.get_vector("computer", level=50)

# Inspect vocabulary and matrix
print(wv.index_to_key[:5])            # ['computer', 'hello', ...] in index order
M = wv.vectors                        # 2D numpy array (n_keys, vector_size)
print(M.shape)
```

Constructor notes:

- sentences (iterable of iterables, optional): The sentences iterable can be a simple list of token lists for small corpora. For large corpora, prefer an iterable that streams sentences directly from disk or network to avoid loading everything into memory.
- If you don’t supply sentences, the model is left uninitialized — use this if you plan to ingest/train later or initialize weights in another way.
- alpha (float, optional): Initial learning rate (default 0.025).
- min_alpha (float, optional): Learning rate linearly decays to this value over training (default 0.0001).
- verbose (bool, optional): Enable gensim-style training progress logging via Python `logging` (default True; can be overridden per `train`).
- progress_interval (float, optional): Seconds between progress updates when logging or callback is enabled (default 1.0; can be overridden per `train`).

Deferred ingestion example:

```python
from word2vec_matryoshka import Word2Vec

# Initialize without sentences (uninitialized model)
m = Word2Vec(vector_size=64, window=5, min_count=1, workers=2, levels=[16, 32, 64])

# Provide a restartable streaming iterable later
class Corpus:
    def __iter__(self):
        # stream from disk/network in real use
        yield ["hello", "world"]
        yield ["computer", "science"]

corpus = Corpus()
m.train(corpus, epochs=2)

# Now you can query vectors
vec = m.wv["hello"]
```

Important: for `epochs > 1` or multiple `train` calls, the iterable must be restartable — implement `__iter__` to return a fresh iterator each time. Avoid one‑shot generators that exhaust after the first pass.

### Training Progress (gensim-style logging)

This library integrates with Python `logging` to emit gensim-like progress lines when `verbose=True`.

```python
import logging
from word2vec_matryoshka import Word2Vec

# Configure logging to match gensim's default look
logging.basicConfig(
    format="%(asctime)s: %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

corpus = [["hello", "world"], ["computer", "science"]] * 2000
model = Word2Vec(sentences=corpus, vector_size=64, workers=4)

# Emits lines like:
# 2025-09-12 21:06:40: INFO: PROGRESS: at 99.24% tokens, alpha 0.00019, 95350 tokens/s
model.train(corpus, epochs=2, verbose=True, progress_interval=0.5)

# You can also set defaults at construction and omit them here:
m2 = Word2Vec(sentences=corpus, vector_size=64, verbose=True, progress_interval=0.5)
m2.train(corpus, epochs=1)  # uses model-level defaults
```

- Logger name: `word2vec_matryoshka` (set level/handlers on this logger to control output).
- Messages are rate-limited by `progress_interval` seconds and include an end-of-epoch flush.
- Default behavior is silent (no logging) unless `verbose=True` or a `progress` callback is supplied.

You can still use a Python callback if you prefer manual handling of progress (logger can be off or on):

```python
def on_progress(done: int, total: int) -> None:
    pass  # e.g., update a progress bar

model.train(corpus, epochs=2, progress=on_progress, progress_interval=0.5)

# or combine with verbose logging
model.train(corpus, epochs=1, progress=on_progress, verbose=True)
```

Files created by the above code:

- Model save: `word2vec.model.vocab.json`, `word2vec.model.npy`
- KeyedVectors save: `word2vec.wordvectors.vocab.json`, `word2vec.wordvectors.npy`

## Streaming Training

- `sentences` can be any restartable iterable of token sequences: each epoch must be able to iterate again (define `__iter__` to return a fresh iterator; avoid one‑shot generators).
- With `workers=1`, training is truly streaming and does not materialize the full corpus.
- With `workers>1`, a bounded prefetch queue batches sentences per epoch for parallel compute (to avoid cross‑thread access to a Python iterator).

Example: restartable iterable

```python
from word2vec_matryoshka import Word2Vec

class RestartableCorpus:
    def __init__(self, data):
        self._data = list(data)
    def __iter__(self):
        for sent in self._data:
            yield list(sent)

corpus = RestartableCorpus([["hello", "world"], ["computer", "science"], ["hello", "computer"]])
model = Word2Vec(sentences=corpus, vector_size=32, window=5, min_count=1, workers=1, levels=[16, 32])
model.train(corpus, total_examples=3, epochs=2)
```

Run the built‑in example: `uv run python -m word2vec_matryoshka._streaming_examples`

## Features

- Training: Skip‑gram (`sg=1`) or CBOW (`sg=0`); choose NS (`negative>0` and `hs=0`) or HS (`hs=1`).
- Matryoshka levels: `levels=[...]` defines multiple prefix dimensions (defaults to `[d/4, d/2, d]` if omitted). Each prefix is optimized, enabling multi‑granularity queries.
- Vector persistence: `KeyedVectors.save("base")` produces `base.vocab.json` and `base.npy` (float32, C‑order). `KeyedVectors.load("base", mmap='r')` uses NumPy memmap for zero‑copy. `most_similar` on mmap uses NumPy vectorized dot and norms for performance.
- Model persistence: `Word2Vec.save/load("base")` writes and reads the same `base.vocab.json` + `base.npy` format as `KeyedVectors`, preserving `ivocab` order and using atomic writes.
- Determinism: `set_seed(seed)` for reproducible training; per‑thread RNGs derive from the base seed.
- Parallelism: uses `rayon` with lock striping for safe, concurrent updates; optional SIMD acceleration available via `--features simd`.

### Performance Options

- `--features simd`: enables x86_64 AVX/SSE and aarch64 NEON intrinsics for core dot and AXPY (update) operations with runtime detection. Falls back to scalar on unsupported CPUs.
- `--features fast_sigmoid`: uses a smooth approximation `0.5 + 0.5 * x / (1 + |x|)` instead of `exp`‑based sigmoid; improves throughput in activation‑heavy paths with small accuracy impact.
- Thread‑local buffers: CBOW paths reuse per‑thread buffers to reduce allocations (enabled by default; no action required).
- Workers: tune `workers` to available cores; `workers>1` uses parallel compute with a bounded prefetch.
- Levels: fewer/lower levels reduce compute; `[d/4, d/2, d]` is a balanced default.

## Layout (excerpt)

```
src/                       # Rust core (PyO3 module: word2vec_matryoshka._core)
python/word2vec_matryoshka # Python package (re‑exports _core)
tests/                     # Pytests: API, IO, mmap, streaming, HS/NS, matryoshka

### Internal Rust module structure

```
src/
  lib.rs           # PyO3 entry, high‑level types, logging/RNG glue
  io/npy.rs        # NPY read/write helpers
  ops/             # math kernels, SIMD paths, thread‑local buffers
  weights.rs       # striped‑lock shared weights (SharedWeights, SHARDS)
  training/
    ns.rs          # SG/CBOW + Negative Sampling (seq + striped)
    hs.rs          # Hierarchical Softmax + Huffman
  sampling/
    alias.rs       # alias method build/sample
```

This split keeps unsafe/SIMD and concurrency concerns localized and makes training variants easy to extend.

### Dev quality gates

- Rust: `cargo fmt` and `cargo clippy -- -D warnings` must pass.
- Python: `uv run ruff check .` and `uv run ruff format .` for lint/format.
```

## Tips

- For production, prefer `mmap='r'` when loading read‑only vectors to reduce memory. If you need a writable/contiguous copy, call `.copy()` on the NumPy array in Python.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Micro‑benchmark and HS/NS switch

```python
import time
from word2vec_matryoshka import Word2Vec

corpus = [[f"w{i}" for i in range(200)] for _ in range(200)]

def bench(**kw):
    t0 = time.perf_counter()
    m = Word2Vec(
        sentences=corpus, vector_size=128, window=5, min_count=1,
        workers=4, levels=[32, 64, 128], **kw
    )
    m.train(corpus, total_examples=len(corpus), epochs=1)
    return time.perf_counter() - t0

print("NS (negative=5):\t", bench(negative=5, sg=1, hs=0))
print("HS:            \t", bench(negative=0, sg=1, hs=1))
```

Rules of thumb: with large vocabularies/high dimensions NS is often faster with good accuracy; HS can be more stable for smaller vocabs or long‑tail focus. Matryoshka levels work with both.

## Troubleshooting

- After `uvx maturin develop`, run tests via `uv run -m pytest -q` so pytest sees the dev‑installed extension.
- If you interact with Python objects from background threads, bind them under the GIL in that thread. Avoid holding the GIL while blocking on channels; wrap long or blocking sections in `Python::with_gil(|py| py.allow_threads(|| { ... }))`.
- When cloning PyO3 handles, use `clone_ref(py)` under the GIL rather than `clone()` on `Py<T>`.
 - To run the test suite with features enabled, build the extension with the same features before invoking pytest, e.g. `uvx maturin develop --features simd && uv run -m pytest -q`.

### Migration note (save/load)

- If you previously saved a full model as a single JSON file, switch to the base‑path pattern shown above. Using the same base (even if it ends with `.json`) is fine; the library will create `<base>.vocab.json` and `<base>.npy` alongside it.
- For very large models, prefer loading vectors via `KeyedVectors.load(base, mmap='r')` for minimal memory usage and fast startup.
