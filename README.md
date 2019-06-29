# djdep

A simple utility for showing cross-app dependencies in Django (or other Python)
projects.

Example output for a project with several apps, including `api`, `crawlers`,
`repository`:

    {
      "api": [
        "repository.models.Mp",
        "repository.models.Party"
      ],
      "crawlers": [
        "notifications.models.TaskNotification",
        "repository.models.Constituency",
        "repository.models.Mp",
        "repository.models.Party"
      ],
      "repository": [
        "api.contract"
      ]
    }

At a glance you can see that the `api` app uses the `Mp` and `Party` models
from the `repository` app.

Many imports are removed before rendering the result because they do not affect
how your apps interact with each other:
- External, 3rd party imports - an app might import `os` but your other app
doesn't care about that

- App-internal imports. For example, the `api` app has several files that import
`api.contract` but that is hidden because it does not affect how apps interact
with one another. These internal imports may be shown with the `-i` flag.

Additionally, you may remove test files/modules from the results with the `-t`
flag.

By default, imports are shown at the per-app level. If you want more detail use
the `--maxdepth [int]` argument which will give you dependencies on the
submodule- or file-level.
