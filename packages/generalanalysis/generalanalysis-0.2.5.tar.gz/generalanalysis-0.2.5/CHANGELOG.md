# Changelog


## [0.2.5] - 2025-09-14

### Added
- optional reasoning field to guard invoke result

## [0.2.4] - 2025-09-01

### Changed
- Removed redundant database columns from GuardLog model (latency_ms, blocked)
- Consolidated all guard log data into the JSON result column to eliminate redundancy
- Fixed type definitions to properly handle GuardInvokeResponse in log results

## [0.2.3] - 2025-09-01

### Breaking Changes
- Made the following fields mandatory (no longer Optional):
  - `Guard.description` and `Guard.endpoint`
  - `GuardPolicy.definition`
  - `PolicyEvaluation.definition` and `PolicyEvaluation.violation_prob`
  - `GuardInvokeResult.raw`

### Added
- `violation_prob` field to `PolicyEvaluation` for probability/confidence scores (0.0-1.0)
- `raw` field to `GuardInvokeResult` for accessing raw response data from guards
- Support for probability scores from all guard types (Presidio, OpenAI Moderation, SageMaker)

### Changed
- Renamed `harmfulness_prob` to `violation_prob` for more generic applicability
- Updated all guard processors to always provide violation probabilities

## [0.2.2] - 2025-08-28

### Changed
- Updated README

## [0.2.1] - 2025-08-28

### Changed
- Updated README

## [0.2.0] - 2025-08-27

### Added
- Initial Python SDK release with sync/async clients
- Guard operations: list, get, invoke, generate policies, view logs
- Full type hints with custom error types
- Environment variable and direct API key support
- Usage examples for both sync and async patterns