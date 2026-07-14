# .github

Shared community defaults and reusable GitHub Actions workflows for
[@CMDRPhaedra](https://github.com/CMDRPhaedra) repos.

## badges.yml

A reusable workflow that keeps a standard shields.io badge block in a
repo's `README.md` up to date (license, last commit, repo size, top
language, open issues).

To use it in another repo:

1. Add these markers wherever you want the badges in that repo's `README.md`:

   ```markdown
   <!-- BADGES:START -->
   <!-- BADGES:END -->
   ```

2. Add a caller workflow, e.g. `.github/workflows/update-badges.yml`:

   ```yaml
   name: Update README badges

   on:
     push:
       branches: [main]
     workflow_dispatch: {}

   jobs:
     badges:
       uses: CMDRPhaedra/.github/.github/workflows/badges.yml@main
       permissions:
         contents: write
   ```

The workflow only touches the content between the markers, so anything
else in the README is left alone.
