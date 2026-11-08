# DELEGATION.md

## Delegation Boundary

### Decision Rule
> The agent may act independently only when an action is low-risk, reversible, and read-only, and does not significantly impact other people, privacy or finances; any access to sensitive data or any write operation that adds, modifies, or deletes information requires prior user approval.
---

## Action Decisions

| Action | Decision (alone / approval) | Justification |
|----------|----------|----------|
| Read the appointments of a day | alone | Reading calendar data has low risk and no lasting consequences. |
| Look up the weather | alone | Reading weather data is also a low-risk action with no expected consequences. Requiring approval for every such trivial request would be annoying and inconvenient for the user. |
| Search train connections | alone | A read-only and summarization task that does not involve sensitive data. |
| Read notes | approval | Although this is a read-only action, the sensitivity of note contents can vary significantly. Requesting approval helps ensure the user is aware of which information is being accessed. |
| Create a personal block in the calendar (e.g. travel time, no other attendees) | alone | No other participants are affected by this action. |
| Reschedule an appointment with other attendees | approval | This is a write action and directly affects other participants. |
| Book a train ticket | approval | Actions involving payments should always require approval for security reasons. |
| Send a message to third parties | approval | Other people are affected, so approval should be obtained before sending to prevent messages from being sent to the wrong recipient or with inappropriate, unprofessional, or incorrect content. |
| Create a note | approval | This is a write action. |
| Delete a note | approval | This is a write action that may be irreversible. |


---

## Observations from the Role Play

### Observation 1
There are some debatable cases, particularly regarding access to and reading of notes.

If the notes do not contain sensitive information, such as reminders about business appointments, this action could also be classified as alone.

In general, the classification of these cases depends on the level of trust in the agent as well as the user's routine and familiarity with it. At the same time, too many requests for approval in trivial situations should be avoided, as they can become disruptive and reduce usability.

For example, if I regularly use the agent to manage the content of my notes, it is reasonable to allow read access without requiring approval each time. On the other hand, if notes are primarily personal and may contain private or personally identifiable information, requesting approval before access is entirely justified.

### Observation 2
Sometimes the decision also depends on how the request is phrased.

When I ask the agent, “What’s on today?”, it is clear that I expect it to access my calendar and read the relevant information. In contrast, a request such as “Get me to the workshop visit in Munich on time.” implicitly combines several actions. Without feedback, it is not transparent to the user which information sources the agent will access or which actions it will perform.

For example, if the agent responds to this prompt by searching for a train connection and automatically creating a calendar block for the travel time, that would already go too far in my view. In such a case, I would like to be informed beforehand that a calendar block is going to be created. On the other hand, if I explicitly say “Create a calendar block for this time”, then no additional approval should be required because the intent is clear and unambiguous.

As a general principle, write operations, modifications of existing data, and bookings should always require confirmation. This ensures that the user remains in control and has an opportunity to review actions that may have lasting consequences.


