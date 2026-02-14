# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and uses [Conventional Commits](https://www.conventionalcommits.org/).

## 1.1.5 (2026-02-14)

### Bug Fixes

- test changelog generation

## 1.1.4 (2026-02-14)

### Bug Fixes

- update changelog config to non-deprecated format

## 1.1.3 (2026-02-14)

### Bug Fixes

- use only 'published' event to prevent duplicate CD runs
- remove non-existent templates dir from semantic-release config

## 1.1.2 (2026-02-14)

### Bug Fixes

- use PAT to enable CD workflow triggering
- configure commit author in semantic-release config

## 1.1.1 (2026-02-14)

### Bug Fixes

- set git author env vars for verified semantic-release commits
- add 'released' event type to CD workflow trigger
- configure semantic-release remote for GitHub releases

## 1.1.0 (2026-02-14)

### Features

- add version and changelog display in bot info screen

### Bug Fixes

- use verified email for github-actions bot commits

## 1.0.1 (2026-02-14)

### Bug Fixes

- checkout main branch instead of SHA for semantic-release

## 1.0.0 (2026-02-14)

### Features

- add automated semantic versioning and release workflow
- add home page with navigation and bot info
- add end session button and environment-aware config
- add GitHub Actions CI/CD and make check-ci

### Bug Fixes

- use context.args for start payload, generate secret per run

### Refactoring

- modularize bot code into separate files
- add auth decorator and improve session management

