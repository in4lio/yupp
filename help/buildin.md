### Build-in Functions

 | Various functions
--- | :---
`($__FILE__)` | Name of the current preprocessed file.
`($__OUTPUT_FILE__)` | Name of the output file.
`($__MODULE_NAME__)` | Return an uppercase base name of the current preprocessed file without extension. All hyphens are replaced with underscores.
`($__TITLE__)` | Insert comment with file info.
`($car list)` | Head of a list.
`($cdr list)` | Tail of a list.
`($getslice seq start [end [step]])` | Slicing `seq[start:end:step]`.
`($islist x)` | Check an argument is a list.
`($lazy par)` | _Experimental_. Allow to get specific item of `__va_args__` or length of `__va_args__` in case `__va_args__` contains lambda.
`($len list)` | Length of a list.
`($list ...)` | Create a list of arguments.
`($print ...)` | Print arguments to `<stdout>`.
`($q str)` | Quote a string.
`($range end)`<br>`($range start end [step])` | Create a list containing arithmetic progression.
`($repr x)` | Return a string containing a printable representation of an argument.
`($seqiter [start [step]])` | Make an iterator that returns evenly spaced values starting with number start.
`($str x)` | Return a string containing a nicely printable representation of an argument.
`($unq str)` | Unquote a string.
 | **Functions imported from Python `operator` module**
`($add a b)` | Addition `a + b`.
`($concat seq1 seq2)` | Concatenation `seq1 + seq2`.
`($contains seq obj)` | Containment Test `obj in seq`.
`($div a b)` | Division `a / b`.
`($floordiv a b)` | Division `a // b`.
`($and_ a b)` | Bitwise And `a & b`.
`($xor a b)` | Bitwise Exclusive Or `a ^ b`.
`($invert a)` | Bitwise Inversion `~ a`.
`($or_ a b)` | Bitwise Or `a | b`.
`($pow a b)` | Exponentiation `a ** b`.
`($is_ a b)` | Identity `a is b`.
`($is_not a b)` | Identity `a is not b`.
`($getitem obj k)` | Indexing `obj[k]`.
`($lshift a b)` | Left Shift `a << b`.
`($mod a b)` | Modulo `a % b`.
`($mul a b)` | Multiplication `a * b`.
`($neg a)` | Negation (Arithmetic) `-a`.
`($not_ a)` | Negation (Logical) `not a`.
`($pos a)` | Positive `+a`.
`($rshift a b)` | Right Shift `a >> b`.
`($repeat seq i)` | Sequence Repetition `seq * i`.
`($mod s obj)` | String Formatting `s % obj`.
`($sub a b)` | Subtraction `a - b`.
`($truth obj)` | Truth Test `obj`.
`($lt a b)` | Ordering `a < b`.
`($le a b)` | Ordering `a <= b`.
`($eq a b)` | Equality `a == b`.
`($ne a b)` | Difference `a != b`.
`($ge a b)` | Ordering `a >= b`.
`($gt a b)` | Ordering `a > b`.
 | **Functions and constants imported from Python `math` module**
`($acos x)` | Return the arc cosine (measured in radians) of x.
`($acosh x)` | Return the hyperbolic arc cosine (measured in radians) of x.
`($asin x)` | Return the arc sine (measured in radians) of x.
`($asinh x)` | Return the hyperbolic arc sine (measured in radians) of x.
`($atan x)` | Return the arc tangent (measured in radians) of x.
`($atan2 y x)` | Return the arc tangent (measured in radians) of `y/x`. Unlike `atan(y/x)`, the signs of both x and y are considered.
`($atanh x)` | Return the hyperbolic arc tangent (measured in radians) of x.
`($ceil x)` | Return the ceiling of x as a float. This is the smallest integral value greater than or equal to x.
`($copysign x y)` | Return x with the sign of y.
`($cos x)` | Return the cosine of x (measured in radians).
`($cosh x)` | Return the hyperbolic cosine of x.
`($degrees x)` | Convert angle x from radians to degrees.
`($erf x)` | Error function at x.
`($erfc x)` | Complementary error function at x.
`($exp x)` | Return e raised to the power of x.
`($expm1 x)` | Return `exp(x)-1`. This function avoids the loss of precision involved in the direct evaluation of `exp(x)-1` for small x.
`($fabs x)` | Return the absolute value of the float x.
`($factorial x)` | Return x factorial.
`($floor x)` | Return the floor of x as a float. This is the largest integral value less than or equal to x.
`($fmod x y)` | Return fmod(x, y), according to platform C library. `x % y` may differ.
`($fsum iterable)` | Return an accurate floating point sum of values in the iterable. Assumes IEEE-754 floating point arithmetic.
`($gamma x)` | Gamma function at x.
`($hypot x y)` | Return the Euclidean distance, `sqrt(x*x + y*y)`.
`($isinf x)` | Check if float x is infinite (positive or negative).
`($isnan x)` | Check if float x is not a number (NaN).
`($ldexp x i)` | Return `x * (2**i)`.
`($lgamma x)` | Natural logarithm of absolute value of Gamma function at x.
`($log x [base])` | Return the logarithm of x to the given base. If the base not specified, returns the natural logarithm (base e) of x.
`($log10 x)` | Return the base 10 logarithm of x.
`($log1p x)` | Return the natural logarithm of `1+x` (base e). The result is computed in a way which is accurate for x near zero.
`($modf x)` | Return the fractional and integer parts of x. Both results carry the sign of x and are floats.
`($pow x y)` | Return `x**y` (x to the power of y).
`($radians x)` | Convert angle x from degrees to radians.
`($sin x)` | Return the sine of x (measured in radians).
`($sinh x)` | Return the hyperbolic sine of x.
`($sqrt x)` | Return the square root of x.
`($tan x)` | Return the tangent of x (measured in radians).
`($tanh x)` | Return the hyperbolic tangent of x.
`($trunc x)` | Truncates x to the nearest integral toward 0.
`($pi)` | The mathematical constant π = 3.141592..., to available precision.
`($e)` | The mathematical constant e = 2.718281..., to available precision.
 | **Functions and constants imported from Python `string` module**
`($digits)` | The string `'0123456789'`.
`($hexdigits)` | The string `'0123456789abcdefABCDEF'`.
`($letters)` | The concatenation of the strings `lowercase` and `uppercase` described below.
`($lowercase)` | A string containing all the characters that are considered lowercase letters. On most systems this is the string `'abcdefghijklmnopqrstuvwxyz'`.
`($octdigits)` | The string `'01234567'`.
`($uppercase)` | A string containing all the characters that are considered uppercase letters. On most systems this is the string `'ABCDEFGHIJKLMNOPQRSTUVWXYZ'`.
`($whitespace)` | A string containing all characters that are considered whitespace. On most systems this includes the characters space, tab, linefeed, return, formfeed, and vertical tab.
`($atof s)` | Convert a string to a floating point number.
`($atoi s [base])` | Convert string s to an integer in the given base. The base defaults to 10. If it is 0, a default base is chosen depending on the leading characters of the string (after stripping the sign): `0x` or `0X` means 16, `0` means 8, anything else means 10. If base is 16, a leading `0x` or `0X` is always accepted.
`($atol s [base])` | Convert string s to a long integer in the given base. The base argument has the same meaning as for `atoi`. A trailing `l` or `L` is not allowed, except if the base is 0.
`($capitalize word)` | Capitalize the first character of the argument.
`($capwords s)` | Split the argument into words using `split`, capitalize each word using `capitalize`, and join the capitalized words using `join`. Note that this replaces runs of whitespace characters by a single space, and removes leading and trailing whitespace.
`($expandtabs s tabsize)` | Expand tabs in a string, i.e. replace them by one or more spaces, depending on the current column and the given tab size. The column number is reset to zero after each newline occurring in the string. This doesn't understand other non-printing characters or escape sequences.
`($find s sub [start [end]])` | Return the lowest index in s where the substring sub is found such that sub is wholly contained in `s[start:end]`. Return -1 on failure. Defaults for start and end and interpretation of negative values is the same as for slices.
`($rfind s sub [start [end]])` | Like `find` but find the highest index.
`($index s sub [start [end]])` | Like `find` but raise ValueError when the substring is not found.
`($rindex s sub [start [end]])` | Like `rfind` but raise ValueError when the substring is not found.
`($count s sub [start [end]])` | Return the number of (non-overlapping) occurrences of substring sub in string `s[start:end]`. Defaults for start and end and interpretation of negative values is the same as for slices.
`($lower s)` | Convert letters to lower case.
`($maketrans from to)` | Return a translation table suitable for passing to `translate`, that will map each character in _from_ into the character at the same position in _to_; _from_ and _to_ must have the same length.
`($split s [sep [maxsplit]])` | Return a list of the words of the string s. If the optional second argument sep is absent or None, the words are separated by arbitrary strings of whitespace characters (space, tab, newline, return, formfeed). If the second argument sep is present and not None, it specifies a string to be used as the word separator. The returned list will then have one more items than the number of non-overlapping occurrences of the separator in the string. The optional third argument maxsplit defaults to 0. If it is nonzero, at most maxsplit number of splits occur, and the remainder of the string is returned as the final element of the list.
`($join words [sep])` | Concatenate a list or tuple of words with intervening occurrences of sep. The default value for sep is a single space character.
`($lstrip s)` | Remove leading whitespace from the string s.
`($rstrip s)` | Remove trailing whitespace from the string s.
`($strip s)` | Remove leading and trailing whitespace from the string s.
`($swapcase s)` | Convert lower case letters to upper case and vice versa.
`($translate s table [deletechars])` | Delete all characters from s that are in deletechars (if present), and then translate the characters using table, which must be a 256-character string giving the translation for each character value, indexed by its ordinal.
`($upper s)` | Convert letters to upper case.
`($ljust s width)`<br>`($rjust s width)`<br>`($center s width)` | These functions respectively left-justify, right-justify and center a string in a field of given width. They return a string that is at least width characters wide, created by padding the string s with spaces until the given width on the right, left or both sides. The string is never truncated.
`($zfill s width)` | Pad a numeric string on the left with zero digits until the given width is reached. Strings starting with a sign are handled correctly.
`($replace str old new [maxsplit])` | Return a copy of string str with all occurrences of substring old replaced by new. If the optional argument maxsplit is given, the first maxsplit occurrences are replaced.
