# Language evolution

## Status and purpose

This document records a direction for the language after the 2.0 evaluator
work. It is a design note, not a second language specification and not a
deprecation announcement.

The [language guide](README.md) describes the supported surface. The
[evaluator migration guide](yueval-migration.md) is the authoritative record
of the scope, reduction, suspension, and compatibility decisions already made
for 2.0. Proposals below become language contracts only after they have their
own decision, implementation, compatibility analysis, and tests.

## Language identity

yupp is best understood as a staged text-generation language embedded in an
ordinary source file. It is not merely an alternative C preprocessor and it is
not a general-purpose Lisp:

- ordinary source text passes through to the generated file;
- `($...)` applications enter the macro language;
- macro-language expressions can produce values, syntax, or source text;
- an expression that cannot yet finish can remain as residual work and resume
  after its missing context becomes available;
- macros, `EVAL`, and explicit late names provide controlled access to the
  context in which staged work is performed.

That combination is the distinctive part of the language. It supports
generators that remain close to their target language and produce readable,
navigable output while still offering functions, recursion, macros, imports,
and multiple output files.

## How the model evolved

The original evaluator favored flexibility. A definition could indirectly see
call-site state, values of several kinds could act as functions, and an
unfinished expression could be revisited later. This made compact generators
possible, but it also left important behavior dependent on evaluator details.
In particular, ordinary lambda lookup mixed lexical and caller scope, mutable
evaluation records could leak state between reductions, and call setup copied
captured environments as the definition tree grew.

The 2.0 evaluator work turned those implementation effects into an explicit
language model:

- lambdas are lexical by default;
- caller-time lookup is written explicitly with `&name`;
- macros and `EVAL` retain their defined dynamic-operation contexts;
- callee and operands reduce in source order and stop at the first residual;
- an unresolved condition evaluates neither branch;
- reusable ASTs, closures, and residuals are not mutated;
- a resumed residual is a continuation whose forks have independent remaining
  work;
- call frames reference lexical environments instead of copying growing
  definition trees.

This was a semantic correction as well as a performance improvement. It made
local reasoning possible without removing the staged behavior for which the
language exists.

## Principles worth preserving

### Make evaluation visible

A list `(a b c)` and an application `($f a b c)` are visibly different.
Embedding into host text also requires an application or a source enclosure.
This explicit boundary is valuable and should remain obvious in any future
syntax.

### Prefer lexical data flow

Ordinary dependencies should be parameters or lexical bindings. Late binding
is useful for genuinely call-site-sensitive generation, but `&name` should
remain an explicit signal rather than becoming a second default lookup rule.

### Keep staging first-class

Residual evaluation is not just an error-recovery mechanism. It lets a macro
describe work before every value is available. Future simplification should
make this model easier to explain and inspect, not accidentally reduce yupp to
eager string substitution.

### Generate readable source

Formatting, source provenance, diagnostics, and multiple coordinated outputs
are language-level product qualities. A shorter implementation is not an
improvement if generated code becomes opaque or loses navigation back to its
origin.

### Define effects precisely

Evaluation order matters because definitions, imports, output selection,
printing, and host-language expressions can have effects. Effects before a
residual checkpoint must not be repeated accidentally; effects reached after
independent forks may occur in each fork. New features need equally explicit
rules.

### Keep one semantic mode

Compatibility should be provided through source migration, additive forms,
and diagnostics. A permanent switch between incompatible evaluators would
split the language and make every library dependent on hidden runtime state.

## Current design pressure

The language has accumulated several compact ways to express common
operations. Their convenience is real, but each one increases the amount of
syntax and type-directed behavior a reader must remember.

| Surface | Existing value | Design cost | Possible direction |
|---|---|---|---|
| Applying a number | Concise indexing | The meaning of application depends on the callee's runtime type | Evaluate promoting the existing `$getitem` form as the canonical named spelling; retain number application as compatible shorthand |
| Applying a list | Compact iteration | Iteration looks like an ordinary call and hides evaluation details | Document a named mapping/iteration form as canonical |
| Applying a string and `$$` | Concise formatting and parsed evaluation | Formatting, substitution, parsing, and evaluation are visually close | Give formatting and staged evaluation distinct canonical names |
| Backquote, `[]`, reverse brackets, `,,...,,`, and `$code` | Convenient source and quoting forms in different contexts | Several delimiters overlap and increase parser and documentation complexity | Evaluate promoting the existing `($quote ...)` and `($code ...)` forms as canonical while preserving the other spellings |
| Python expressions in `{...}` | Immediate access to a mature host runtime | Security, portability, and yupp/Python semantic boundaries become implicit | Make host interoperation visibly namespaced and keep it within the trusted-input boundary |
| Genuinely unresolved application or residual work | Enables staged evaluation; an ordinary unbound atom is a terminal textual identifier in 2.0 | Missing context inside staged work can look intentional | Add strict finalization diagnostics without making intermediate residuals illegal |
| Explicit late binding and declared late parameters | Supported caller-context mechanisms in the 2.0 staging contract | Context-sensitive behavior needs the operation-context and resumption rules to remain visible | Keep them in the staging layer and prefer lexical parameters for ordinary data flow |
| Scalar `($emit <atom> <function>)` and variadic lambda forms | Explore terse stateful and higher-order generation | The language guide explicitly marks these forms experimental | Keep them in the experimental tier until their unique use cases are demonstrated |

This note does not choose any new names or spellings. `$getitem`,
`($quote ...)`, and `($code ...)` are already accepted named forms; the possible
directions above concern whether documentation should promote them. Any
additional canonical names require a separate design decision and a conflict
check against existing libraries.

## A layered feature model

The supported language can be easier to learn without immediately removing
anything. Documentation and future design can classify features by role.

### Semantic core

The core contains atoms and literal values, lists, explicit application,
lambdas, lexical bindings, definitions, quotation, conditions, and one
canonical way to enclose generated source. A reader should be able to predict
these forms using lexical scope and written evaluation order alone.

### Staging and metaprogramming

Residual expressions, macros, `EVAL`, and explicit late binding form the
staging layer. These features are central to advanced yupp programs, but they
need the vocabulary of operation context, suspension, resumption, and forked
continuations introduced by the 2.0 contract.

### Generation services

Imports, standard libraries, passages, output-file selection, titles, and
source navigation support real generation workflows. They should be described
as services around the evaluator rather than unrelated evaluator special
cases.

### Host interoperation

Python expressions and imported Python functions are a trusted escape hatch.
They are practical, but they should have an explicit boundary and should not
silently define the meaning of the language core.

### Compatibility and experimental surface

Polymorphic application shortcuts and alternative source delimiters can remain
supported compatibility forms while being absent from the introductory path.
The scalar `emit` modifier and variadic lambda forms are the constructs in this
group that the language guide explicitly marks experimental. Explicit late
binding and declared late parameters remain part of the supported staging
contract. A feature moves toward the core only when it is orthogonal,
explainable, scalable, diagnosable, and covered by a clear compatibility
contract.

## Proposed directions

### 1. Freeze and specify the 2.0 core

The immediate priority is to keep the current evaluator contract stable. A
compact semantic reference should eventually define:

- value and expression categories;
- lexical frames and explicit operation contexts;
- application and conditional reduction order;
- residual creation, resumption, and forking;
- effect boundaries;
- macro substitution and `EVAL` context;
- the point at which an unresolved expression becomes a diagnostic.

The reference should be executable where practical: each rule should map to a
small semantics test, while generated examples continue to protect complete
source-to-output behavior.

### 2. Introduce canonical forms additively

Where runtime type currently changes the meaning of an application, a named
form could make intent explicit. The existing compact spelling can remain valid
as sugar. New documentation and libraries would prefer the canonical form,
allowing the language to become more regular without a flag day.

The same approach can reduce the apparent number of quoting and source-block
mechanisms: select canonical forms for new code, document the exact role of
each older delimiter, and avoid changing their output.

### 3. Make unresolved work inspectable

Residuals need first-class diagnostics. Useful tooling could report why a form
is suspended, which names it demands, where its operation context began, and
which effects have already completed. A strict finalization mode could reject
genuinely unfinished residual work at the output boundary without treating
terminal unbound atoms as errors or making intermediate residuals illegal.

This also creates a place for warnings about accidental experimental syntax,
ambiguous host access, or effects that may execute independently after a fork.

### 4. Clarify the Python boundary

Host expressions are valuable for arithmetic, string processing, and access
to existing libraries. Their use should nevertheless be visible in source and
documentation. Possible future work includes explicit namespaces, a smaller
default host surface, and configuration of additional host functions for
trusted projects.

Any such change must account for existing generators and remain consistent
with the rule that yupp input and configuration are trusted code.

### 5. Separate pure reduction from generation effects

The language does not need a static effect type system, but its documentation
and diagnostics can distinguish pure computations from operations that mutate
bindings, load modules, select output, print, or execute host code. This would
make suspension and fork behavior easier to predict and would give future
features a clear review question: can the operation safely be repeated, and
at what point is it committed?

### 6. Provide deliberate macro-local naming

Macros intentionally operate in invocation context, so automatic Lisp-style
hygiene may not match yupp's text-generation model. Still, large macro
libraries need a reliable way to create local names without accidental
capture. An explicit local-binding or generated-name facility may be a better
fit than silently rewriting all macro identifiers.

This requires its own design: generated host-language names and evaluator
bindings have different collision rules.

### 7. Improve the learning path before adding features

The introductory language should be teachable with a small set of forms.
Advanced syntax can remain fully documented in a later section with its
evaluation rules and motivating use cases. Examples should demonstrate one
preferred spelling first and compatibility spellings only when maintaining
older code.

## Compatibility policy for evolution

Language evolution should follow these constraints:

1. Treat the 2.0 evaluator rules as the compatibility baseline.
2. Add canonical forms before discouraging compatible shorthand.
3. Require characterization tests for every affected legacy form.
4. Preserve byte-equivalent generated examples unless an observable change is
   explicitly approved.
5. Introduce opt-in diagnostics before default warnings, and default warnings
   before considering removal.
6. Remove supported syntax only in a major release and only when a mechanical
   migration exists.
7. Do not preserve old behavior through a second evaluator or hidden semantic
   mode.

Performance is part of this policy. A feature whose call setup or lookup cost
grows with unrelated definitions should not enter the stable core even if its
small examples are correct.

## Open design questions

The following questions should remain explicit rather than being answered by
implementation accident:

- How should future diagnostics distinguish an ordinary unbound atom, which is
  a terminal textual identifier today, from genuinely unresolved application
  or residual work?
- Which source enclosure and quotation forms should be canonical?
- Which polymorphic applications have enough real-world value to remain
  prominent?
- What information must a residual expose for diagnostics and tooling?
- Should strict finalization be opt-in per invocation, per project, or a future
  default?
- How small can the default Python surface become without harming the main use
  cases?
- What explicit local-name facility would help macros without imposing full
  hygiene?
- Which experimental features solve problems that cannot be expressed clearly
  by the semantic core and staging layer?

These are decision points, not a release checklist. They should be resolved
with representative programs, compatibility fixtures, and scaling evidence.

## Non-goals

The proposed direction does not aim to turn yupp into a general-purpose
language, replace the parser solely for syntactic fashion, understand the AST
of every possible target language, or remove unusual syntax merely because it
is unusual. The goal is a smaller conceptual model, explicit staging, and a
clear path from existing programs to more readable new ones.

## Perspective

yupp has academic interest because it combines lexical functions, dynamic
metaprogramming operations, partial evaluation, continuations, and text
generation in a compact language. It also has a practical niche: producing
coordinated, readable C, C++, Python, and other text artifacts from a source
that remains close to its output.

Its main limitation is no longer a lack of expressive power. The next stage of
language maturity is to organize that power: stabilize the semantic core,
make advanced context dependence explicit, prefer canonical forms, and let
diagnostics guide compatible source migration.
