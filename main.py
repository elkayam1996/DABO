from context import Context
from modelConnection import LocalModelFactory, CloudModelFactory
from primitiveTools import ToolRegistry
from plan import Plan
from compiler.astValidator import ASTValidator
from compiler.graphCompiler import GraphCompiler
import consts


def print_header(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def read_multiline_request() -> str:
    print_header("USER REQUEST")
    print("Write your request.")
    print("When done, type END_REQUEST on a new line.\n")

    lines = []

    while True:
        line = input()

        if line.strip() == "END_REQUEST":
            break

        lines.append(line)

    return "\n".join(lines).strip()


def ask_plan_feedback() -> str | None:
    print("\nPlan options:")
    print("- Press Enter to accept the plan")
    print("- Type feedback to improve the plan")
    print("- Type QUIT to exit")

    feedback = input("\nYour choice: ").strip()

    if feedback == "":
        return None

    if feedback.upper() == "QUIT":
        raise SystemExit(0)

    return feedback


def create_human_plan(
    cloud_llm,
    private_llm,
    local_tools_description: str,
    frontier_tools_description: str,
) -> str:
    plan_context = Context()
    pln = Plan()

    user_request = read_multiline_request()

    if user_request == "":
        print("Request is empty.")
        raise SystemExit(1)

    local_model_profile = (
        f"Local model selected by user: "
        f"{getattr(private_llm, 'model_name', 'unknown')}"
    )

    first_prompt = pln.prompt(
        user_p=user_request,
        local_model_tools=local_tools_description,
        frontier_tools=frontier_tools_description,
        local_model_profile=local_model_profile,
    )

    plan_context.append("user", first_prompt)

    while True:
        print_header("CREATING PLAN")

        cloud_plan = cloud_llm.chat(
            plan_context.getContextList(),
            reasoning=cloud_llm.REASONING.NONE,
        )

        pln.set_plan(cloud_plan)
        plan_context.append("assistant", cloud_plan)

        print_header("CURRENT PLAN")
        print(cloud_plan)

        feedback = ask_plan_feedback()

        if feedback is None:
            return pln.get_plan()

        plan_context.append("user", feedback)


def create_valid_ast(
    cloud_llm,
    human_plan: str,
    local_tools_description: str,
    frontier_tools_description: str,
    max_attempts: int = 3,
) -> dict:
    validator = ASTValidator(local_tools_description)

    previous_ast = "None"
    validation_errors = "None"

    for attempt in range(1, max_attempts + 1):
        print_header(f"CREATING AST ATTEMPT {attempt}/{max_attempts}")

        ast_prompt = (
            consts.AST_COMPILER_PROMPT
            .replace("__HUMAN_PLAN__", human_plan)
            .replace("__LOCAL_TOOLS__", local_tools_description)
            .replace("__FRONTIER_TOOLS__", frontier_tools_description)
            .replace("__PREVIOUS_AST__", previous_ast)
            .replace("__VALIDATION_ERRORS__", validation_errors)
        )

        ast_context = Context()
        ast_context.append("user", ast_prompt)

        raw_ast = cloud_llm.chat(
            ast_context.getContextList(),
            reasoning=cloud_llm.REASONING.NONE,
        )

        validation_result = validator.validate(raw_ast)

        if validation_result["ok"]:
            print("AST is valid.")
            return validation_result["ast_dict"]

        print("AST is invalid.")
        print(validation_result["feedback"])

        previous_ast = raw_ast
        validation_errors = validation_result["feedback"]

    print("Could not create valid AST.")
    raise SystemExit(1)


def compile_graph(valid_ast_dict: dict) -> dict:
    print_header("COMPILING GRAPH")

    graph_compiler = GraphCompiler()
    graph = graph_compiler.compile(valid_ast_dict)

    print("Graph compiled successfully.")
    print("Root nodes:", graph["root_nodes"])
    print("All nodes:", list(graph["node_by_id"].keys()))

    return graph


if __name__ == "__main__":
    print_header("DABO")

    cloud_model_picker = input("Pick cloud model provider: ").strip()
    cloud_llm = CloudModelFactory(cloud_model_picker)

    private_model_picker = input("Pick private model provider: ").strip()
    private_llm = LocalModelFactory(private_model_picker)

    tool_registry = ToolRegistry()
    local_tools_description = tool_registry.get_available_tools()
    frontier_tools_description = "None"

    human_plan = create_human_plan(
        cloud_llm=cloud_llm,
        private_llm=private_llm,
        local_tools_description=local_tools_description,
        frontier_tools_description=frontier_tools_description,
    )

    valid_ast_dict = create_valid_ast(
        cloud_llm=cloud_llm,
        human_plan=human_plan,
        local_tools_description=local_tools_description,
        frontier_tools_description=frontier_tools_description,
    )

    graph = compile_graph(valid_ast_dict)

    print_header("DONE")
    print("Planner, AST validation, and graph compilation completed.")