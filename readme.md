# CST8917 Final Project Approval Pipeline Assignment

Name: Corey Mark-Stewart
Student Number: 040 770 982  
Course Code: CST8917  
Project Title: Assignment 2 - Expense Approval Pipeline  
Date: 2026-08-14

## Version A Summary
 I chose Azure Durable Functions because the expense approval process is a stateful workflow with a natural human-in-the-loop step. The orchestrator keeps the workflow logic in one place and controls the full lifecycle of the request, while activity functions handle validation, result building, and notification so the orchestrator stays deterministic. For manager approval, I used the Human Interaction pattern with an external event and a durable timer running in parallel, which lets the workflow wait for a manager response without blocking compute. If the manager responds in time, the request is approved or rejected; if not, the timer wins and the expense is auto-approved and marked as escalated. This design was chosen because it is reliable, easy to trace by instance ID, and maps directly to the assignment requirements.

## Version B Summary
The system uses Azure Logic Apps to orchestrate the expense approval workflow, Service Bus for asynchronous messaging, and an Azure Function to validate expense requests. Requests under $100 are automatically approved, while requests of $100 or more are sent to a manager through a Service Bus decision queue. Logic Apps waits for the manager’s response and automatically approves and flags the expense as escalated if the timeout is reached. The final outcome is published to a Service Bus topic with filtered subscriptions for approved, rejected, and escalated results, which trigger an email notification to the employee.

## Comparison Analysis

Version A and Version B both implement the same expense approval workflow, but they approach the problem differently. Version A is based primarily on Azure Functions and orchestration, while Version B uses Azure Logic Apps and Service Bus. Both solutions can successfully validate expenses, automatically approve smaller expenses, handle manager approval, manage timeouts, and notify employees. However, there are differences in complexity, cost, deployment, integration, and ease of development.

One of the biggest advantages of Version A is its simplicity. Since the workflow can be handled primarily through Azure Functions and orchestration, there are fewer Azure services that need to be configured and connected. I also found Version A easier to develop because I already had experience working with Azure Functions. This made it easier to understand how the different parts of the workflow worked together and how to troubleshoot problems. The deployment process was also more familiar because the Functions-based approach follows a development model similar to other applications I have worked with.

Version B requires more knowledge of the Azure services involved. Logic Apps provides a visual workflow, which can make the overall architecture easier to understand, but actually building the workflow can require more understanding of Logic Apps expressions, conditions, triggers, and actions. For example, checking the result returned by the validation Azure Function requires using Logic Apps expressions correctly. This adds another layer of knowledge compared with Version A, where much of the logic can be written directly in code. During development, I found that Version B required more step-by-step guidance to understand how the different Logic Apps actions and expressions should be configured.

Another difference is the amount of assistance required during development. Version A was relatively straightforward to implement because I was already familiar with Azure Functions and could use AI assistance to generate or explain parts of the implementation. Version B required more detailed guidance because there were more Azure-specific configuration steps involved. Service Bus queues, topics, subscriptions, filters, Logic Apps actions, and expressions all needed to be configured correctly. This does not necessarily make Version B worse, but it does give it a steeper learning curve for someone who is not already familiar with Logic Apps and Service Bus.

Cost is another important consideration. Version B uses multiple Azure services, including Logic Apps, Service Bus, and Azure Functions. Using two or more managed services can increase the overall cost compared with a simpler Functions-based implementation. Depending on the workload and pricing tier, the difference may be small for a school project or low-volume application, but it becomes more important as the system grows. Version A can therefore be more attractive when keeping the architecture and infrastructure costs as low as possible is a priority.

On the other hand, Version B has a major advantage when it comes to connecting different services together. Logic Apps provides many built-in connectors and triggers, making it relatively easy to integrate Azure services and external services without writing as much custom code. Service Bus also provides a reliable messaging layer between components. This makes Version B more flexible for an organization that expects the workflow to eventually integrate with additional systems. Instead of writing custom integration code for every service, Logic Apps can often connect directly to the required service.

Email notifications are another area where Version B has an advantage. Logic Apps provides connectors and actions specifically designed for sending emails and interacting with other services. This makes it easier to build different notification paths for approved, rejected, and escalated expenses. The Service Bus topic and filtered subscriptions also provide a clean way to separate these outcomes. For example, an approved message can go to the approved subscription while a rejected message goes to the rejected subscription. This makes the notification architecture easier to expand if additional types of notifications are required.

The manager approval requirement also shows an important difference between the two approaches. Version A's orchestration model is better suited to managing a long-running workflow because the orchestration can maintain the state of the approval process and wait for an external event. Version B does not provide the same human-interaction pattern as Durable Functions, so a reasonable workaround is required. In Version B, I used Service Bus to send the manager approval request and receive the manager's decision, while Logic Apps uses a polling and timeout approach. If implemented correctly, this can handle the approval process fairly well, but it requires more configuration and careful handling of the expense ID and timeout.

Overall, Version A is the better choice for simplicity, familiarity, and potentially lower cost, especially for a developer who already has experience with Azure Functions. It is easier to develop and deploy because there are fewer moving parts and more of the business logic can be handled directly in code. Version B is more complex, but it provides stronger integration capabilities and better built-in options for connecting services and sending notifications. The Service Bus messaging model also makes Version B more flexible for larger event-driven workflows.

In conclusion, neither version is universally better. Version A is better when simplicity and ease of development are the main priorities, while Version B is better when integration, messaging, and extensibility are more important. For this project, I found Version A easier to implement because of my previous experience with Azure Functions. However, Version B demonstrated how Logic Apps and Service Bus can make it easier to connect multiple services together and build a more event-driven architecture. If the system were expanded into a larger enterprise workflow with many external integrations and notification requirements, Version B would likely become more valuable despite its additional complexity and cost

## Recommendation

I would recommend Version A for the expense approval system because it provides the best balance between simplicity, cost, and control. Version A is easier to develop and deploy because most of the workflow can be handled through Azure Functions and orchestration. Since I already have experience working with Azure Functions, I found it easier to understand the workflow and troubleshoot problems when something did not work as expected.

Another reason I would choose Version A is that it requires fewer Azure services compared with Version B. Version B uses Logic Apps, Service Bus queues, a Service Bus topic with multiple subscriptions, and Azure Functions. While this provides strong integration capabilities, it also introduces additional configuration and potential costs. For a relatively simple expense approval workflow, the additional services may not provide enough benefit to justify the extra complexity.

Version A also makes the business logic easier to control because the validation, approval conditions, timeout handling, and other workflow logic can be implemented directly in code. This makes the application easier to customize as requirements change. Version B's visual workflow is useful for connecting services, but it requires more knowledge of Logic Apps expressions, triggers, conditions, and Service Bus configuration.

Although Version B has advantages, particularly for service integration and email notifications, I believe Version A is the better choice for this particular application. It is simpler, more familiar, easier to maintain, and potentially less expensive. For a larger enterprise system with many integrations, I would reconsider Version B, but for this expense approval workflow, Version A is the more practical solution.

## References

- [Azure Durable Functions overview](https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-overview)
- [Azure Functions Python developer guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [Durable Functions Python v2 programming model](https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-python-model-v2)

## AI Disclosure

I was running out time and use AI throughout this assignment.

