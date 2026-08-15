# CST8917 Final Project Approval Pipeline Assignment

Name: Corey Mark-Stewart
Student Number: 040 770 982  
Course Code: CST8917  
Project Title: Assignment 2 - Expense Approval Pipeline  
Date: 2026-08-14

## Version A Summary

- Brief description of the Durable Functions implementation.
- Design decisions: I chose Azure Durable Functions because the expense approval process is a stateful workflow with a natural human-in-the-loop step. The orchestrator keeps the workflow logic in one place and controls the full lifecycle of the request, while activity functions handle validation, result building, and notification so the orchestrator stays deterministic. For manager approval, I used the Human Interaction pattern with an external event and a durable timer running in parallel, which lets the workflow wait for a manager response without blocking compute. If the manager responds in time, the request is approved or rejected; if not, the timer wins and the expense is auto-approved and marked as escalated. This design was chosen because it is reliable, easy to trace by instance ID, and maps directly to the assignment requirements.
- Challenges encountered:
	- [Add challenge 1]
	- [Add challenge 2]

## Version B Summary

- Brief description of the alternative architecture.
- Approach chosen for manager approval:
	- [Describe how manager approval is handled]
- Challenges encountered:
	- [Add challenge 1]
	- [Add challenge 2]

## Comparison Analysis

[Write 800-1200 words comparing Version A and Version B.]

Suggested points to cover:
- Reliability
- Complexity
- Maintainability
- Scalability
- Cost
- Developer experience
- Testing and debugging

## Recommendation

[Write 200-300 words recommending one version and explaining why.]

## References

- [Azure Durable Functions overview](https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-overview)
- [Azure Functions Python developer guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [Durable Functions Python v2 programming model](https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-python-model-v2)
- [Add any assignment-specific sources here]

## AI Disclosure

- [State how AI was used in this assignment, or write that no AI was used.]

