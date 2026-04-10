"""GitHub REST API client for creating branches, commits, and PRs."""

import base64
import time

import httpx

from .config import Settings

API = "https://api.github.com"


class GitHubClient:
    def __init__(self, settings: Settings):
        self.repo = settings.github_repo
        self.headers = {
            "Authorization": f"Bearer {settings.github_pat}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def close(self):
        await self._client.aclose()

    # -- Helpers --

    async def _get(self, path: str) -> httpx.Response:
        return await self._client.get(f"{API}{path}")

    async def _post(self, path: str, json: dict) -> httpx.Response:
        return await self._client.post(f"{API}{path}", json=json)

    # -- Pack existence --

    async def check_pack_exists(self, pack_name: str) -> bool:
        """Check if pax/<pack_name>/ already exists on main."""
        resp = await self._get(f"/repos/{self.repo}/contents/pax/{pack_name}/pax.yaml")
        return resp.status_code == 200

    # -- Git Trees API for atomic multi-file commits --

    async def get_main_sha(self) -> str:
        """Get the SHA of the main branch HEAD."""
        resp = await self._get(f"/repos/{self.repo}/git/ref/heads/main")
        resp.raise_for_status()
        return resp.json()["object"]["sha"]

    async def create_branch(self, branch_name: str, base_sha: str) -> None:
        """Create a new branch from a base SHA."""
        resp = await self._post(
            f"/repos/{self.repo}/git/refs",
            json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
        )
        resp.raise_for_status()

    async def create_tree(self, base_tree_sha: str, files: dict[str, bytes]) -> str:
        """Create a git tree with the given files. Returns tree SHA.

        files: mapping of path (e.g. "pax/my-pack/pax.yaml") -> file content bytes
        """
        tree_items = []
        for path, content in files.items():
            tree_items.append({
                "path": path,
                "mode": "100644",
                "type": "blob",
                "content": content.decode("utf-8"),
            })

        resp = await self._post(
            f"/repos/{self.repo}/git/trees",
            json={"base_tree": base_tree_sha, "tree": tree_items},
        )
        resp.raise_for_status()
        return resp.json()["sha"]

    async def create_commit(self, tree_sha: str, parent_sha: str, message: str) -> str:
        """Create a commit. Returns commit SHA."""
        resp = await self._post(
            f"/repos/{self.repo}/git/commits",
            json={
                "message": message,
                "tree": tree_sha,
                "parents": [parent_sha],
            },
        )
        resp.raise_for_status()
        return resp.json()["sha"]

    async def update_branch(self, branch_name: str, commit_sha: str) -> None:
        """Update a branch ref to point to a new commit."""
        resp = await self._client.patch(
            f"{API}/repos/{self.repo}/git/refs/heads/{branch_name}",
            json={"sha": commit_sha},
        )
        resp.raise_for_status()

    async def commit_pack_files(
        self, branch_name: str, pack_name: str, files: dict[str, bytes]
    ) -> str:
        """Atomic multi-file commit via Git Trees API.

        files: mapping of relative path within pack dir -> content bytes
               e.g. {"pax.yaml": b"...", "knowledge/constructs.json": b"..."}

        Returns the commit SHA.
        """
        main_sha = await self.get_main_sha()

        # Get the base tree SHA from main
        resp = await self._get(f"/repos/{self.repo}/git/commits/{main_sha}")
        resp.raise_for_status()
        base_tree_sha = resp.json()["tree"]["sha"]

        # Prefix all paths with pax/<pack_name>/
        prefixed = {f"pax/{pack_name}/{path}": content for path, content in files.items()}

        tree_sha = await self.create_tree(base_tree_sha, prefixed)
        commit_sha = await self.create_commit(
            tree_sha, main_sha, f"[Community] Add {pack_name}"
        )

        # Create branch pointing to this commit
        await self.create_branch(branch_name, commit_sha)

        return commit_sha

    # -- Pull Requests --

    async def create_pull_request(
        self,
        branch_name: str,
        pack_name: str,
        username: str,
        is_update: bool,
    ) -> dict:
        """Open a PR and add the 'community' label. Returns PR data."""
        action = "Update" if is_update else "Add"
        title = f"[Community] {action} {pack_name}"
        body = (
            f"## Community Pack Submission\n\n"
            f"**Pack:** `{pack_name}`\n"
            f"**Submitted by:** @{username}\n"
            f"**Type:** {'Update to existing pack' if is_update else 'New pack'}\n\n"
            f"---\n"
            f"*Submitted via [PAX Upload Service](https://submit.pax-market.com)*"
        )

        resp = await self._post(
            f"/repos/{self.repo}/pulls",
            json={
                "title": title,
                "body": body,
                "head": branch_name,
                "base": "main",
            },
        )
        resp.raise_for_status()
        pr_data = resp.json()

        # Add community label
        await self._ensure_label_exists()
        await self._post(
            f"/repos/{self.repo}/issues/{pr_data['number']}/labels",
            json={"labels": ["community"]},
        )

        return pr_data

    async def _ensure_label_exists(self) -> None:
        """Create 'community' label if it doesn't exist."""
        resp = await self._get(f"/repos/{self.repo}/labels/community")
        if resp.status_code == 404:
            await self._post(
                f"/repos/{self.repo}/labels",
                json={
                    "name": "community",
                    "color": "7057ff",
                    "description": "Community-submitted pack",
                },
            )

    # -- User's submissions --

    async def get_user_submissions(self, username: str) -> list[dict]:
        """Get PRs submitted by a user via the upload service."""
        resp = await self._get(
            f"/repos/{self.repo}/pulls?state=all&sort=created&direction=desc&per_page=20"
        )
        resp.raise_for_status()

        submissions = []
        for pr in resp.json():
            # Filter to community PRs mentioning this user
            body = pr.get("body") or ""
            if f"@{username}" not in body or "[Community]" not in pr.get("title", ""):
                continue

            # Determine CI status
            ci_status = await self._get_pr_ci_status(pr["number"])

            submissions.append({
                "pr_number": pr["number"],
                "title": pr["title"],
                "state": "merged" if pr.get("merged_at") else pr["state"],
                "ci_status": ci_status,
                "created_at": pr["created_at"],
                "url": pr["html_url"],
            })

        return submissions

    async def _get_pr_ci_status(self, pr_number: int) -> str | None:
        """Get combined CI status for a PR."""
        # Get the PR's head SHA
        resp = await self._get(f"/repos/{self.repo}/pulls/{pr_number}")
        if resp.status_code != 200:
            return None
        head_sha = resp.json()["head"]["sha"]

        # Get combined status
        resp = await self._get(f"/repos/{self.repo}/commits/{head_sha}/status")
        if resp.status_code != 200:
            return None
        return resp.json().get("state")  # pending, success, failure, error
