# Eval assertion fixtures

Synthetic transcripts, used by the `eval assertions` section of `tests/lint.sh` to test the
regexes in `tests/eval.sh` without an API call. `tests/eval.sh --dump` prints the real
assertions, so these test the regexes that actually run rather than copies that would drift.

| Suffix | Must |
| --- | --- |
| `.pass.txt` | match the case's expect regex, and not match its DENY |
| `.fail-expect.txt` | NOT match the expect regex |
| `.fail-deny.txt` | match the DENY |

Nothing here is a real transcript and nothing here contains a real credential. Several are
regressions: a case that once reported a correct run as failed keeps its transcript here so
the assertion can never drift back.
