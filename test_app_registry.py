from core.app_registry import criar_registry


registry = criar_registry()


print()

print("="*60)

print("PRINTER ASSISTANT REGISTRY")

print("="*60)


print()


print("TOOLS")

print("-"*60)


for tool in registry.tools.values():

    print(

        tool.name,

        "-",

        tool.description

    )


print()


print("REPORTS")

print("-"*60)


for report in registry.reports.values():

    print(

        report.title

    )


print()


print("WORKFLOWS")

print("-"*60)


for workflow in registry.workflows.values():

    print(

        workflow.name

    )