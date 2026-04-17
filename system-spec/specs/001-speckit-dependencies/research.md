# Research: Add Spec Kit Dependencies

## Decision: Unification of Dependencies in `requirements.txt`
**Decision**: We will explicitly add `specify-cli` to `requirements.txt` to ensure both local developers and the Docker container install the dependency.
**Rationale**: By explicitly avoiding `requirements-dev.txt`, the installation process is kept uniform. The virtual environment setup (`pip install -r requirements.txt`) and Docker build will both pick up `specify-cli`.
**Alternatives considered**: Installing it globally via `pipx` or `uv`. Rejected because the specification explicitly demanded it be listed with the existing primary python dependencies.

## Decision: Docker System Dependencies
**Decision**: We will add `git` to the `apt-get install` list in the `Dockerfile`.
**Rationale**: Spec Kit (`specify-cli`) extensively relies on Git repository state (branches, hooks) for its workflow lifecycle. The Docker container currently installs `build-essential` and `curl`, but not `git`. For developers using Spec Kit workflows *inside* the container, `git` is functionally required.
**Alternatives considered**: Mocking the git status. Rejected because Spec Kit actively executes git commands (`speckit-git-feature`, `speckit-git-commit`).
