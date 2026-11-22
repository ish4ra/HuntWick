# Working on HuntWick

Follow docs/development.md for the project toolchain and checks. Use the existing checkout in isolated cloud tasks. Keep changes scoped to the requested feature.

Use deterministic fixtures for tests. Search history is opt-in. Never log usernames or public profile links, add tracking, bypass website access controls, or disable certificate verification. Preserve upstream attribution. Use explicit result states when site responses are ambiguous.

Keep frontend, native and sidecar message shapes synchronized. Validate inputs on both sides of each trust boundary. Keep release artifacts out of Git and reserve publication for the manual release workflow.
