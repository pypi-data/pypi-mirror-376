# sd-metrics-lib

Python library for calculating various metrics related to the software development process. Provides developer and team velocity
calculations based on data from Jira and Azure DevOps. Metrics calculation classes use interfaces, so the library can be easily extended
with other data providers (e.g., Trello, Asana) from application code.

## Architecture and API reference

### Overview

This library separates metric calculation from data sourcing. Calculators operate on abstract provider interfaces so you can plug in Jira, Azure DevOps, or your own sources. Below is a structured overview by package with links to the key classes you will use.

### Calculators

- Module: `sd_metrics_lib.calculators.metrics`
    - `MetricCalculator` (abstract): Base interface for all metric calculators (`calculate()`).
- Module: `sd_metrics_lib.calculators.velocity`
    - `AbstractMetricCalculator` (abstract): Adds lazy extraction and shared `calculate()` workflow.
    - `UserVelocityCalculator`: Per-user velocity (story points per time unit). Requires `TaskProvider`, `StoryPointExtractor`, `WorklogExtractor`.
    - `GeneralizedTeamVelocityCalculator`: Team velocity (total story points per time unit). Requires `TaskProvider`, `StoryPointExtractor`, `TaskTotalSpentTimeExtractor`.

### Sources (data providers)

- Module: `sd_metrics_lib.sources.tasks`
    - `TaskProvider` (abstract): Fetches a list of tasks/work items.
    - `ProxyTaskProvider`: Wraps a pre-fetched list of tasks (useful for tests/custom sources).
    - `CachingTaskProvider`: Caches results of any `TaskProvider`. Cache key is built from `provider.query` and `provider.additional_fields`; works with any dict-like cache (e.g., `cachetools.TTLCache`).
- Module: `sd_metrics_lib.sources.story_points`
    - `StoryPointExtractor` (abstract)
    - `ConstantStoryPointExtractor`: Returns a constant story point value (defaults to 1).
    - `FunctionStoryPointExtractor`: Wraps a callable to compute story points from a task.
    - `AttributePathStoryPointExtractor`: Reads story points via a dotted attribute path and converts to float with default fallback.
    - Vendor implementations below: `AzureStoryPointExtractor`, `JiraCustomFieldStoryPointExtractor`, `JiraTShirtStoryPointExtractor`.
- Module: `sd_metrics_lib.sources.worklog`
    - `WorklogExtractor` (abstract): Returns mapping `user -> Duration` for a task.
    - `TaskTotalSpentTimeExtractor` (abstract): Returns total `Duration` spent on a task.
    - `ChainedWorklogExtractor`: Tries extractors in order and returns the first non-empty result.
    - `FunctionWorklogExtractor`: Wraps a callable to produce per-user time dict; values must be `Duration` instances; invalid values are ignored.
    - `FunctionTotalSpentTimeExtractor`: Wraps a callable returning a `Duration`; invalid values fall back to `Duration.zero()`.
    - `AttributePathWorklogExtractor`: Reads a mapping at a dotted attribute path; values must be `Duration` instances; invalid values are ignored.
    - `AttributePathTotalSpentTimeExtractor`: Reads a value at a dotted attribute path; returns it if it's a `Duration`, otherwise returns a default `Duration` (configurable).
- Module: `sd_metrics_lib.sources.abstract_worklog`
    - `AbstractStatusChangeWorklogExtractor` (abstract): Derives work time from assignment/status change history; attributes time to assignee and respects optional user filters and `WorkTimeExtractor`.

#### Jira

- Module: `sd_metrics_lib.sources.jira.tasks`
    - `JiraTaskProvider`: Fetch tasks by `JQL` via `atlassian-python-api`; supports paging and optional `ThreadPoolExecutor`.
- Module: `sd_metrics_lib.sources.jira.query`
    - `JiraSearchQueryBuilder`: Builder for `JQL` (project, status, date range, type, team, custom raw filters, order by)
- Module: `sd_metrics_lib.sources.jira.story_points`
    - `JiraCustomFieldStoryPointExtractor`: Reads a numeric custom field; supports default value.
    - `JiraTShirtStoryPointExtractor`: Maps T-shirt sizes (e.g., `S`/`M`/`L`) to numbers from a custom field.
- Module: `sd_metrics_lib.sources.jira.worklog`
    - `JiraWorklogExtractor`: Aggregates time from native Jira worklogs (optionally includes subtasks); optional user filter.
    - `JiraStatusChangeWorklogExtractor`: Derives time from changelog (status/assignee changes); supports username vs `accountId` and status names vs codes; uses a `WorkTimeExtractor`.
    - `JiraResolutionTimeTaskTotalSpentTimeExtractor`: Total time from `created` to `resolutiondate`.

#### Azure DevOps

- Module: `sd_metrics_lib.sources.azure.tasks`
    - `AzureTaskProvider`: Executes `WIQL`; fetches work items in pages (sync or `ThreadPoolExecutor`); can expand updates for status-change-based calculations.
- Module: `sd_metrics_lib.sources.azure.query`
    - `AzureSearchQueryBuilder`: Builder for WIQL (project, status, date range, type, area path/team, custom raw filters, order by)
- Module: `sd_metrics_lib.sources.azure.story_points`
    - `AzureStoryPointExtractor`: Reads story points from a field (default `Microsoft.VSTS.Scheduling.StoryPoints`); robust parsing with default.
- Module: `sd_metrics_lib.sources.azure.worklog`
    - `AzureStatusChangeWorklogExtractor`: Derives per-user time from work item updates (assignment/state changes); supports status filters; uses `WorkTimeExtractor`.
    - `AzureTaskTotalSpentTimeExtractor`: Total time from `System.CreatedDate` to `Microsoft.VSTS.Common.ClosedDate`.

### Utilities

- Module: `sd_metrics_lib.utils.enums`
    - `HealthStatus` (Enum): values `GREEN`, `YELLOW`, `ORANGE`, `RED`, `GRAY`
    - `SeniorityLevel` (Enum): values `JUNIOR`, `MIDDLE`, `SENIOR`
- Module: `sd_metrics_lib.utils.storypoints`
    - `TShirtMapping`: Helper to convert between T-shirt sizes (`XS`/`S`/`M`/`L`/`XL`) and story points using default mapping `xs=1`, `s=5`, `m=8`, `l=13`, `xl=21`.
- Module: `sd_metrics_lib.utils.time`
    - Constants: `SECONDS_IN_HOUR`, `WORKING_HOURS_PER_DAY`, `WORKING_DAYS_PER_WEEK`, `WORKING_WEEKS_IN_MONTH`, `WEEKDAY_FRIDAY`
    - Classes: `TimeUnit`, `TimePolicy` (with presets `TimePolicy.ALL_HOURS`, `TimePolicy.BUSINESS_HOURS`), `Duration`
        - Key methods: zero(), of(), datetime_difference(), to_seconds(), convert(), is_zero(), add()/sub() and operators +/-, sum(iterable), scalar * and /.
    - Prefer `TimePolicy.convert()` or `Duration.convert()` over manual seconds math.
- Module: `sd_metrics_lib.utils.worktime`
    - `WorkTimeExtractor` (abstract)
    - `SimpleWorkTimeExtractor`: Computes working Duration between two datetimes with business-day heuristics.
    - `BoundarySimpleWorkTimeExtractor`: Like `SimpleWorkTimeExtractor` but clamps to [start, end] boundaries.
- Module: `sd_metrics_lib.utils.cache`
    - `CacheProtocol` (Protocol), `DictProtocol` (Protocol)
    - `DictToCacheProtocolAdapter`: Adapts a dict-like to `CacheProtocol`.
    - `CacheKeyBuilder`: Helpers to build cache keys for data/meta entries.
    - `SupersetResolver`: Finds a superset fieldset for cached data reuse.
- Module: `sd_metrics_lib.utils.generators`
    - `TimeRangeGenerator`: Iterator producing date ranges for the requested `TimeUnit` (supports HOUR, DAY, WEEK, MONTH)

### Public API imports

Use the physical modules directly (no export shims):

- Calculators:
    - `from sd_metrics_lib.calculators.velocity import UserVelocityCalculator, GeneralizedTeamVelocityCalculator`
- Common utilities:
    - `from sd_metrics_lib.utils.enums import HealthStatus, SeniorityLevel`
    - `from sd_metrics_lib.utils.storypoints import TShirtMapping`
    - `from sd_metrics_lib.utils.time import SECONDS_IN_HOUR, WORKING_HOURS_PER_DAY, WORKING_DAYS_PER_WEEK, WORKING_WEEKS_IN_MONTH, WEEKDAY_FRIDAY, TimeUnit, TimePolicy, Duration`
    - `from sd_metrics_lib.utils.worktime import WorkTimeExtractor, SimpleWorkTimeExtractor, BoundarySimpleWorkTimeExtractor`
    - `from sd_metrics_lib.utils.generators import TimeRangeGenerator`
    - `from sd_metrics_lib.utils.cache import CacheKeyBuilder, CacheProtocol, DictToCacheProtocolAdapter, SupersetResolver, DictProtocol`
- Sources (providers):
    - `from sd_metrics_lib.sources.tasks import TaskProvider, ProxyTaskProvider, CachingTaskProvider`
    - `from sd_metrics_lib.sources.story_points import StoryPointExtractor, ConstantStoryPointExtractor, FunctionStoryPointExtractor, AttributePathStoryPointExtractor`
    - `from sd_metrics_lib.sources.worklog import WorklogExtractor, ChainedWorklogExtractor, TaskTotalSpentTimeExtractor, FunctionWorklogExtractor, FunctionTotalSpentTimeExtractor, AttributePathWorklogExtractor, AttributePathTotalSpentTimeExtractor`
- Jira:
    - `from sd_metrics_lib.sources.jira.query import JiraSearchQueryBuilder`
    - `from sd_metrics_lib.sources.jira.tasks import JiraTaskProvider`
    - `from sd_metrics_lib.sources.jira.story_points import JiraCustomFieldStoryPointExtractor, JiraTShirtStoryPointExtractor`
    - `from sd_metrics_lib.sources.jira.worklog import JiraWorklogExtractor, JiraStatusChangeWorklogExtractor, JiraResolutionTimeTaskTotalSpentTimeExtractor`
- Azure:
    - `from sd_metrics_lib.sources.azure.query import AzureSearchQueryBuilder`
    - `from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider`
    - `from sd_metrics_lib.sources.azure.story_points import AzureStoryPointExtractor`
    - `from sd_metrics_lib.sources.azure.worklog import AzureStatusChangeWorklogExtractor, AzureTaskTotalSpentTimeExtractor`

## Installation

Install core library:

```bash
pip install sd-metrics-lib
```

Optional extras for providers:

```bash
pip install sd-metrics-lib[jira]
pip install sd-metrics-lib[azure]
```

### At a glance (Quickstart)

- Most-used class: `UserVelocityCalculator`.
- Minimal flow: TaskProvider + StoryPointExtractor + WorklogExtractor -> `calculate()`.
- Time model: `Duration` + `TimeUnit` + `TimePolicy` (convert using `Duration.convert(...)`).
- Typical defaults: business-hours policy and per-day velocities.

Smallest working sketch:

```python
from sd_metrics_lib.calculators.velocity import UserVelocityCalculator
from sd_metrics_lib.sources.tasks import ProxyTaskProvider
from sd_metrics_lib.sources.story_points import ConstantStoryPointExtractor
from sd_metrics_lib.sources.worklog import FunctionWorklogExtractor
from sd_metrics_lib.utils.time import Duration, TimeUnit

# Pretend we have two tasks and attribute all work to one user
tasks = [{"id": 1}, {"id": 2}]
provider = ProxyTaskProvider(tasks)
sp = ConstantStoryPointExtractor(1)
wl = FunctionWorklogExtractor(lambda t: {"user1": Duration.of(1, TimeUnit.DAY)})

calc = UserVelocityCalculator(provider, sp, wl)
print(calc.calculate(TimeUnit.DAY))  # {"user1": ~2.0 / day}
```

### Concepts

- Task: A Jira issue or Azure DevOps work item fetched by a TaskProvider.
- Story points: Numeric size measure, extracted by a StoryPointExtractor from a field or via function.
- Worklog (derived): Time per user inferred either from native logs (Jira) or from status/assignee changes.
- Duration: A typed quantity with unit (SECOND/HOUR/DAY/WEEK/MONTH). Convert via `Duration.convert()`.
- TimeUnit/TimePolicy: Choose units and business vs civil time assumptions.

### Interface contracts (I/O)

- TaskProvider.get_tasks() -> list
- StoryPointExtractor.get_story_points(task) -> float | None
- WorklogExtractor.get_work_time_per_user(task) -> Dict[str, Duration]
- TaskTotalSpentTimeExtractor.get_total_spent_time(task) -> Duration
- Duration: `of()`, `zero()`, `convert()`, `to_seconds()`, arithmetic add/sub/sum.

## Code examples

### Calculate amount of tickets developer resolves per day based on Jira ticket status change history.

This code should work on any project and give at least some data for analysis.

```python
from atlassian import Jira

from sd_metrics_lib.calculators.velocity import UserVelocityCalculator
from sd_metrics_lib.sources.jira.story_points import JiraCustomFieldStoryPointExtractor
from sd_metrics_lib.sources.jira.tasks import JiraTaskProvider
from sd_metrics_lib.sources.jira.worklog import JiraStatusChangeWorklogExtractor
from sd_metrics_lib.utils.time import TimeUnit

JIRA_SERVER = 'server_url'
JIRA_LOGIN = 'login'
JIRA_PASS = 'password'
jira_client = Jira(JIRA_SERVER, JIRA_LOGIN, JIRA_PASS, cloud=True)

jql = " project in ('TBC') AND resolutiondate >= 2022-08-01 "
task_provider = JiraTaskProvider(jira_client, jql, additional_fields=['changelog'])

story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_10010', default_story_points_value=1)
jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['In Progress', 'In Development'])

velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
                                             story_point_extractor=story_point_extractor,
                                             worklog_extractor=jira_worklog_extractor)
velocity = velocity_calculator.calculate(velocity_time_unit=TimeUnit.DAY)

print(velocity)
```

### Calculate amount of story points developer resolves per day based on Azure DevOps work items.

This example uses Azure DevOps WIQL to fetch closed items and derives time spent per user from status/assignment changes.
It also demonstrates enabling concurrency with a thread pool and caching results with a TTL cache.

```python
# from cachetools import TTLCache  # optional, for caching examples
from concurrent.futures import ThreadPoolExecutor

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from sd_metrics_lib.calculators.velocity import UserVelocityCalculator
from sd_metrics_lib.sources.azure.story_points import AzureStoryPointExtractor
from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider
from sd_metrics_lib.sources.azure.worklog import AzureStatusChangeWorklogExtractor
from sd_metrics_lib.utils.time import TimeUnit

# Optional thread pool for faster fetching
jira_fetch_executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="azure-fetch")

ORGANIZATION_URL = 'https://dev.azure.com/your_org'
PERSONAL_ACCESS_TOKEN = 'your_pat'

credentials = BasicAuthentication('', PERSONAL_ACCESS_TOKEN)
connection = Connection(base_url=ORGANIZATION_URL, creds=credentials)
wit_client = connection.clients.get_work_item_tracking_client()

wiql = """
       SELECT [System.Id]
       FROM workitems
       WHERE
           [System.TeamProject] = 'YourProject'
         AND [System.State] IN ('Closed', 'Done', 'Resolved')
         AND [System.WorkItemType] IN ('User Story', 'Bug')
         AND [Microsoft.VSTS.Common.ClosedDate] >= '2025-08-01'
       ORDER BY [System.ChangedDate] DESC \
       """

# Use thread pool
task_provider = AzureTaskProvider(wit_client, query=wiql, thread_pool_executor=jira_fetch_executor)

story_point_extractor = AzureStoryPointExtractor(default_story_points_value=1)
worklog_extractor = AzureStatusChangeWorklogExtractor(transition_statuses=['In Progress'])

velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
                                             story_point_extractor=story_point_extractor,
                                             worklog_extractor=worklog_extractor)
velocity = velocity_calculator.calculate(velocity_time_unit=TimeUnit.DAY)

print(velocity)
```

## How velocity is computed (UserVelocityCalculator)

For each task with positive story points:

1) Extract per-user working time via WorklogExtractor.
2) Compute total task time across users; skip if zero.
3) Split the task’s story points among users proportionally to each user’s share of time.
4) Sum per-user story points and per-user time across tasks.
5) Convert total time to the requested TimeUnit/TimePolicy.
6) Return story_points / time_in_unit per user (omit zero velocities).

## Provider capability matrix (summary)

- Jira
    - JiraTaskProvider: JQL, paging, optional ThreadPoolExecutor, can fetch all fields for subtasks.
    - JiraWorklogExtractor: native worklogs; filter by users; can include subtasks.
    - JiraStatusChangeWorklogExtractor: derives work time from changelog; supports names vs accountId; status names vs codes.
    - JiraCustomFieldStoryPointExtractor: numeric custom field by name.
    - JiraTShirtStoryPointExtractor: T-shirt sizes -> numeric mapping.
    - JiraResolutionTimeTaskTotalSpentTimeExtractor: duration from created to resolutiondate.
- Azure DevOps
    - AzureTaskProvider: WIQL, stable pagination of get_work_items; custom expand fields (updates, child tasks); optional ThreadPoolExecutor.
    - AzureStatusChangeWorklogExtractor: derives time from updates; supports author/assignee resolution; user-filter; status filters.
    - AzureTaskTotalSpentTimeExtractor: creation -> closed duration.
    - AzureStoryPointExtractor: reads story points from a configurable field.

## Recipes

- Team velocity from resolution time (Jira):

```python
from atlassian import Jira

from sd_metrics_lib.calculators.velocity import GeneralizedTeamVelocityCalculator
from sd_metrics_lib.sources.jira.story_points import JiraCustomFieldStoryPointExtractor
from sd_metrics_lib.sources.jira.tasks import JiraTaskProvider
from sd_metrics_lib.sources.jira.worklog import JiraResolutionTimeTaskTotalSpentTimeExtractor
from sd_metrics_lib.utils.time import TimeUnit

# Fetch resolved tasks only; no changelog needed
jira = Jira('https://your_jira', 'login', 'password', cloud=True)
jql = "project = 'TBC' AND resolutiondate >= 2025-01-01"
provider = JiraTaskProvider(jira, jql)
sp = JiraCustomFieldStoryPointExtractor('customfield_10010', default_story_points_value=1)
spent = JiraResolutionTimeTaskTotalSpentTimeExtractor()
team = GeneralizedTeamVelocityCalculator(provider, sp, spent)
print(team.calculate(TimeUnit.DAY))
```

- Custom story points from nested attribute path:

```python
from sd_metrics_lib.sources.story_points import AttributePathStoryPointExtractor

sp = AttributePathStoryPointExtractor('my_model.points', default=1.0)
```

- Custom worklog by callable returning Durations:

```python
from sd_metrics_lib.sources.worklog import FunctionWorklogExtractor
from sd_metrics_lib.utils.time import Duration, TimeUnit


def my_worklog(task):
    return {'u1': Duration.of(3, TimeUnit.HOUR)}


wl = FunctionWorklogExtractor(my_worklog)
```

## Troubleshooting / FAQ

- I get zeros or empty results.
    - Ensure your extractor returns Duration objects (not ints). Zero totals are skipped.
    - Ensure tasks actually have story points > 0.
    - For status-change extractors, include changelog/updates in additional/custom fields.
- Time conversion seems wrong.
    - Pass TimePolicy explicitly if you need business vs civil time: `calculate(time_policy=TimePolicy.BUSINESS_HOURS)`.
    - Use `Duration.convert(TimeUnit.SECOND/DAY/...)` to check values step-by-step.
- Jira user identifiers mismatch.
    - Use JiraStatusChangeWorklogExtractor(use_user_name=True) to attribute by display name instead of accountId.
- Azure date parsing fails.
    - Extractors handle formats with/without milliseconds. If a custom format is needed, pass time_format.
- Cache misses unexpectedly.
    - CachingTaskProvider keys include query and additional_fields. Field order doesn’t matter; ensure consistent field sets.

## Extending the library

- Add a TaskProvider: implement get_tasks() that returns a list of your task objects.
- Add a StoryPointExtractor: implement get_story_points(task) -> float | None.
- Add a WorklogExtractor: implement get_work_time_per_user(task) -> Dict[str, Duration]. Return Duration objects only.
- Add a TaskTotalSpentTimeExtractor: implement get_total_spent_time(task) -> Duration.

## Supported environments

- Python: 3.9+
- Optional extras: [jira], [azure]

## Security

- Do not embed tokens in code; prefer environment variables or secret managers.

## Version history

### 7.0

+ (Breaking) JiraTaskProvider API migrated to the latest Jira API using enhanced_jql with new pagination.

### 6.3.0

+ (Feature) Add support of custom TimePolicy in SimpleWorkTimeExtractor
+ (Bug Fix) Fix wrong time assignment in Azure DevOps for status and user change in same worklog

### 6.2.1

+ (Feature) Support internal caching of get worklog requests inside AzureTaskProvider

### 6.2.0

+ (Feature) Support math and comparison operations of Duration with float/int.
+ (Feature) Add assignee history support in constructors of Azure and Jira query builders.
+ (Refactor) Replace default SimpleWorkTimeExtractor() with SIMPLE_WORKTIME_EXTRACTOR constant in worklog extractors.

### 6.1.0

+ (Breaking) Removed VelocityTimeUnit. TimeUnit should be used instead.

### 6.0

+ (Breaking) Adopt Duration/TimeUnit/TimePolicy across the public API. Calculators and worklog extractors now use Duration. Velocity calculators accept utils.time.TimeUnit (not utils.enums.VelocityTimeUnit).
+ (Feature) Add assignee history filters to Azure and Jira query builders.
+ (Bug Fix) Quote project keys/names in Jira project IN (...) filter.
+ (Refactor) Migrate internals to Duration math with TimePolicy.
+ (Docs) Refresh README examples and API overview for the new time model.

### 5.3.0

+ (Feature) Add time conversion to seconds and customizable time units.
+ (Feature) Add SECOND to VelocityTimeUnit.
+ (Feature) Add GRAY (unknown/indeterminate) to HealthStatus.

### 5.2.4

+ (Feature) Add assignee filter to Azure and Jira query builders.
+ (Bug Fix) Azure: use IN (...) for team filter; support multiple teams.

### 5.2.3

+ (Feature) Add ideal_working_hours_per_day option to utils.time.convert_time for non-standard working days.
+ (Improvement) When use_user_name=True, prefer displayName, then uniqueName, then id in AzureStatusChangeWorklogExtractor.

### 5.2.2

+ (Bug Fix) Fetch custom expand fields for child tasks in AzureTaskProvider.
+ (Bug Fix) Prefer StateChangeDate/ChangedDate for change time in AzureStatusChangeWorklogExtractor.

### 5.2.1

+ (Bug Fix) Use revised_date as change timestamp; accept datetime objects; handle times without milliseconds in AzureStatusChangeWorklogExtractor.

### 5.2

+ (Feature) Infer assignee from status-change author when last assigned is unknown in status-change worklog extractors.
+ (Bug Fix) Support resolving by user name or user id in AzureStatusChangeWorklogExtractor.
+ (Bug Fix) Use revisedDate as change timestamp (not CreatedDate) in AzureStatusChangeWorklogExtractor.
+ (Bug Fix) Handle a single entry that changes assignee and status at once in abstract status-change worklog.

### 5.1

+ (Feature) Add child tasks via custom expand field 'CustomExpand.ChildTasks' in AzureTaskProvider.
+ (Feature) Fetch all fields for subtasks when 'subtasks' is requested in JiraTaskProvider.
+ (Bug Fix) Skip filters for empty iterables in JiraSearchQueryBuilder (avoid broken JQL).
+ (Bug Fix) Use user id instead of uniqueName for proper log extraction in AzureStatusChangeWorklogExtractor.

### 5.0.2

+ (Improvement) Better type support for FunctionExtractors

### 5.0.1

+ (Bug Fix) Fix bad import in utils module

### 5.0

+ (Breaking) Restructure packages and rename files for better import Developer Experience.

+ (Feature) Add proxy-style classes for extractors
+ (Bug Fix) Fix task id adding in query builders
+ (Bug Fix) Fix custom expand field in AzureTaskProvider

### 4.0

+ (Breaking) Fix circular module import issue

+ (Feature) Add filtering by task ids in Azure and Jira query builders

### 3.0

+ (Breaking) Rename all Issue* terms to Task* across API (IssueProvider -> TaskProvider, IssueTotalSpentTimeExtractor -> TaskTotalSpentTimeExtractor, etc.). Removed backward-compatibility aliases.
+ (Breaking) Change package and method names in JiraSearchQueryBuilder

+ (Feature) Introduce AzureSearchQueryBuilder
+ (Feature) Make changelog history optional via additional fields in AzureTaskProvider
+ (Feature) Extend JiraSearchQueryBuilder with custom raw filters; filter by Team; open-ended resolution date
+ (Feature) Rewrite CachingTaskProvider to support Django caches
+ (Feature) Introduce AzureSearchQueryBuilder
+ (Bug Fix) Azure: fetch all tasks beyond 20k limit using stable pagination
+ (Bug Fix) Jira: do not fail on empty search results

### 2.0

+ (Feature) Add integration with Azure DevOps
+ (Breaking) Add a generic CachingIssueProvider to wrap any IssueProvider and remove CachingJiraIssueProvider

### 1.2.1

+ **(Improvement)** Add possibility to adjust init time
+ **(Bug Fix)** Fix bug with wrong cache data fetching
+ **(Bug Fix)** Fix bug in week time period end date resolving

### 1.2

+ **(Feature)** Added BoundarySimpleWorkTimeExtractor
+ **(Improvement)** Filter unneeded changelog items for better performance
+ **(Improvement)** Add T-Shirt to story points mapping util class
+ **(Improvement)** Add helper enums
+ **(Bug Fix)** Fix bug with story points returned instead of spent time
+ **(Bug Fix)** Fix bug with missing time for active status
+ **(Bug Fix)** Fix bug with passing class instances in extractor

### 1.1.4

+ **(Improvement)** Add multithreading support for JiraIssueProvider.

### 1.1.3

+ **(Feature)** Add CachingJiraIssueProvider.

### 1.1.2

+ **(Improvement)** Add story points getter for GeneralizedTeamVelocityCalculator.

### 1.1.1

+ **(Improvement)** Execute data fetching in Jira velocity calculators only once.
+ **(Improvement)** Add story points getter for Jira velocity calculators.

### 1.1

+ **(Feature)** Add team velocity calculator.
+ **(Improvement)** Add JQL filter for last modified data.
+ **(Bug Fix)** Fix wrong user resolving in JiraStatusChangeWorklogExtractor.
+ **(Bug Fix)** Fix resolving more time than spent period of time.
+ **(Bug Fix)** Fix Jira filter query joins without AND.

### 1.0.3

+ **(Improvement)** Add JiraIssueSearchQueryBuilder util class.
+ **(Improvement)** Add TimeRangeGenerator util class.
+ **(Bug Fix)** Fix filtering by status when no status list passed.

### 1.0.2

+ **(Bug Fix)** Fix package import exception after installing from pypi.

### 1.0

+ **(Feature)** Add user velocity calculator.