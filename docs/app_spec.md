# Phase 1 Web App Build Spec

## Overview

Build a database-backed web app that helps **[intended user]** complete
**[primary task]**. In the first release, a user should be able to
**[complete the workflow from start to finish]**.

## Functional Scope

- Primary workflow — [Describe what the user does and what the app shows or saves.]
- Data — [List what the app stores and which records users can view or change.]
- Out of scope — User accounts, sign-in, and permissions are deferred to a later phase.

## Technical Requirements

- Use Supabase-hosted PostgreSQL for persistent storage.
- Deploy the web app to Render and provide a URL for testing.
- Keep database credentials on the server and configure them through environment variables.

## Design and Licensing

- Design for mobile first. Verify that the same workflow is usable on desktop.
- Use a restrained palette, primarily light and dark grays. Maintain readable
  contrast and use text or icons alongside color to communicate status.
- Use system fonts or fonts licensed for free web use.
- Use software and assets that require no paid licenses. Include any required
  attribution and license notices.

## Phase 1 Acceptance Criteria

- A tester can open the Render URL and complete the primary workflow without signing in.
- The workflow saves the expected data to PostgreSQL, and the app can retrieve it
  in a new session.
- The workflow is usable at mobile and desktop widths.
- Required attribution and license notices are included.

## Implementation Plan

Before coding, outline the screens, the data model, the build sequence, and how
each acceptance criterion will be verified. Flag unresolved scope questions,
hosting costs or limits, and any unclear license or attribution requirements.