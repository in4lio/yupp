# Evaluator semantics and migration

The evaluator now has a defined scope, reduction, and suspension model. Lambda
functions are lexical. Macros, `EVAL` (`$$`), and explicit late-bound names are
the language's caller-context mechanisms. There is no legacy dynamic-scope
mode.

## Language contract

- A lambda captures the environment in which it is defined. Each full or
  partial application has fresh parameter state; calling a closure never
  changes the closure template.
- A regular free name is resolved through the lambda's invocation frame and
  lexical definition chain only.
- `&name` resolves through the caller of the application or residual resumption
  that first demands it. A declared late parameter such as
  `\dependency..\function.` retains the same explicit late-binding behavior.
- Macro arguments, substitution, parsing, and the expanded form use the macro
  invocation context. `EVAL` input and its parsed form use the context in which
  that `EVAL` begins.
- A macro or `EVAL` already in progress retains its original operation context
  across suspension. A nested dynamic operation first reached after resumption
  uses the resumption caller.
- Parameter defaults are evaluated once, at lambda definition time. A default
  that remains residual retains that lexical definition context.
- Applications reduce the callee first, then positional and named operands in
  written source order. Reduction stops at the first residual operand; later
  operands are untouched.
- A conditional evaluates only its condition and selected branch. An
  unresolved condition does not evaluate either branch.
- Completed effects are removed from the remaining residual work. Following a
  residual produces one continuation chain; resuming the same earlier
  checkpoint creates independent forks, so effects before the checkpoint do
  not repeat and effects after it may occur once in each fork.
- Parsed ASTs, reusable closures, and supplied residuals are not mutated by
  evaluation.

## Migrating accidental dynamic lookup

Code that relied on a regular lambda name being supplied by its caller must
make that dependency explicit. For example, this old pattern is no longer
dynamic:

```text
($set render \value.($format prefix value))
```

If `prefix` is ordinary data, pass it as an argument:

```text
($set render \prefix.\value.($format prefix value))
($render prefix value)
```

If caller-time lookup is intentional, use late binding:

```text
($set render \value.($format &prefix value))
```

The declared late-parameter form remains available when an argument expression
has named late dependencies:

```text
($ \param..\func.\val.($func val) ($upper &param) "late bound param")
```

Prefer explicit arguments for ordinary data flow. Reserve late binding for
call-site-sensitive language behavior.

## Runtime migration warning

The optional warning reports an executed regular reference that is absent from
the lambda's lexical environment but present in its invocation caller. It is a
presence check only: the caller value is never substituted and the lexical
result is unchanged.

Enable it for one command:

```console
yupp -Wdynamic-scope source.yu-c
```

Disable an inherited command-line setting with `-Wno-dynamic-scope`. A trusted
`.yuconfig` can enable the same check:

```python
warn_dynamic_scope = True
```

Warnings are emitted once per source occurrence in one evaluation chain,
retain macro and `EVAL` inclusion provenance, and explicitly recommend an
argument or late binding. This is runtime-only analysis: unexecuted branches
are not checked.

## Compatibility delta

| Surface | Previous behavior | Current behavior | Contract and migration |
|---|---|---|---|
| Legacy evaluator records 01-13 | Established exact output and diagnostics | All 13 records remain exact | Supported application, recursion, macro, `EVAL`, late-binding, and diagnostic surfaces remain compatible (R15, R20) |
| Tracked generated examples | Repository golden files | All 17 source cases regenerate byte-for-byte after declared timestamp normalization | `switch.py` now marks `p-val` as late-bound explicitly; generated output is unchanged |
| `eg/switch.py` pattern body | Regular `p-val` references relied on the enclosing switch invocation | Uses `&p-val` at the three caller-context sites | R2, R5; F1/F4. This is the source migration pattern for intentional caller lookup |
| Regular lambda free name found only in caller | Could resolve through accidental hybrid dynamic scope | Does not use the caller value; lambda lookup is lexical | R2, R4; F1; AE1. Pass an argument or use `&name` |
| Explicit late name | Caller-context lookup | Caller-context lookup through the completing application or resumption | R5; F4; AE2, AE10, AE12. No migration |
| Unresolved conditional | Could reduce both branches, perform an unselected effect, or raise an unselected error | Evaluates neither branch until the condition resolves, then evaluates only the selected branch | R8, R11; F3; AE3-AE5. Move any intentionally eager work before the conditional |
| Application with a residual operand | Later operands could be visited and the input tree could retain reducer mutations | Stops at the first residual in written order and returns a new residual | R7, R9, R11; F2; AE4, AE13 |
| Reusing an AST, closure, or residual | Prior evaluation could change later results | Inputs are reusable; each result or fork has independent remaining work | R3, R7, R12-R14; AE6, AE7 |

No legacy fixture or generated example changed output. One example template
was migrated from accidental lookup to explicit late binding; the observable
semantic deltas are otherwise isolated by the focused tests and are intentional
corrections listed above.

## Scaling evidence

The benchmark command is:

```console
PYTHONPATH=src python script/benchmark_yueval.py --sizes 25 50 100 200 400
```

The original evaluator copied captured environments during call setup. Its
measured copied-binding series was `675, 2600, 10200, 40400, 160800`, classified
as definitions-by-calls growth. The current evaluator reports zero environment
deep copies, zero copied bindings, and zero captured-ancestor enumeration at
every size.

| Definitions / calls | Old seconds | Current seconds | Current call frames | Target + demanded lookup visits |
|---:|---:|---:|---:|---:|
| 25 | 0.00247 | 0.00131 | 50 | 25 + 25 |
| 50 | 0.01119 | 0.00255 | 100 | 50 + 50 |
| 100 | 0.06355 | 0.00519 | 200 | 100 + 100 |
| 200 | 0.41222 | 0.01025 | 400 | 200 + 200 |
| 400 | 2.89138 | 0.02071 | 800 | 400 + 400 |

Elapsed time is illustrative and is not a cross-platform CI threshold. The
blocking evidence is structural: call-state creation performs constant work
per call and never copies or enumerates unrelated captured definitions.
