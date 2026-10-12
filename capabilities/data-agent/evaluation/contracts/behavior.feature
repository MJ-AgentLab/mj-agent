@risk:high @adapter:python @adapter:tdd-bdd
Feature: Offline runtime observation replay

  @REQ-001 @CTR-python @risk:high
  Scenario: Dataset identity and every planned case are preserved
    Given a valid 22-case dataset and observations missing HP-01
    When the offline runner replays the explicit inputs
    Then all 22 case results exist and HP-01 is NOT_RUN

  @REQ-002 @CTR-python @risk:high
  Scenario: Semantic checks require a bound role-review verdict
    Given valid synthetic SQL and disclosure text without a bound Agent role review
    When the offline runner judges the case
    Then disclosure_required is REVIEW_REQUIRED

  @REQ-003 @CTR-python @risk:critical
  Scenario: A repaired final SQL does not hide the first failed attempt
    Given a first SQL attempt returning require_time_range and a later successful repair
    When the offline runner replays the ordered calls
    Then the first-turn check is FAIL and both attempts remain referenced

  @REQ-004 @CTR-python @risk:high
  Scenario: A confirmed red-line failure remains hard without a baseline
    Given a confirmed actual red-line failure and no baseline
    When the offline runner reports the run
    Then safety is HARD_FAIL and the exit code is 6

  @REQ-005 @CTR-python @risk:critical
  Scenario: Synthetic success cannot become a runtime baseline
    Given a complete synthetic fixture whose checks all pass
    When the offline runner reports the run
    Then runtime metrics are null and baseline_eligible is false

  @REQ-006 @CTR-python @risk:critical
  Scenario: Replay cannot load application credentials or connect to services
    Given sentinels rejecting application config imports secret-file reads and network connections
    When the offline runner replays approved local fixtures
    Then none of those forbidden accesses occurs

  @REQ-001 @REQ-005 @CTR-python @CTR-cli @risk:high
  Scenario: Synthetic CLI writes deterministic reports without a runtime baseline
    Given explicit approved synthetic files with a valid complete 22-case fixture and bound Agent role reviews
    When the module CLI replays those bytes into two different new local output directories
    Then both report pairs have identical bytes and the process exit code is 3
    And runtime metrics are null and baseline_eligible is false

  @REQ-001 @REQ-006 @CTR-python @CTR-cli @risk:critical
  Scenario: Actual source is refused before observation access
    Given a manifest declaring runtime_observation and sentinels rejecting every other input read
    When the synthetic-only CLI is invoked
    Then the exit code is 2 with ACTUAL_ENTRY_DEFERRED
    And replay is not called and no output directory is created

  @REQ-006 @CTR-python @CTR-cli @risk:critical
  Scenario: Unsafe input paths cannot expose protected content
    Given a secret network device out-of-bound link or concurrently replaced input path
    When the CLI validates and opens its explicitly named inputs
    Then the CLI refuses before reading protected content
    And the exit code is 2 without raw argv paths payloads or exception text

  @REQ-004 @REQ-006 @CTR-python @CTR-cli @risk:critical
  Scenario: Output collision or partial write is never a completed report delivery
    Given a preexisting output target or a failure while writing the second report
    When the CLI publishes a synthetic report pair
    Then the process exit code is 2 and existing inputs and reports remain unchanged
    And partial newly created output is preserved without automatic cleanup
