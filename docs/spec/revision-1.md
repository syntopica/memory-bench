# memory-bench specification, Revision 1

Status: current. Dated 2026-10-11.

This is the normative specification of memory-bench. A result cites it by
revision: every `manifest.json` carries `"spec_revision": 1`, written from
`membench/spec_revision.py`, and the rules below are what a run carrying that
number was produced and scored under. A revision is never edited after it is
cited; a changed rule is a new file, `revision-2.md`, and a new number.

The words MUST, MUST NOT and MAY are normative. Everything else is
explanation. The reasoning behind the rules lives in the design record,
`docs/superpowers/specs/2026-09-17-memory-bench-design.md`, which is historical
and not normative; where the two disagree, this document governs.

Every rule names the code that implements it and the test that verifies it.
Each was checked against the harness at the commit that introduced this file.
A rule that the harness cannot check, because it binds the system under test
rather than the harness, says so.

## 1. Scope

**S1.** Revision 1 specifies Track R, source discovery: which conversations a
system finds for a question. It does not specify Track A (answer sufficiency),
operability scoring, or scoring thresholds; section 8 lists what is deferred.
A Revision 1 result is a Track R result and MUST NOT be presented as a measure
of memory quality. The manifest says so in `"track": "R: source discovery"`.
Code: `membench/build_manifest.py`. Test:
`test_the_manifest_records_the_track_it_scored`.

## 2. Inputs

### Corpus

**C1.** A corpus is a JSONL file of conversations, one object per line, each
with `conversation_id`, `started_at` and `messages`; each message has `role`,
`content` and `timestamp`. Blank lines are skipped. Code:
`membench/load_corpus.py`. Tests: `test_loads_a_conversation_with_its_messages`,
`test_blank_lines_are_skipped`.

**C2.** A `conversation_id` MUST be unique within a corpus. A duplicate is
refused before the run starts. Test: `test_duplicate_conversation_ids_are_rejected`.

### Question set

**Q1.** A question set is a JSONL file of questions, one object per line, each
with `question_id`, `question`, an answer label and `strata`, and optionally
`as_of`. Code: `membench/load_questions.py`. Tests:
`test_loads_a_labelled_question`, `test_as_of_is_read_when_present_and_none_otherwise`.

**Q2.** The answer label is either `answer_conversation_ids`, a list of
strings, or `answer_conversation_id`, a string or `null`. A question record
MUST carry exactly one of the two keys. Code: `membench/read_answer_labels.py`.
Tests: `test_both_keys_at_once_is_an_error`, `test_an_unlabelled_question_is_rejected`,
`test_a_missing_answer_key_is_still_an_unlabelled_question`,
`test_a_plural_key_is_read_as_the_label_set`.

**Q3.** A question is **unanswerable** exactly when its label is empty: `[]`
or `null`. A missing key, an empty or whitespace-only id, a non-string id, or a
plural key that is not a list is a corpus defect and is refused, never read as
unanswerable. Tests: `test_an_explicit_null_answer_is_an_unanswerable_question`,
`test_an_empty_plural_key_is_an_unanswerable_question`,
`test_an_empty_string_answer_is_an_unlabelled_question`,
`test_a_whitespace_only_singular_label_is_an_unlabelled_question`,
`test_a_whitespace_only_label_inside_the_plural_key_is_refused`,
`test_an_empty_string_inside_the_plural_key_is_an_unlabelled_question`,
`test_a_non_string_singular_label_is_refused_as_the_wrong_type`,
`test_a_non_string_inside_the_plural_key_is_refused_as_the_wrong_type`,
`test_a_plural_key_that_is_not_a_list_is_refused`.

**Q4.** A question's `strata` MUST carry exactly one tag from each of four
dimensions - language `es`/`en`, source shape `conversation`/`note`,
vocabulary overlap `overlap`/`no-overlap`, age `recent`/`old` - and MAY carry
`temporal-contradiction` once. Any other tag is refused. Strata are for
descriptive breakdowns only and never enter a score. Code:
`membench/strata_vocabulary.py`, `membench/validate_strata.py`. Tests:
`test_a_complete_tag_set_is_accepted`, `test_the_temporal_contradiction_tag_is_optional`,
`test_an_unknown_tag_is_rejected`, `test_two_tags_from_one_dimension_are_rejected`,
`test_a_missing_dimension_is_rejected`, `test_a_stratum_tag_outside_the_vocabulary_is_rejected`.

**Q5.** `as_of` is recorded and MUST NOT be scored on Track R. Code:
`membench/question.py` (carried on `Question`, read by no metric).
Verified by inspection: outside `load_questions.py`, `question.py` and a
docstring in `strata_vocabulary.py`, no module under `membench/` names
`as_of`, and none of the scoring modules in section 5 does.

## 3. The adapter contract

The contract is `membench/memory_adapter.py`, at `ADAPTER_CONTRACT_VERSION`
`2.1`. Its docstrings are normative and this section restates them.

**A1.** An adapter implements `setup()`, `ingest(corpus) -> IngestReport`,
`query(question, k, token_budget) -> list[Evidence]` and `teardown()`. Code:
`membench/memory_adapter.py`. Verified by `mypy membench` against the
shipped adapter, `membench/adapters/baseline_fts5_adapter.py`.

**A2.** An adapter is constructed by calling it with the workspace `Path`
first and every option from `--adapter-options` as a keyword. The binding is
checked with `inspect.signature(...).bind` before anything is written, and an
option the constructor does not accept refuses the run with exit code 2.
Options MUST be a JSON object. Code: `membench/cli.py`,
`membench/load_adapter_options.py`. Tests:
`test_an_unknown_option_exits_2_and_writes_nothing`,
`test_a_non_object_adapter_options_file_exits_2_and_writes_nothing`,
`test_an_unrecognised_option_raises_rather_than_being_ignored`.

**A3.** The workspace is `<out>/workspace/`. The harness creates it, empty,
before constructing the adapter, and never writes inside it. Under `--force`
the harness removes the workspace and creates it again after every refusal
has passed; a symbolic link in its place is unlinked, not followed. Code:
`membench/cli.py`, `membench/clear_workspace.py`. Tests:
`test_the_workspace_exists_before_the_adapter_is_constructed`,
`test_a_forced_rerun_ingests_into_an_empty_workspace`,
`test_a_refused_forced_run_leaves_the_workspace_alone`,
`test_a_symlinked_workspace_is_unlinked_not_followed`.

**A4.** An adapter MUST create nothing outside its workspace. This binds the
system under test; the harness does not check it.

**A5.** `teardown()` is called exactly once however the run ends, including
after a failure during setup, ingest or querying. A teardown failure after the
run already failed is reported on stderr and the original failure is raised; on
an otherwise successful run a teardown failure fails the run. Code:
`membench/adapter_lifecycle.py`. Tests:
`test_a_run_that_finishes_tears_the_adapter_down_once`,
`test_an_ingest_that_raises_still_tears_the_adapter_down`,
`test_a_failing_teardown_does_not_mask_the_failure_that_ended_the_run`,
`test_a_failing_teardown_says_so_on_stderr`,
`test_a_teardown_failure_on_the_success_path_is_reported`,
`test_a_run_that_fails_during_ingest_still_tears_the_adapter_down`.

**A6.** Track R calls `query` with `token_budget=None`, meaning unbounded.
Code: `membench/run_track_r.py`. Test: `test_track_r_asks_with_an_unbounded_budget`.
When a budget is given, an adapter MUST return the longest prefix of its
ranking whose texts fit under `count_tokens`, dropping from the end only. This
binds the system under test; the harness checks it only for the shipped
baseline (`test_a_budget_drops_evidence_from_the_end`,
`test_a_budget_smaller_than_the_first_hit_returns_nothing`).

**A7.** A token is a whitespace-separated run of characters. Code:
`membench/count_tokens.py`. Tests: `test_it_counts_whitespace_separated_words`,
`test_it_counts_nothing_in_an_empty_string`,
`test_punctuation_attached_to_a_word_does_not_add_a_token`. This definition is
only meaningful for whitespace-delimited scripts, and a corpus in an
unsegmented script MUST NOT be measured under it.

## 4. Ranking

**K1.** `k` MUST be at least 1; a smaller value is refused before anything is
written. Code: `membench/validate_run_paths.py`. Tests:
`test_a_zero_k_is_refused_and_writes_nothing`,
`test_a_negative_k_is_refused_and_writes_nothing`.

**K2.** A run's ranking is a sequence of slots built from the evidence in the
order returned. Each distinct source id spends one slot, in the order it
appears; an id already ranked keeps its earlier slot and spends none; a piece
of evidence with no source ids spends one slot, recorded as `null`, and
unsourced slots are never deduplicated. Code: `membench/ranked_sources.py`.
Tests: `test_returns_sources_in_rank_order`,
`test_deduplicates_keeping_the_best_rank`,
`test_one_evidence_with_several_sources_yields_each_in_order`,
`test_an_unsourced_hit_occupies_its_slot`,
`test_two_unsourced_hits_are_not_deduplicated_into_one_slot`,
`test_a_repeated_source_keeps_its_best_slot_only`.

**K3.** A source id is matched verbatim against `conversation_id`, after
removing exactly one leading `synthesis/`. Nothing else is normalised. Code:
`membench/normalize_source_id.py`. Tests:
`test_strips_the_atrium_synthesis_namespace`, `test_leaves_a_plain_id_alone`,
`test_strips_only_the_leading_namespace`, `test_unknown_namespace_is_left_intact`,
`test_normalizes_the_synthesis_namespace_before_deduplicating`.

**K4.** Slots past the k-th are discarded before scoring, and the row's
`truncated` is `true` exactly when there were more than `k` slots. Code:
`membench/run_track_r.py`. Tests: `test_ranked_sources_are_truncated_to_k`,
`test_a_cut_ranking_says_it_was_cut`, `test_a_ranking_that_fits_says_it_was_not_cut`.

## 5. Scoring

**M1. Applicability is decided once per run.** A run is `not_applicable` when
the system returned evidence and no slot on any question, before the depth
cut, named a source; otherwise every row is `scored`. A run that returned
nothing at all is `scored`. There is no mixed run. Code:
`membench/run_applicability.py`. Tests:
`test_a_run_that_never_cited_a_conversation_is_not_applicable`,
`test_one_cited_conversation_anywhere_scores_the_whole_run`,
`test_the_verdict_does_not_depend_on_which_question_carried_the_source`,
`test_a_run_that_returned_nothing_at_all_is_scored_as_the_misses_it_made`,
`test_provenance_past_the_requested_depth_still_scores_the_system`,
`test_stripping_provenance_on_the_questions_it_loses_buys_a_system_nothing`.

**M2. `recall_any_at_d`**, for `d` in 1, 5 and 10, is `1.0` when at least one
labelled conversation is within the first `d` slots and `0.0` otherwise. An
unsourced slot never matches. Code: `membench/recall_any_at_k.py`. Tests:
`test_hit_inside_k_scores_one`, `test_hit_outside_k_scores_zero`,
`test_one_of_several_labels_inside_k_is_enough`, `test_an_unsourced_slot_never_matches`.

**M3. `recall_all_at_d`** is `1.0` when every distinct labelled conversation
is within the first `d` slots, `0.0` when one is not, and `null` when `d` is
smaller than the number of distinct labels. Code: `membench/recall_all_at_k.py`.
Tests: `test_every_label_inside_k_scores_one`, `test_one_label_outside_k_scores_zero`,
`test_a_depth_too_shallow_to_hold_every_label_is_undefined`,
`test_a_depth_exactly_wide_enough_is_observed`, `test_a_repeated_label_needs_no_extra_slot`.

**M4.** Every metric at a depth `d` greater than the run's `k` is `null`,
never `0.0`. Code: `membench/recall_at_depth.py`. Tests:
`test_a_depth_deeper_than_k_is_unknown_not_zero`,
`test_a_depth_beyond_k_is_null_rather_than_a_miss`,
`test_a_shallow_k_publishes_no_number_under_a_deeper_name`.

**M5. `reciprocal_rank`** is `1 / rank` of the best-ranked labelled
conversation within the `k` slots, and `0.0` when none is there. It is
reciprocal rank at `depth`: rows from runs at different `depth` MUST be
grouped by `depth` before this field is averaged. A worst-rank measurement, if
ever added, is a new field and never a redefinition of this one. Code:
`membench/reciprocal_rank.py`. Tests: `test_the_best_ranked_label_is_the_one_measured`,
`test_label_order_does_not_change_the_score`, `test_reciprocal_rank_measures_the_best_ranked_label`.

**M6.** `recall_any_*` and `recall_all_*` are published side by side and MUST
NOT be averaged into one recall. Code: `membench/metric_means.py` (separate
means). Test: `test_any_and_all_measure_different_things_on_a_multi_label_question`.

**M7.** On an unanswerable question, or in a `not_applicable` run, every
metric is `null`. Code: `membench/question_metrics.py`. Tests:
`test_an_unanswerable_question_has_no_recall_to_report`,
`test_a_system_without_provenance_is_not_applicable_rather_than_wrong`,
`test_a_run_without_any_provenance_is_not_applicable_on_every_row`.

**M8. Means.** A metric's mean is taken over the rows that are answerable and
`scored` and whose value for that metric is not `null`. A `null` is never
averaged as a zero. A metric no row observed has no mean. Code:
`membench/scored_answerable_rows.py`, `membench/metric_means.py`. Tests:
`test_it_averages_the_scored_rows`,
`test_an_unscorable_row_is_excluded_rather_than_averaged_as_zero`,
`test_a_metric_no_row_observed_has_no_mean`, `test_an_unanswerable_row_never_enters_a_mean`.

**M9. Abstention.** On an unanswerable question `abstained` is `true` when the
system returned nothing at all, and `false` when it returned anything,
including evidence with no source; on an answerable question it is `null`. The
abstention rate is the share of unanswerable rows that abstained, `null` when
there are none, and it is computed whatever the run's applicability. Code:
`membench/abstention_verdict.py`, `membench/abstention_rate.py`. Tests:
`test_nothing_returned_is_abstaining`,
`test_an_unsourced_slot_still_counts_as_having_answered`,
`test_an_answerable_question_has_no_verdict`,
`test_a_run_with_no_unanswerable_question_observed_no_rate`,
`test_an_unscorable_run_still_reports_what_it_returned`.

**M10.** The abstention rate MUST NOT be averaged with, or reported inside,
the retrieval means. Code: `membench/cli.py` (printed on its own line).
Tests: `test_abstaining_everywhere_does_not_lift_a_single_recall`,
`test_a_run_over_unanswerable_questions_reports_them_outside_the_metrics`.

## 6. Run requirements

**R1.** A run refuses, with exit code 2 and before creating or touching the
output directory, a missing corpus or question file, an invalid `k`, an
unknown adapter, unreadable adapter options, or an option the adapter does not
accept. Code: `membench/cli.py`, `membench/validate_run_paths.py`. Tests:
`test_a_missing_corpus_is_refused_and_writes_nothing`,
`test_a_missing_questions_file_is_refused_and_writes_nothing`,
`test_an_unknown_adapter_is_refused`,
`test_missing_adapter_options_file_exits_2_and_writes_nothing`.

**R2.** Without `--force` a run refuses an output directory holding a
`manifest.json`, and a non-empty `workspace/` with no manifest beside it.
Code: `membench/validate_run_paths.py`. Tests:
`test_a_second_run_into_the_same_directory_is_refused`,
`test_a_populated_workspace_without_a_manifest_is_refused`,
`test_the_run_after_a_crash_is_refused_until_forced`.

**R3.** A completed run writes exactly two artifacts beside the workspace:
`manifest.json` and `raw.jsonl`, one row per question in question order.
Code: `membench/write_run.py`. Test: `test_writes_the_manifest_and_one_line_per_question`.

## 7. Artifacts and disclosure

### The raw row

**W1.** Every `raw.jsonl` row carries `schema_version` (`RAW_SCHEMA_VERSION`,
`4.0`) and the fields `question_id`, `strata`, `ranked_sources`,
`applicability`, `answerable`, `answer_label_count`, `depth`, `truncated`,
`recall_any_at_1`, `recall_any_at_5`, `recall_any_at_10`, `recall_all_at_1`,
`recall_all_at_5`, `recall_all_at_10`, `reciprocal_rank`, `abstained`,
`seconds` and `evidence_texts`, with the meanings `README.md` gives under
"The result schema". Code: `membench/write_run.py`,
`membench/question_result.py`. Tests:
`test_every_row_carries_the_schema_version_it_was_written_under`,
`test_the_row_carries_what_it_needs_to_read_an_empty_all_recall`.

**W2.** `answer_label_count` is the number of distinct labelled
conversations, `0` when unanswerable. Code: `membench/run_track_r.py`. Test:
`test_the_label_count_is_distinct_labels_and_matches_what_the_metric_applied`.

### The manifest

**W3.** Every `manifest.json` carries: `run_id`, `track`, `manifest_version`
(`1.2`), `raw_schema_version`, `adapter_contract_version`, `spec_revision`,
`sqlite_version`, `adapter`, `k`, `corpus` and `questions` (each with `path`,
`sha256` and `source`), `started_at`, `harness` (`commit`, `dirty`),
`environment` (`python`, `platform`), `dependency_lock` (`path`, `sha256`),
`adapter_options` exactly as passed, and `ingest` (`seconds`,
`persisted_bytes`, `input_tokens`, `output_tokens`). Code:
`membench/build_manifest.py`, `membench/write_run.py`. Tests:
`test_the_manifest_pins_the_inputs`,
`test_the_manifest_records_the_versions_of_both_published_artifacts`,
`test_the_manifest_records_the_sqlite_build_that_ran`,
`test_it_records_what_reproduction_needs`,
`test_the_written_manifest_carries_the_cli_s_options_unchanged`.

**W4.** `corpus.path` and `questions.path` name the file relative to the root
of the repository holding it, else relative to the working directory, else by
file name; an absolute path never appears. Code: `membench/portable_path.py`.
Tests: `test_a_file_in_a_repository_is_named_from_its_root_whatever_the_working_directory`,
`test_an_absolute_home_path_never_survives_into_the_label`.

**W5.** `source.repository` is that repository's `origin` remote with any
credentials removed, and `source.commit` is its `HEAD` only when `HEAD` holds
the file unmodified; either is `null` when it cannot be stated. A reader
reproduces the input by cloning `repository`, checking out `commit`, reading
`path`, and comparing `sha256`. Code: `membench/file_source.py`,
`membench/committed_revision.py`, `membench/redact_remote_url.py`. Tests:
`test_a_committed_file_names_its_repository_and_commit`,
`test_a_modified_file_has_no_commit`, `test_an_untracked_file_has_no_commit`,
`test_a_token_in_an_https_remote_is_removed`.

**W6.** `started_at` is the instant the run began, in UTC with an explicit
offset. Tests: `test_the_timestamp_is_utc_and_explicit`,
`test_the_timestamp_is_the_caller_s_instant_not_the_serialisation_instant`.

**W7.** A field that cannot be determined is recorded as unknown rather than
failing the run: `harness.commit` `"unknown"` with `dirty` `true`,
`dependency_lock.sha256` `"unknown"`. Code: `membench/harness_commit.py`,
`membench/dependency_lock.py`. Tests:
`test_it_admits_ignorance_outside_a_repository`, `test_it_admits_the_lock_is_absent`.

### Versions

**V1.** `manifest_version`, `raw_schema_version` and
`adapter_contract_version` each raise their major part when a field or method
changes meaning, is removed, or becomes newly nullable, and their minor part
for an addition an existing reader or adapter can ignore. `spec_revision` is
an integer that increases whenever a rule in this document changes. Code: the
docstrings of `MANIFEST_VERSION`, `RAW_SCHEMA_VERSION`,
`ADAPTER_CONTRACT_VERSION` and `SPEC_REVISION`. Verified by inspection.

### Disclosure

**D1.** Every printed mean carries its depth and the number of questions it
was taken over: `<metric>@k=<k>: <value> (over <n> questions)`, with `n/a`
for a metric with no mean. Code: `membench/cli.py`,
`membench/metric_observations.py`. Tests:
`test_two_means_over_different_populations_print_different_denominators`,
`test_a_metric_the_run_never_observed_is_reported_as_unavailable`.

**D2.** The run prints how many answerable questions were scored and how many
were excluded as not applicable. Test:
`test_the_run_reports_its_means_and_what_it_excluded`.

**D3.** The abstention line prints `n/a` when the set holds no unanswerable
question, and, when the run is not applicable anywhere, says on the line itself
that it is not a Track R score. Test:
`test_a_perfect_abstention_beside_no_scores_says_it_is_not_a_track_r_score`.

**D4.** A result over a corpus small enough to saturate a column MUST report
that column as saturated, not as a tie or a perfect score. This binds whoever
publishes a result; the harness does not detect saturation.

**D5.** A published comparison MUST state that beating the untuned lexical
baseline establishes only that a system is better than untuned lexical
retrieval. This binds whoever publishes a result.

## 8. Not in Revision 1

These are not rules yet, and a Revision 1 result MUST NOT claim them:

- Track A, answer sufficiency, and the fixed reader it needs.
- Operability scoring and the capability matrix.
- Scoring thresholds. The design requires them to be derived from a baseline
  pilot and committed before any scored run; none exist.
- An adapter identity beyond its registered name. It will be defined from a
  package version or commit plus a configuration digest once a second adapter
  exists.
- An image or container digest, and the prompts issued and models resolved,
  which arrive with the model gateway.
- A mechanism for registering a foreign adapter. Today the harness constructs
  only the adapters in `membench/build_adapter.py`.
